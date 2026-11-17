"""Private Treino36 snapshot receiver and fortnightly Drive backup."""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import time
from contextlib import contextmanager
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parent
DATA = Path(os.environ.get('TREINO36_BACKUP_DIR', '/home/caio/.local/share/treino36-backup'))
ORIGIN = 'https://caio.tail953b6e.ts.net:8443'
FOLDER = '11RtO6KGo7Vpp4luIvPnno___qIn4ToPF'
INTERVAL = 15 * 86400
MAX_BYTES = 64 * 1024 * 1024

class RevisionConflict(Exception):
    pass

@contextmanager
def locked():
    DATA.mkdir(mode=0o700, parents=True, exist_ok=True)
    with (DATA / 'lock').open('a') as handle:
        fcntl.flock(handle, fcntl.LOCK_EX)
        yield

def read_state():
    path = DATA / 'state.json'
    return json.loads(path.read_text()) if path.exists() else {}

def atomic(path, data):
    fd, name = tempfile.mkstemp(dir=DATA)
    try:
        with os.fdopen(fd, 'wb') as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)

def save_state(state):
    atomic(DATA / 'state.json', json.dumps(state).encode())

def validate(payload, allow_empty=False):
    if not isinstance(payload, dict) or payload.get('tipo') != 'treino36-completo':
        raise ValueError('Backup completo inválido.')
    for key in ('alunos', 'avaliacoes', 'mobilidades'):
        if not isinstance(payload.get(key), list):
            raise ValueError('Lista inválida: ' + key)
    if not payload['alunos'] and not allow_empty:
        raise ValueError('Backup vazio recusado para preservar a cópia anterior.')
    if 'treino36:photo:' in json.dumps(payload):
        raise ValueError('Há fotos ainda não carregadas. Aguarde e tente novamente.')

def snapshot(payload, client=None, expected_revision=None):
    validate(payload, allow_empty=bool(expected_revision))
    encoded = json.dumps(payload, ensure_ascii=False, separators=(',', ':')).encode()
    with locked():
        state = read_state()
        if expected_revision is not None and expected_revision != state.get('sha256', ''):
            raise RevisionConflict('Há alterações de outro navegador. Sincronize antes de enviar novamente.')
        if expected_revision is None and client and state.get('client') not in (None, client):
            raise PermissionError('O backup já recebe dados de outro navegador. Use o navegador principal.')
        if expected_revision is None and client and not state.get('client') and (DATA / 'latest.json').exists():
            previous = json.loads((DATA / 'latest.json').read_text())
            previous_ids = {student.get('student_id') for student in previous['alunos']}
            incoming_ids = {student.get('student_id') for student in payload['alunos']}
            if not previous_ids.issubset(incoming_ids):
                raise PermissionError('Carregue seu JSON completo neste navegador antes de ativar o backup automático.')
        if client:
            state['client'] = client
        if (DATA / 'latest.json').exists():
            atomic(DATA / 'previous.json', (DATA / 'latest.json').read_bytes())
        atomic(DATA / 'latest.json', encoded)
        state.update(received_at=time.time(), students=len(payload['alunos']), sha256=hashlib.sha256(encoded).hexdigest())
        save_state(state)
        return state

class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def result(self, code, value):
        body = json.dumps(value).encode()
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Cache-Control', 'no-store')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == '/api/sync':
            with locked():
                state = read_state()
                payload = json.loads((DATA / 'latest.json').read_text()) if (DATA / 'latest.json').exists() else None
            self.result(200, {'revision':state.get('sha256', ''), 'data':payload, 'client':state.get('client'), 'received_at':state.get('received_at')})
        elif self.path == '/api/backup/status':
            with locked():
                state = read_state()
            self.result(200, {k: state.get(k) for k in ('received_at', 'uploaded_at', 'students', 'error', 'sha256')})
        elif self.path.startswith('/api/'):
            self.result(404, {'error': 'Não encontrado.'})
        elif any(part.startswith('.') for part in unquote(urlsplit(self.path).path).split('/')) or urlsplit(self.path).path.endswith('.py'):
            self.send_error(404)
        else:
            super().do_GET()

    def do_POST(self):
        if self.path == '/api/backup/snapshot':
            return self.result(409, {'error': 'Recarregue o Treino36 para ativar a sincronização entre navegadores.'})
        if self.path != '/api/sync':
            return self.result(404, {'error': 'Não encontrado.'})
        if self.headers.get('Origin') != ORIGIN or self.headers.get('Content-Type', '').split(';')[0] != 'application/json':
            return self.result(403, {'error': 'Origem não autorizada.'})
        client = self.headers.get('X-Treino36-Client', '')
        if not 16 <= len(client) <= 100:
            return self.result(400, {'error': 'Identificação do navegador ausente.'})
        try:
            size = int(self.headers.get('Content-Length', '0'))
            if not 0 < size <= MAX_BYTES:
                return self.result(413, {'error': 'Tamanho do backup inválido.'})
            revision = self.headers.get('X-Treino36-Revision')
            if revision is None:
                return self.result(428, {'error':'A versão de origem é obrigatória.'})
            state = snapshot(json.loads(self.rfile.read(size)), client, revision)
            return self.result(200, {'received_at': state['received_at'], 'revision':state['sha256']})
        except RevisionConflict as error:
            return self.result(409, {'error':str(error)})
        except PermissionError as error:
            return self.result(409, {'error': str(error)})
        except (ValueError, TypeError) as error:
            return self.result(400, {'error': str(error)})

def upload(force=False):
    # Keep snapshots stable until the upload and its verification finish.
    with locked():
        state = read_state()
        if not (DATA / 'latest.json').exists():
            return
        if not force and time.time() - state.get('uploaded_at', 0) < INTERVAL:
            return
        flags = ['--drive-root-folder-id', FOLDER, '--contimeout', '15s', '--timeout', '90s', '--retries', '2']
        try:
            subprocess.run(['/home/caio/.local/bin/rclone', 'copyto', str(DATA / 'latest.json'), 'gdrive:treino36-backup.json', *flags], check=True, timeout=240, capture_output=True)
            result = subprocess.run(['/home/caio/.local/bin/rclone', 'lsjson', 'gdrive:treino36-backup.json', '--stat', '--hash', *flags], check=True, timeout=120, capture_output=True)
            remote = json.loads(result.stdout)
            content = (DATA / 'latest.json').read_bytes()
            if remote['Size'] != len(content) or remote.get('Hashes', {}).get('md5') != hashlib.md5(content).hexdigest():
                raise ValueError('A verificação do arquivo no Drive falhou.')
            if state.get('drive_file_id') and state['drive_file_id'] != remote.get('ID'):
                raise ValueError('O identificador do backup no Drive mudou.')
            state.update(uploaded_at=time.time(), uploaded_received_at=state['received_at'], drive_file_id=remote.get('ID'), error=None)
            save_state(state)
        except Exception:
            state['error'] = 'Falha no envio ao Drive. A cópia local foi preservada; nova tentativa automática.'
            save_state(state)
            raise

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['serve', 'upload', 'seed'])
    parser.add_argument('--file')
    parser.add_argument('--force', action='store_true')
    args = parser.parse_args()
    if args.action == 'serve':
        ThreadingHTTPServer(('127.0.0.1', 8036), Handler).serve_forever()
    elif args.action == 'seed':
        snapshot(json.loads(Path(args.file).read_text()))
    else:
        upload(args.force)
