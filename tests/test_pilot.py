import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from datetime import datetime
from unittest.mock import patch
from app import autopilot, pilot, review


class PilotTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'config').mkdir()
        (self.root / 'characters/dinda').mkdir(parents=True)
        self.write('config/project.json', {'mode': 'controlled_pilot'})
        self.write('config/pilot.json', {'scope': 'controlled_pilot_not_unattended_operations',
            'flow_total_credit_cap': 25, 'authorized_on': datetime.now(autopilot.WIB).date().isoformat()})
        self.write('characters/dinda/profile.json', {'id': 'dinda'})
        self.db = sqlite3.connect(':memory:')
        self.addCleanup(self.db.close)
        for path in ['operations/schema.sql', 'operations/migrations/002_telegram_review.sql',
                     'operations/migrations/003_autopilot.sql']:
            self.db.executescript((pilot.ROOT / path).read_text())
        self.db.execute("INSERT INTO characters VALUES('dinda','Dinda','@dinda.kemala_')")
        self.db.commit()
        self.plan = {'purpose': 'technical_identity_test', 'character_id': 'dinda',
                     'kind': 'video', 'duration_seconds': 6, 'caption': 'Technical test only',
                     'shots': [{'seconds': 6, 'prompt': 'Single identity test'}],
                     'new_biography_facts': [], 'promotional': False}

    def write(self, path, data):
        (self.root / path).write_text(json.dumps(data))

    def test_one_technical_slot_does_not_create_a_job_or_publish(self):
        with patch('app.autopilot.reference_status', return_value={'state': 'ready'}):
            slot = pilot.prepare(self.db, self.root, self.plan)
            self.assertTrue(slot.startswith('dinda-technical-pilot-'))
            with self.assertRaises(review.ReviewError):
                pilot.prepare(self.db, self.root, self.plan)
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM generation_jobs').fetchone()[0], 0)
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM publications').fetchone()[0], 0)

    def test_daily_content_cannot_use_technical_pilot_path(self):
        with self.assertRaises(review.ReviewError):
            pilot.prepare(self.db, self.root, dict(self.plan, purpose='daily_content'))

    def test_setup_mode_and_missing_identity_are_rejected(self):
        self.write('config/project.json', {'mode': 'setup_only'})
        with self.assertRaises(review.ReviewError):
            pilot.prepare(self.db, self.root, self.plan)
        self.write('config/project.json', {'mode': 'controlled_pilot'})
        with patch('app.autopilot.reference_status', return_value={'state': 'missing'}):
            with self.assertRaises(review.ReviewError):
                pilot.prepare(self.db, self.root, self.plan)


if __name__ == '__main__':
    unittest.main()
