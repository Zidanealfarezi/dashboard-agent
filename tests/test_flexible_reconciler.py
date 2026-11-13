import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sqlite3
import tempfile
import json

from app import flexible_reconciler

WIB = timezone(timedelta(hours=7))

class TestFlexibleReconciler(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp_dir.name)
        (self.root / "config").mkdir(parents=True)
        (self.root / "operations").mkdir(parents=True)

        project_cfg = {
            "publication_schedules": {
                "dinda": {"production_time_wib": "09:00", "publish_time_wib": "11:30"},
                "isk": {"production_time_wib": "10:00", "publish_time_wib": "13:00"},
                "bang_ray": {"production_time_wib": "14:00", "publish_time_wib": "16:00"},
                "pak_vincent": {"production_time_wib": "15:00", "publish_time_wib": "18:00"}
            }
        }
        (self.root / "config/project.json").write_text(json.dumps(project_cfg))

        self.db = sqlite3.connect(":memory:")
        self.db.row_factory = sqlite3.Row
        self.db.execute("""
            CREATE TABLE daily_slots (
                id TEXT PRIMARY KEY,
                day TEXT NOT NULL,
                character_id TEXT NOT NULL,
                kind TEXT NOT NULL,
                duration_seconds INTEGER,
                state TEXT NOT NULL,
                plan_json TEXT,
                profile_sha256 TEXT,
                job_id TEXT,
                version_id TEXT,
                delivery_id TEXT,
                created_at TEXT NOT NULL
            )
        """)

    def tearDown(self):
        self.db.close()
        self.tmp_dir.cleanup()

    def test_schedule_windows_cutoff_calculation(self):
        now_dt = datetime(2026, 11, 13, 10, 15, tzinfo=WIB)
        windows = flexible_reconciler.get_schedule_windows(self.root, now_dt)

        self.assertEqual(windows["dinda"]["cutoff_time_wib"], "10:30")
        self.assertEqual(windows["isk"]["cutoff_time_wib"], "12:00")
        self.assertEqual(windows["bang_ray"]["cutoff_time_wib"], "15:00")
        self.assertEqual(windows["pak_vincent"]["cutoff_time_wib"], "17:00")

        # At 10:15 WIB:
        # Dinda is within retry window (09:00 - 10:30)
        self.assertTrue(windows["dinda"]["is_within_retry_window"])
        self.assertFalse(windows["dinda"]["is_past_cutoff"])

        # ISK is within retry window (10:00 - 12:00)
        self.assertTrue(windows["isk"]["is_within_retry_window"])
        self.assertFalse(windows["isk"]["is_past_cutoff"])
        self.assertEqual(windows["isk"]["minutes_to_cutoff"], 105)

        # Bang Ray is NOT due yet (prod at 14:00)
        self.assertFalse(windows["bang_ray"]["is_production_due"])
        self.assertFalse(windows["bang_ray"]["is_within_retry_window"])
        self.assertFalse(windows["bang_ray"]["is_past_cutoff"])

    def test_past_cutoff_state(self):
        # Clock at 12:15 WIB
        now_dt = datetime(2026, 11, 13, 12, 15, tzinfo=WIB)
        windows = flexible_reconciler.get_schedule_windows(self.root, now_dt)

        # ISK cutoff is 12:00, so at 12:15 it is past cutoff
        self.assertTrue(windows["isk"]["is_past_cutoff"])
        self.assertFalse(windows["isk"]["is_within_retry_window"])

    def test_evaluate_and_reconcile_attempt_progression(self):
        # ISK slot created as 'planned' without version_id
        self.db.execute("""
            INSERT INTO daily_slots (id, day, character_id, kind, state, created_at)
            VALUES ('isk-2026-11-13', '2026-11-13', 'isk', 'video', 'planned', '2026-11-13T01:00:00Z')
        """)
        self.db.commit()

        # Run 1 at 10:05 WIB (inside retry window)
        now_dt = datetime(2026, 11, 13, 10, 5, tzinfo=WIB)
        res1 = flexible_reconciler.evaluate_and_reconcile(self.db, self.root, now_dt=now_dt, dry_run=False)
        actions1 = [a for a in res1["actions_taken"] if a["character_id"] == "isk"]
        self.assertEqual(len(actions1), 1)
        self.assertEqual(actions1[0]["action"], "silent_auto_recovery_attempt_1")

        # Run 2 at 10:15 WIB (still stuck) -> should trigger attempt 2 critical alert
        now_dt2 = datetime(2026, 11, 13, 10, 15, tzinfo=WIB)
        res2 = flexible_reconciler.evaluate_and_reconcile(self.db, self.root, now_dt=now_dt2, dry_run=False)
        actions2 = [a for a in res2["actions_taken"] if a["character_id"] == "isk"]
        self.assertEqual(len(actions2), 1)
        self.assertEqual(actions2[0]["action"], "critical_telegram_alert_attempt_2")

        # Run 3 at 12:05 WIB (past cutoff) -> should trigger skip notification
        now_dt3 = datetime(2026, 11, 13, 12, 5, tzinfo=WIB)
        res3 = flexible_reconciler.evaluate_and_reconcile(self.db, self.root, now_dt=now_dt3, dry_run=False)
        actions3 = [a for a in res3["actions_taken"] if a["character_id"] == "isk"]
        self.assertEqual(len(actions3), 1)
        self.assertEqual(actions3[0]["action"], "skip_due_to_cutoff_exceeded")

if __name__ == "__main__":
    unittest.main()
