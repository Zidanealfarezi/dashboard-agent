import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from app import hermes_bridge, review


class BridgeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name); (self.root / 'config').mkdir()
        for name in ['hermes', 'project', 'autopilot']:
            config = json.loads((hermes_bridge.ROOT / f'config/{name}.json').read_text())
            self.write(name, config)

    def write(self, name, config):
        (self.root / f'config/{name}.json').write_text(json.dumps(config))

    def enable(self):
        for name, fields in [('hermes', {'execution_enabled': True}),
                             ('project', {'mode': 'pilot', 'operator': 'hermes'}),
                             ('autopilot', {'enabled': True})]:
            config = json.loads((self.root / f'config/{name}.json').read_text())
            config.update(fields); self.write(name, config)

    def test_setup_mode_spawns_nothing_and_creates_no_lock(self):
        # Jangan bergantung pada kondisi config repo (bisa sudah aktif): paksa setup mode.
        hermes = json.loads((self.root / 'config/hermes.json').read_text())
        hermes['execution_enabled'] = False
        self.write('hermes', hermes)
        project = json.loads((self.root / 'config/project.json').read_text())
        project.update({'mode': 'setup_only', 'operator': 'hermes'})
        self.write('project', project)
        with patch('subprocess.run', side_effect=AssertionError('No worker allowed')):
            with self.assertRaises(review.ReviewError):
                hermes_bridge.launch(self.root, 'nara', 'Test')
        self.assertFalse((self.root / 'operations').exists())

    def test_command_routes_character_without_shell_or_credentials(self):
        self.enable()
        command = hermes_bridge.command(self.root, 'dinda', 'Only local test')
        self.assertEqual(command[1:3], ['-p', 'ai-influencer-dinda'])
        bang_ray_cmd = hermes_bridge.command(self.root, 'bang_ray', 'Only local test')
        self.assertEqual(bang_ray_cmd[1:3], ['-p', 'ai-influencer-bang-ray'])
        self.assertEqual(command[3:5], ['--in', str(self.root)])
        self.assertIn('--oneshot', command)
        # Provider mengikuti config/hermes.json (migrasi 5 Nov 2026: deepseek), bukan nama hardcode.
        provider = json.loads((hermes_bridge.ROOT / 'config/hermes.json').read_text())['model']['provider']
        self.assertEqual(command[command.index('--provider') + 1], provider)
        self.assertNotIn('auth.json', ' '.join(command))

    def test_wrong_operator_and_profile_rejected(self):
        self.enable()
        project = json.loads((self.root / 'config/project.json').read_text())
        project['operator'] = 'codex_chat'; self.write('project', project)
        with self.assertRaises(review.ReviewError): hermes_bridge.command(self.root, 'nara', 'Test')
        with self.assertRaises(review.ReviewError): hermes_bridge.command(self.root, '../other', 'Test')

    def test_concurrent_worker_is_blocked(self):
        import fcntl
        self.enable(); (self.root / 'operations').mkdir()
        with (self.root / 'operations/hermes-worker.lock').open('a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            with patch('subprocess.run', side_effect=AssertionError('No second worker')):
                with self.assertRaises(review.ReviewError):
                    hermes_bridge.launch(self.root, 'nara', 'Test')


if __name__ == '__main__': unittest.main()
