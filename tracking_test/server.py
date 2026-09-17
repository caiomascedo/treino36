import functools
import hashlib
from contextlib import contextmanager
import hmac
import json
import os
from pathlib import Path
import re
import secrets
import sqlite3
import subprocess
import time
import urllib.parse
from datetime import datetime
from zoneinfo import ZoneInfo

from flask import Flask, Response, abort, jsonify, redirect, render_template_string, request, send_file
from werkzeug.serving import make_server

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data'
TZ = ZoneInfo('America/Fortaleza')
NOTICE = ('O evento indica interação do aluno (abertura do PDF, clique no botão "Iniciar Treino" ou clique no link do YouTube do exercício). '
          'Acessos repetidos à mesma ação em menos de 60 segundos são deduplicados.')
FIXTURE = dict(nome='Aluno Teste - Caio', student_id='tracking-test-caio',
               treino_id='tracking-test-workout', treinoNome='Treino de teste A',
               treino={'A': ['Agachamento Livre 3x 12', 'Prancha 3x 30s']},
               titulos={'A': 'A. TREINO DE TESTE'}, secaoFAtiva=False)


@contextmanager
def connect(path):
    db = sqlite3.connect(path, timeout=15)
    db.row_factory = sqlite3.Row
    try:
        with db:
            yield db
    finally:
        db.close()


def initialize(path):
    with connect(path) as db:
        db.executescript('''
        PRAGMA journal_mode=WAL;
        CREATE TABLE IF NOT EXISTS pdf_links (
          token TEXT PRIMARY KEY, student_id TEXT NOT NULL, student_name TEXT NOT NULL,
          workout_id TEXT NOT NULL, workout_name TEXT NOT NULL, pdf BLOB NOT NULL,
          last_seen REAL, active INTEGER NOT NULL DEFAULT 1);
        CREATE TABLE IF NOT EXISTS pdf_events (
          id INTEGER PRIMARY KEY, student_id TEXT NOT NULL, student_name TEXT NOT NULL,
          workout_id TEXT NOT NULL, workout_name TEXT NOT NULL, token TEXT NOT NULL,
          event_type TEXT NOT NULL, opened_at TEXT NOT NULL, ip TEXT, user_agent TEXT);
        CREATE INDEX IF NOT EXISTS events_token ON pdf_events(token);
        ''')
        for table in ('pdf_links', 'pdf_events'):
            if 'whatsapp' not in {r['name'] for r in db.execute('PRAGMA table_info(' + table + ')')}:
                db.execute('ALTER TABLE ' + table + " ADD COLUMN whatsapp TEXT NOT NULL DEFAULT ''")
        db.executescript('''
        CREATE TABLE IF NOT EXISTS students (
          student_name TEXT PRIMARY KEY, whatsapp TEXT NOT NULL DEFAULT '',
          workout_name TEXT NOT NULL DEFAULT '', total_accesses INTEGER NOT NULL DEFAULT 0,
          latest TEXT);
        CREATE INDEX IF NOT EXISTS events_student_action ON pdf_events(student_name,event_type,id);
        INSERT OR IGNORE INTO students(student_name,whatsapp,workout_name,total_accesses,latest)
          SELECT student_name, '', workout_name, COUNT(*), MAX(opened_at)
          FROM pdf_events GROUP BY student_name;
        ''')


def normalize_whatsapp(value):
    digits = re.sub(r'\D', '', str(value or ''))
    if len(digits) in (10, 11):
        digits = '55' + digits
    return digits if 10 <= len(digits) <= 15 else ''


def sync_student(db, name, whatsapp, workout, latest=None, increment=0):
    db.execute('''INSERT INTO students(student_name,whatsapp,workout_name,total_accesses,latest)
      VALUES(?,?,?,?,?) ON CONFLICT(student_name) DO UPDATE SET
      whatsapp=CASE WHEN excluded.whatsapp!='' THEN excluded.whatsapp ELSE students.whatsapp END,
      workout_name=excluded.workout_name, total_accesses=students.total_accesses+excluded.total_accesses,
      latest=COALESCE(excluded.latest,students.latest)''',
      (name, normalize_whatsapp(whatsapp), workout, increment, latest))


