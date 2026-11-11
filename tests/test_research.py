from datetime import datetime, timedelta, timezone
from pathlib import Path
import tempfile
import unittest
from app import research


class ResearchTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.db = research.connect(Path(self.temp.name) / 'catalog.sqlite')
        self.addCleanup(self.db.close)
        self.candidate = {'url': 'https://www.tiktok.com/@a/video/123?utm_source=x',
                          'title': 'Example', 'evidence': 'Observed example, no trend claim',
                          'verification_status': 'candidate_unverified',
                          'sound_url': 'https://www.tiktok.com/music/example-987'}
        self.today = datetime.now(timezone.utc) - timedelta(minutes=1)

    def test_same_post_next_day_keeps_observations_without_duplicate_source(self):
        research.record(self.db, self.candidate, (self.today - timedelta(days=1)).isoformat())
        updated = dict(self.candidate, url='https://www.tiktok.com/@renamed/video/123?x=2')
        result = research.record(self.db, updated, self.today.isoformat())
        self.assertEqual(result['classification'], 'existing_reference')
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM sources').fetchone()[0], 1)
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM observations').fetchone()[0], 2)

    def test_new_post_same_sound_is_recognized(self):
        research.record(self.db, self.candidate, self.today.isoformat())
        result = research.record(self.db, dict(self.candidate,
            url='https://www.tiktok.com/@b/video/456'), self.today.isoformat())
        self.assertEqual(result['classification'], 'new_reference_same_sound')

    def test_missing_evidence_or_future_timestamp_is_rejected(self):
        with self.assertRaises(ValueError):
            research.record(self.db, dict(self.candidate, evidence=''), self.today.isoformat())
        with self.assertRaises(ValueError):
            research.record(self.db, self.candidate, (self.today + timedelta(days=2)).isoformat())

    def test_short_link_is_not_claimed_to_match_resolved_post(self):
        self.assertNotEqual(research.identity('https://vt.tiktok.com/abc/')[0],
                            research.identity(self.candidate['url'])[0])


if __name__ == '__main__':
    unittest.main()
