import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import threading
import urllib.request
import urllib.error
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('backup', Path(__file__).parents[1] / 'backup-server.py')
backup = importlib.util.module_from_spec(spec)
spec.loader.exec_module(backup)

class BackupTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        backup.DATA = Path(self.temp.name)
        self.payload = {'tipo':'treino36-completo','alunos':[{'student_id':'a'}], 'avaliacoes':[], 'mobilidades':[]}

    def test_empty_or_unhydrated_cannot_replace_snapshot(self):
        backup.snapshot(self.payload)
        before = (backup.DATA / 'latest.json').read_bytes()
        with self.assertRaises(ValueError):
            backup.snapshot({**self.payload, 'alunos':[]})
        with self.assertRaises(ValueError):
            backup.snapshot({**self.payload, 'photo':'treino36:photo:abc'})
        self.assertEqual(before, (backup.DATA / 'latest.json').read_bytes())

    def test_first_browser_must_have_all_seed_students(self):
        backup.snapshot(self.payload)
        with self.assertRaises(PermissionError):
            backup.snapshot({**self.payload, 'alunos':[{'student_id':'other'}]}, 'client-one')
        backup.snapshot(self.payload, 'client-one')
        with self.assertRaises(PermissionError):
            backup.snapshot(self.payload, 'client-two')

    def test_fifteen_days_and_same_destination(self):
        backup.snapshot(self.payload)
        content = (backup.DATA / 'latest.json').read_bytes()
        result = type('Result', (), {'stdout':json.dumps({'Size':len(content), 'Hashes':{'md5':backup.hashlib.md5(content).hexdigest()}, 'ID':'same-file'}).encode()})()
        with patch.object(backup.subprocess, 'run', return_value=result) as run, patch.object(backup.time, 'time', return_value=2000000):
            backup.upload()
            self.assertEqual(run.call_args_list[0].args[0][3], 'gdrive:treino36-backup.json')
            self.assertEqual(backup.read_state()['drive_file_id'], 'same-file')
            self.assertEqual(run.call_count, 2)
        with patch.object(backup.subprocess, 'run', return_value=result) as run, patch.object(backup.time, 'time', return_value=2000000 + backup.INTERVAL - 1):
            backup.upload()
            run.assert_not_called()
        with patch.object(backup.subprocess, 'run', return_value=result) as run, patch.object(backup.time, 'time', return_value=2000000 + backup.INTERVAL):
            backup.upload()
            self.assertEqual(run.call_count, 2)

    def test_upload_failure_keeps_snapshot_and_deadline(self):
        backup.snapshot(self.payload)
        with patch.object(backup.subprocess, 'run', side_effect=RuntimeError('offline')):
            with self.assertRaises(RuntimeError):
                backup.upload()
        self.assertTrue((backup.DATA / 'latest.json').exists())
        self.assertNotIn('uploaded_at', backup.read_state())
        self.assertTrue(backup.read_state()['error'])

    def test_explicit_versioned_delete_is_preserved_and_stale_delete_rejected(self):
        initial=backup.snapshot(self.payload)
        updated=backup.snapshot({**self.payload,'alunos':[]}, 'client-a', initial['sha256'])
        self.assertEqual(updated['students'],0)
        self.assertEqual(json.loads((backup.DATA/'previous.json').read_text())['alunos'],self.payload['alunos'])
        with self.assertRaises(backup.RevisionConflict):
            backup.snapshot(self.payload,'client-b',initial['sha256'])

    def test_http_upload_requires_private_origin_and_preserves_data(self):
        server = backup.ThreadingHTTPServer(('127.0.0.1', 0), backup.Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        url = 'http://127.0.0.1:' + str(server.server_port)
        def request(origin, payload, client='test-browser-123456', revision=''):
            return urllib.request.urlopen(urllib.request.Request(url + '/api/sync', data=json.dumps(payload).encode(), headers={'Origin':origin, 'Content-Type':'application/json', 'X-Treino36-Client':client, 'X-Treino36-Revision':revision}), timeout=5)
        with self.assertRaises(urllib.error.HTTPError) as error:
            request('https://unrelated.test', self.payload)
        self.assertEqual(error.exception.code, 403)
        with request(backup.ORIGIN, self.payload) as response:
            self.assertEqual(response.status, 200)
        with urllib.request.urlopen(url + '/api/backup/status') as response:
            self.assertEqual(json.load(response)['students'], 1)
        with self.assertRaises(urllib.error.HTTPError) as error:
            request(backup.ORIGIN, self.payload, 'different-browser-123456')
        self.assertEqual(error.exception.code, 409)
        with urllib.request.urlopen(url + '/api/sync') as response:
            cloud=json.load(response)
        with request(backup.ORIGIN, {**self.payload,'mobilidades':[{'id':'new'}]}, 'different-browser-123456', cloud['revision']) as response:
            self.assertEqual(response.status, 200)
        self.assertEqual(backup.read_state()['students'], 1)
        self.assertTrue((backup.DATA / 'previous.json').exists())

if __name__ == '__main__':
    unittest.main()