def register_pdf(path, pdf, student=None):
    if not pdf.startswith(b'%PDF-') or len(pdf) > 20 * 1024 * 1024:
        raise ValueError('PDF inválido ou maior que 20 MB')
    if student is None:
        student = FIXTURE
    token = secrets.token_urlsafe(32)
    student_id = student.get('student_id') or secrets.token_hex(6)
    student_name = student.get('nome') or student.get('student_name') or 'Aluno'
    workout_id = student.get('treino_id') or student.get('workout_id') or 'workout'
    workout_name = student.get('treinoNome') or student.get('workout_name') or 'Treino'
    with connect(path) as db:
        db.execute('INSERT INTO pdf_links(token,student_id,student_name,workout_id,workout_name,pdf,whatsapp) VALUES(?,?,?,?,?,?,?)',
                   (token, student_id, student_name, workout_id, workout_name, pdf, normalize_whatsapp(student.get("whatsapp"))))
        sync_student(db, student_name, student.get("whatsapp"), workout_name)
    return token


def record_open(path, token, ip, agent, clock=time.time):
    with connect(path) as db:
        db.execute('BEGIN IMMEDIATE')
        row = db.execute('SELECT * FROM pdf_links WHERE token=? AND active=1', (token,)).fetchone()
        if row is None:
            return False
        now = clock()
        last_seen = db.execute('SELECT MAX(last_seen) FROM pdf_links WHERE student_name=?', (row['student_name'],)).fetchone()[0]
        counted = last_seen is None or now - last_seen >= 60
        sync_student(db, row['student_name'], row['whatsapp'], row['workout_name'], datetime.fromtimestamp(now, TZ).isoformat(timespec='seconds'), int(counted))
        if counted:
            db.execute('INSERT INTO pdf_events(student_id,student_name,workout_id,workout_name,token,event_type,opened_at,ip,user_agent,whatsapp) VALUES(?,?,?,?,?,?,?,?,?,?)',
                       (row['student_id'], row['student_name'], row['workout_id'], row['workout_name'], token,
                        'PDF aberto', datetime.fromtimestamp(now, TZ).isoformat(timespec='seconds'), ip, (agent or '')[:1024], row['whatsapp']))
        db.execute('UPDATE pdf_links SET last_seen=? WHERE token=?', (now, token))
    return True


def record_custom_event(path, student_name, workout_name, event_type, token='direct', ip='', agent='', clock=time.time, whatsapp=''):
    with connect(path) as db:
        db.execute('BEGIN IMMEDIATE')
        now = clock()
        latest = datetime.fromtimestamp(now, TZ).isoformat(timespec='seconds')
        last = db.execute("SELECT opened_at FROM pdf_events WHERE student_name=? AND event_type=? ORDER BY id DESC LIMIT 1",
                          (student_name, event_type)).fetchone()
        counted = not last or now - datetime.fromisoformat(last['opened_at']).timestamp() >= 60
        sync_student(db, student_name, whatsapp, workout_name, latest, int(counted))
        if not counted:
            return False
        db.execute('''INSERT INTO pdf_events(student_id,student_name,workout_id,workout_name,token,event_type,opened_at,ip,user_agent,whatsapp)
                      VALUES(?,?,?,?,?,?,?,?,?,?)''',
                   ('auto-' + hashlib.sha256(student_name.encode()).hexdigest()[:16], student_name,
                    'workout', workout_name, token, event_type, latest, ip, (agent or '')[:1024], normalize_whatsapp(whatsapp)))
        return True


