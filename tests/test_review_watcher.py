"""Tests for scripts/telegram_review_watcher.py prompt ACC handling."""
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest

from app import publication, review
from scripts import telegram_review_watcher as watcher


class FakeWatcherAPI:
    def __init__(self, updates=None, fail_get=False):
        self.updates = list(updates or [])
        self.fail_get = fail_get
        self.calls = []

    def call(self, method, fields, document=None):
        self.calls.append((method, fields))
        if method == "getUpdates":
            if self.fail_get:
                raise review.ReviewError("Simulasi gangguan jaringan Telegram")
            return self.updates
        return {"message_id": 200 + len(self.calls)}


class ReviewWatcherTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / "operations").mkdir()
        (self.root / "config").mkdir()
        (self.root / "characters/bang_ray/content/slot1").mkdir(parents=True)
        media_file = self.root / "characters/bang_ray/content/slot1/video.mp4"
        media_file.write_bytes(b"mp4-fixture-bytes")

        self.config = {
            "enabled": True,
            "token_verified": True,
            "recipient_paired": True,
            "allowed_user_ids": [7463982122],
            "allowed_chat_ids": [7463982122],
            "bot_id": 9159288377,
        }
        (self.root / "config/project.json").write_text(json.dumps({"telegram_enabled": True, "publication_enabled": True}))
        (self.root / "config/telegram.json").write_text(json.dumps(self.config))

        with sqlite3.connect(self.root / "operations/production.sqlite") as db:
            db.executescript((review.ROOT / "operations/schema.sql").read_text())
            db.executescript((review.ROOT / "operations/migrations/002_telegram_review.sql").read_text())
            db.execute("INSERT INTO characters VALUES ('bang_ray', 'Bang Ray', '@teuku.rayyan00')")
            db.commit()

        with review.connect(self.root) as db:
            self.vid = review.register(db, self.root, "bang_ray", "bang_ray_slot1", "video",
                                       "characters/bang_ray/content/slot1/video.mp4", "Tips pasang keramik")
            self.rid = review.prepare(db, self.root, self.vid, 7463982122)
            review.send(db, self.root, self.rid, FakeWatcherAPI())

    def test_poll_once_records_acc_and_unlocks_publication(self):
        updates = [{
            "update_id": 500,
            "callback_query": {
                "id": "cb_500",
                "from": {"id": 7463982122, "is_bot": False},
                "data": f"rv:{self.rid}:a",
                "message": {"message_id": 202, "chat": {"id": 7463982122, "type": "private"}, "from": {"id": 9159288377}},
            },
        }]
        api = FakeWatcherAPI(updates=updates)
        res = watcher.poll_once(root=self.root, api_factory=lambda _r: api)
        self.assertTrue(res["ok"])
        self.assertEqual(res["processed"], 1)
        methods = [m for m, _ in api.calls]
        self.assertIn("answerCallbackQuery", methods)
        self.assertIn("editMessageText", methods)

        with review.connect(self.root) as db:
            row, _ = review.approved_package(db, self.root, self.vid)
            self.assertEqual(row["id"], self.vid)
            pub = publication.begin(db, self.root, self.vid, "@teuku.rayyan00")
            self.assertEqual(pub["account"], "@teuku.rayyan00")

    def test_poll_once_handles_network_error_without_crashing(self):
        res = watcher.poll_once(root=self.root, api_factory=lambda _r: FakeWatcherAPI(fail_get=True))
        self.assertFalse(res["ok"])
        self.assertFalse(res["skipped"])
        self.assertIn("jaringan", res["reason"])


if __name__ == "__main__":
    unittest.main()