def create_app(db_path, password, network_guard=False):
    from io import BytesIO
    app = Flask(__name__)
    app.config['MAX_CONTENT_LENGTH'] = 20 * 1024 * 1024
    initialize(db_path)

    @app.after_request
    def headers(response):
        response.headers['Cache-Control'] = 'no-store, private, max-age=0'
        response.headers['Referrer-Policy'] = 'no-referrer'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        return response

    def admin(fn):
        @functools.wraps(fn)
        def wrapped(*args, **kwargs):
            auth = request.authorization
            if not auth or auth.type.lower() != 'basic' or auth.username != 'caio' or not hmac.compare_digest((auth.password or '').encode('utf-8'), password.encode('utf-8')):
                return Response('Autenticação do treinador necessária.', 401,
                                {'WWW-Authenticate': 'Basic realm="Treinos - teste", charset="UTF-8"'})
            return fn(*args, **kwargs)
        return wrapped

    @app.get('/')
    @admin
    def editor():
        html = (ROOT / 'index.html').read_text()
        return '<script src="/tracking-test.js"></script></body>'.join(html.rsplit('</body>', 1))

    @app.get('/tracking-test.js')
    @admin
    def javascript():
        return Response((ROOT / 'tracking_test/client.js').read_text(), mimetype='application/javascript')

    @app.post('/api/test/pdf')
    @admin
    def upload():
        if request.headers.get('X-Tracking-Test') != '1':
            abort(403)
        if request.mimetype != 'application/pdf':
            abort(415)
        raw_name = request.headers.get('X-Student-Name', 'Aluno')
        raw_workout = request.headers.get('X-Workout-Name', 'Treino')
        student_name = urllib.parse.unquote(raw_name)
        workout_name = urllib.parse.unquote(raw_workout)
        student_info = {
            'student_id': secrets.token_hex(4),
            'nome': student_name,
            'treino_id': secrets.token_hex(4),
            'treinoNome': workout_name,
            'whatsapp': request.headers.get('X-Student-WhatsApp', '')
        }
        try:
            token = register_pdf(db_path, request.get_data(), student_info)
        except ValueError as exc:
            return jsonify(error=str(exc)), 400
        return jsonify(url='/pdf/rastreado/' + token), 201

    @app.route('/pdf/rastreado/<token>', methods=['GET', 'HEAD'])
    def pdf(token):
        if not re.fullmatch(r'[A-Za-z0-9_-]{43}', token):
            abort(404)
        with connect(db_path) as db:
            row = db.execute('SELECT pdf FROM pdf_links WHERE token=? AND active=1', (token,)).fetchone()
        if row is None:
            abort(404)
        from io import BytesIO
        response = send_file(BytesIO(row['pdf']), mimetype='application/pdf',
                             download_name='treino.pdf', conditional=True, etag=False, max_age=0)
        if request.method == 'GET' and response.status_code in (200, 206):
            if not record_open(db_path, token, request.remote_addr, request.user_agent.string):
                pass
        return response

    @app.get('/r/yt')
    def track_youtube():
        aluno = request.args.get('aluno', 'Aluno').strip()[:200] or 'Aluno'
        treino = request.args.get('treino', 'Treino')[:300]
        ex = request.args.get('ex', 'Exercício')[:300]
        dest = request.args.get('url', 'https://www.youtube.com')
        parsed = urllib.parse.urlsplit(dest)
        if parsed.scheme != 'https' or parsed.hostname not in ('youtube.com', 'www.youtube.com', 'm.youtube.com', 'youtu.be', 'music.youtube.com') or parsed.username or parsed.password:
            abort(400)
        workout_desc = f"{treino} — {ex}" if treino else ex
        record_custom_event(db_path, aluno, workout_desc, 'Vídeo YouTube', 'youtube', request.remote_addr, request.user_agent.string, whatsapp=request.args.get('whatsapp', ''))
        return redirect(dest, 302)

    @app.get('/r/iniciar')
    def track_iniciar():
        aluno = request.args.get('aluno', 'Aluno').strip()[:200] or 'Aluno'
        treino = request.args.get('treino', 'Treino')[:300]
        record_custom_event(db_path, aluno, treino, 'Treino iniciado', 'iniciar', request.remote_addr, request.user_agent.string, whatsapp=request.args.get('whatsapp', ''))
        return render_template_string('''<!doctype html>
<html lang="pt-br">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Treino Iniciado! 💪</title>
<style>
  * { box-sizing: border-box; }
  body {
    margin: 0; padding: 20px;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    display: flex; flex-direction: column; align-items: center; justify-content: center;
    min-height: 85vh; background: #0f172a; color: #fff; text-align: center;
  }
  .card {
    background: #1e293b; padding: 32px 24px; border-radius: 24px;
    box-shadow: 0 12px 32px rgba(0,0,0,0.5); max-width: 340px; width: 100%;
    border: 1px solid #334155;
  }
  .emoji { font-size: 54px; margin-bottom: 12px; }
  h1 { font-size: 24px; color: #22c55e; margin: 0 0 10px; font-weight: 800; }
  p { font-size: 15px; color: #94a3b8; line-height: 1.5; margin: 0 0 24px; }
  .btn {
    display: block; width: 100%; padding: 14px; background: #22c55e; color: #0f172a;
    border-radius: 14px; text-decoration: none; font-weight: 700; font-size: 16px;
    border: none; cursor: pointer;
  }
  .btn:active { transform: scale(0.98); }
  .hint { font-size: 12px; color: #64748b; margin-top: 16px; }
</style>
</head>
<body>
  <div class="card">
    <div class="emoji">💪🔥</div>
    <h1>Treino Iniciado!</h1>
    <p>Bom treino, <strong>{{ aluno }}</strong>!<br>Seu treinador foi avisado.</p>
    <button class="btn" onclick="window.close(); history.back();">Voltar ao PDF</button>
    <div class="hint">Pode fechar esta aba e acompanhar seus exercícios</div>
  </div>
  <script>
    setTimeout(function() { window.close(); }, 3000);
  </script>
</body>
</html>''', aluno=aluno, treino=treino)

    @app.post('/painel/apagar-evento/<int:event_id>')
    @admin
    def delete_event(event_id):
        with connect(db_path) as db:
            row = db.execute('SELECT student_name FROM pdf_events WHERE id=?', (event_id,)).fetchone()
            if row:
                st_name = row['student_name']
                db.execute('DELETE FROM pdf_events WHERE id=?', (event_id,))
                stats = db.execute('SELECT COUNT(*) as tot, MAX(opened_at) as lat FROM pdf_events WHERE student_name=?', (st_name,)).fetchone()
                db.execute('UPDATE students SET total_accesses=?, latest=? WHERE student_name=?',
                           (stats['tot'] or 0, stats['lat'], st_name))
        return redirect('/painel/aberturas-pdf')

    @app.post('/painel/apagar-aluno/<student_name>')
    @admin
    def delete_student(student_name):
        with connect(db_path) as db:
            db.execute('DELETE FROM students WHERE student_name=?', (student_name,))
            db.execute('DELETE FROM pdf_events WHERE student_name=?', (student_name,))
            db.execute('DELETE FROM pdf_links WHERE student_name=?', (student_name,))
        return redirect('/painel/aberturas-pdf')

    @app.post('/painel/limpar-eventos')
    @admin
    def clear_events():
        with connect(db_path) as db:
            db.execute('DELETE FROM pdf_events')
            db.execute('UPDATE students SET total_accesses=0, latest=NULL')
        return redirect('/painel/aberturas-pdf')

    @app.get('/painel/aberturas-pdf')
    @admin
    def dashboard():
        with connect(db_path) as db:
            students = db.execute('SELECT * FROM students ORDER BY latest DESC, student_name').fetchall()
            events = db.execute('SELECT * FROM pdf_events ORDER BY id DESC LIMIT 500').fetchall()
            tot_students = len(students)
            tot_events = len(events)
            latest_time = events[0]['opened_at'] if events else 'Nenhuma'
        return render_template_string('''<!doctype html>
<html lang="pt-br">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>Painel do Treinador | Rastreamento</title>
<style>
  :root {
    --bg: #f8fafc;
    --card: #ffffff;
    --border: #e2e8f0;
    --text: #0f172a;
    --sub: #64748b;
    --primary: #1e293b;
    --accent: #2563eb;
    --danger: #dc2626;
    --success: #16a34a;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    background: var(--bg);
    color: var(--text);
    padding: 16px;
    max-width: 960px;
    margin: 0 auto;
    line-height: 1.4;
  }
  .header {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    justify-content: space-between;
    gap: 10px;
    padding-bottom: 16px;
    border-bottom: 1px solid var(--border);
    margin-bottom: 16px;
  }
  .header h1 {
    font-size: 1.3rem;
    font-weight: 700;
    color: var(--text);
    display: flex;
    align-items: center;
    gap: 8px;
  }
  .header-actions {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
  }
  .btn {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    padding: 7px 12px;
    font-size: 0.8rem;
    font-weight: 600;
    border-radius: 8px;
    border: none;
    cursor: pointer;
    text-decoration: none;
    transition: background .15s;
  }
  .btn-back { background: #e2e8f0; color: #334155; }
  .btn-refresh { background: var(--accent); color: white; }
  .btn-clear { background: #fee2e2; color: var(--danger); }
  .btn-del {
    background: #fee2e2;
    color: var(--danger);
    padding: 3px 8px;
    font-size: 0.75rem;
    border-radius: 6px;
    border: none;
    cursor: pointer;
  }
  .btn-del:hover { background: #fecaca; }
  .btn-wpp {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    background: #dcfce7;
    color: var(--success);
    padding: 4px 8px;
    border-radius: 6px;
    text-decoration: none;
    font-size: 0.75rem;
    font-weight: 600;
  }
  .stats-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
    gap: 10px;
    margin-bottom: 20px;
  }
  .stat-card {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 12px;
    box-shadow: 0 1px 2px rgba(0,0,0,0.03);
  }
  .stat-card .label { font-size: 0.72rem; color: var(--sub); font-weight: 600; text-transform: uppercase; }
  .stat-card .value { font-size: 1.3rem; font-weight: 700; margin-top: 4px; }
  .stat-card .sub { font-size: 0.7rem; color: var(--sub); margin-top: 2px; }
  .section-title {
    font-size: 1rem;
    font-weight: 700;
    margin-bottom: 10px;
    display: flex;
    align-items: center;
    justify-content: space-between;
  }
  .card-box {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 14px;
    overflow: hidden;
    margin-bottom: 24px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.03);
  }
  .table-responsive { width: 100%; overflow-x: auto; }
  table { width: 100%; border-collapse: collapse; text-align: left; font-size: 0.82rem; }
  th { background: #f8fafc; padding: 10px 12px; font-weight: 600; color: var(--sub); border-bottom: 1px solid var(--border); }
  td { padding: 10px 12px; border-bottom: 1px solid var(--border); vertical-align: middle; }
  tr:last-child td { border-bottom: none; }
  .badge {
    display: inline-block;
    padding: 3px 8px;
    border-radius: 20px;
    font-size: 0.72rem;
    font-weight: 600;
  }
  .badge-yt { background: #fee2e2; color: #b91c1c; }
  .badge-start { background: #dcfce7; color: #15803d; }
  .badge-pdf { background: #e0f2fe; color: #0369a1; }
  .empty { padding: 24px; text-align: center; color: var(--sub); font-size: 0.85rem; }
  .nowrap { white-space: nowrap; }
</style>
</head>
<body>
  <div class="header">
    <h1>📊 Painel de Atividades</h1>
    <div class="header-actions">
      <a href="/" class="btn btn-back">← Editor</a>
      <a href="" class="btn btn-refresh">🔄 Atualizar</a>
      {% if events %}
      <form action="/painel/limpar-eventos" method="post" onsubmit="return confirm('Deseja limpar todo o histórico de testes? Os cadastros dos alunos serão mantidos.');" style="display:inline;">
        <button type="submit" class="btn btn-clear">🧹 Limpar Histórico</button>
      </form>
      {% endif %}
    </div>
  </div>

  <div class="stats-grid">
    <div class="stat-card">
      <div class="label">Alunos</div>
      <div class="value">{{ tot_students }}</div>
      <div class="sub">Cadastrados</div>
    </div>
    <div class="stat-card">
      <div class="label">Acessos</div>
      <div class="value">{{ tot_events }}</div>
      <div class="sub">Vídeos / Treinos</div>
    </div>
    <div class="stat-card">
      <div class="label">Última Atividade</div>
      <div class="value" style="font-size:0.95rem;padding-top:4px;">{{ latest_time.split('T')[-1] if 'T' in latest_time else (latest_time or 'Nenhuma') }}</div>
      <div class="sub">{{ latest_time.split('T')[0] if 'T' in latest_time else '' }}</div>
    </div>
  </div>

  <div class="section-title">
    <span>👥 Alunos Cadastrados ({{ tot_students }})</span>
  </div>
  <div class="card-box">
    <div class="table-responsive">
      <table>
        <thead>
          <tr>
            <th>Aluno</th>
            <th>WhatsApp</th>
            <th>Último Exercício</th>
            <th class="nowrap">Total</th>
            <th>Último Acesso</th>
            <th style="text-align:right;">Ação</th>
          </tr>
        </thead>
        <tbody>
          {% for r in students %}
          <tr>
            <td><strong>{{ r.student_name }}</strong></td>
            <td>
              {% if r.whatsapp %}
                <a href="https://wa.me/{{ r.whatsapp }}" target="_blank" rel="noopener" class="btn-wpp">
                  💬 {{ r.whatsapp }}
                </a>
              {% else %}
                <span style="color:#94a3b8;font-size:0.75rem;">Sem WhatsApp</span>
              {% endif %}
            </td>
            <td>{{ r.workout_name or '-' }}</td>
            <td><strong style="color:var(--accent);">{{ r.total_accesses }}x</strong></td>
            <td class="nowrap" style="color:var(--sub);font-size:0.75rem;">{{ r.latest or 'Ainda não abriu' }}</td>
            <td style="text-align:right;">
              <form action="/painel/apagar-aluno/{{ r.student_name }}" method="post" onsubmit="return confirm('Excluir o aluno {{ r.student_name }} e todo seu histórico do painel?');" style="display:inline;">
                <button type="submit" class="btn-del" title="Excluir Aluno">🗑️ Apagar</button>
              </form>
            </td>
          </tr>
          {% else %}
          <tr>
            <td colspan="6" class="empty">Nenhum aluno registrado ainda.</td>
          </tr>
          {% endfor %}
        </tbody>
      </table>
    </div>
  </div>

  <div class="section-title">
    <span>⚡ Linha do Tempo de Acessos Recentes</span>
  </div>
  <div class="card-box">
    <div class="table-responsive">
      <table>
        <thead>
          <tr>
            <th>Horário</th>
            <th>Aluno</th>
            <th>Exercício / Treino</th>
            <th>Ação</th>
            <th style="text-align:right;">Ação</th>
          </tr>
        </thead>
        <tbody>
          {% for r in events %}
          <tr>
            <td class="nowrap" style="font-size:0.75rem;color:var(--sub);">
              <strong>{{ r.opened_at.split('T')[-1][:5] if 'T' in r.opened_at else r.opened_at }}</strong>
              <div style="font-size:0.65rem;">{{ r.opened_at.split('T')[0] if 'T' in r.opened_at else '' }}</div>
            </td>
            <td><strong>{{ r.student_name }}</strong></td>
            <td>{{ r.workout_name }}</td>
            <td>
              {% if 'iniciado' in r.event_type %}
                <span class="badge badge-start">🟢 Treino Iniciado</span>
              {% elif 'Vídeo' in r.event_type %}
                <span class="badge badge-yt">▶️ YouTube</span>
              {% else %}
                <span class="badge badge-pdf">📄 PDF</span>
              {% endif %}
            </td>
            <td style="text-align:right;">
              <form action="/painel/apagar-evento/{{ r.id }}" method="post" onsubmit="return confirm('Apagar este registro?');" style="display:inline;">
                <button type="submit" class="btn-del" title="Apagar Registro">🗑️</button>
              </form>
            </td>
          </tr>
          {% else %}
          <tr>
            <td colspan="5" class="empty">Nenhuma atividade registrada ainda.</td>
          </tr>
          {% endfor %}
        </tbody>
      </table>
    </div>
  </div>
</body>
</html>''', students=students, events=events, tot_students=tot_students, tot_events=tot_events, latest_time=latest_time)

    return app


def credentials():
    DATA.mkdir(mode=0o700, exist_ok=True)
    path = DATA / 'pdf_tracking_test_credentials.json'
    if not path.exists():
        with open(path, 'x', opener=lambda p, flags: os.open(p, flags, 0o600)) as f:
            json.dump({'username': 'caio', 'password': secrets.token_urlsafe(18)}, f)
    return json.loads(path.read_text())


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8765)
    args = parser.parse_args()
    os.umask(0o077)
    auth = credentials()
    app = create_app(DATA / 'pdf_tracking_test.db', auth['password'])
    server = make_server('0.0.0.0', args.port, app, threaded=True)
    try:
        ip = subprocess.check_output(['tailscale', 'ip', '-4'], text=True).strip().splitlines()[0]
    except (OSError, subprocess.CalledProcessError, IndexError):
        ip = '127.0.0.1'
    print(f'Painel: http://{ip}:{args.port}/painel/aberturas-pdf', flush=True)
    print('Credenciais locais: data/pdf_tracking_test_credentials.json', flush=True)
    import logging
    logging.getLogger('werkzeug').disabled = True
    server.serve_forever()


if __name__ == '__main__':
    main()
