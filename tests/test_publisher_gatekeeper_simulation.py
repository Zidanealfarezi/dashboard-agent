"""Automated simulation tests for the Unified Publisher Gatekeeper.

Verifies the 4 core gatekeeper failure modes without consuming Flow credits
and without touching live TikTok Studio:
1. Case A: Scheduled slot mismatch / wrong time (rejects if outside scheduled window).
2. Case B: Missing / invalid Telegram callback ACC (rejects chat approvals or unauthenticated reviewers).
3. Case C: Media integrity / file hash mismatch (rejects if file bytes changed after approval).
4. Case D: Caption mismatch / truncation / placeholder (rejects if editor caption does not match 100%).
"""
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
import uuid

from app import publication, review

WIB = timezone(timedelta(hours=7))


def normalize_caption(text):
    return " ".join(text.replace("\r\n", "\n").split()).strip()


def verify_editor_caption(editor_text, expected_caption):
    norm_editor = normalize_caption(editor_text)
    norm_expected = normalize_caption(expected_caption)
    is_bad_placeholder = any(
        ph in editor_text.lower() for ph in ["final_vlog", ".mp4", "final_10s", "raw_flow"]
    )
    is_exact_match = norm_editor == norm_expected
    return {
        "ok": is_exact_match and not is_bad_placeholder,
        "is_exact_match": is_exact_match,
        "is_bad_placeholder": is_bad_placeholder,
        "text": editor_text,
        "expected": expected_caption,
    }


class TestPublisherGatekeeperSimulation(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.db_path = self.root / "operations/production.sqlite"
        self.db_path.parent.mkdir(parents=True)
        self.db = sqlite3.connect(self.db_path)
        self.db.row_factory = sqlite3.Row

        # Execute project migrations
        for path in [
            "operations/schema.sql",
            "operations/migrations/002_telegram_review.sql",
            "operations/migrations/003_autopilot.sql",
        ]:
            self.db.executescript((review.ROOT / path).read_text())

        # Configs
        (self.root / "config").mkdir(parents=True)
        self.project_config = {
            "publication_enabled": True,
            "production_hold": False,
            "publication_schedules": {
                "isk": {
                    "production_time_wib": "09:00",
                    "publish_time_wib": "12:00",
                    "allowed_publish_window_minutes": 120,
                },
                "dinda": {
                    "production_time_wib": "06:00",
                    "publish_time_wib": "07:00",
                    "allowed_publish_window_minutes": 120,
                },
            },
        }
        (self.root / "config/project.json").write_text(json.dumps(self.project_config))
        self.telegram_config = {
            "allowed_chat_ids": [1001],
            "allowed_user_ids": [2001],
            "bot_id": 9999,
        }
        (self.root / "config/telegram.json").write_text(json.dumps(self.telegram_config))

        # Register characters
        self.db.execute(
            "INSERT INTO characters VALUES (?,?,?)",
            ("isk", "PT Intan Suar Kartika", "@intansuarkartika"),
        )
        self.db.execute(
            "INSERT INTO characters VALUES (?,?,?)",
            ("dinda", "Dinda Kemala", "@dinda.kemala_"),
        )
        self.db.commit()

        # Seed content folder and mock video
        self.media_dir = self.root / "characters/isk/content/sample"
        self.media_dir.mkdir(parents=True)
        self.media_file = self.media_dir / "sample_isk.mp4"
        self.initial_video_bytes = b"\x00\x00\x00\x18ftypmp42" + b"A" * 1024
        self.media_file.write_bytes(self.initial_video_bytes)

        self.approved_caption = (
            "Paku Cap Keris diproduksi langsung dari kawat baja pilihan dengan ketahanan optimal. "
            "Kepala paku rata dan presisi untuk hasil pengerjaan kayu dan konstruksi terbaik."
        )

        # Register version
        self.version_id = review.register(
            self.db,
            self.root,
            "isk",
            "isk_content_001",
            "video",
            self.media_file,
            self.approved_caption,
        )

    def tearDown(self):
        self.db.close()
        self.temp_dir.cleanup()

    def _grant_telegram_approval(self, version_id, chat_id=1001, user_id="2001"):
        delivery_id = uuid.uuid4().hex
        self.db.execute(
            """INSERT INTO review_deliveries 
               (id, version_id, chat_id, state, media_message_id, card_message_id, expires_at, decision, created_at)
               VALUES (?, ?, ?, 'decided', 10, 11, ?, 'approved', ?)""",
            (
                delivery_id,
                version_id,
                chat_id,
                (datetime.now(timezone.utc) + timedelta(days=1)).isoformat(),
                review.now(),
            ),
        )
        approval_id = uuid.uuid4().hex
        self.db.execute(
            """INSERT INTO approvals 
               (id, version_id, decision, reviewer_id, channel, external_event_id, created_at)
               VALUES (?, ?, 'approved', ?, 'telegram', ?, ?)""",
            (
                approval_id,
                version_id,
                user_id,
                f"telegram:9999:{uuid.uuid4().hex[:8]}",
                review.now(),
            ),
        )
        self.db.commit()

    # --- CASE A: Schedule / Time Window Guard ---

    def test_case_a_rejects_publishing_outside_scheduled_window(self):
        """Publisher halts if current time is outside the 12:00 WIB window for ISK."""
        self._grant_telegram_approval(self.version_id)

        # ISK slot: 12:00 WIB. Attempt at 08:30 WIB (like ISK_PK_006 incident)
        wrong_time = datetime(2026, 11, 10, 8, 30, tzinfo=WIB)
        with self.assertRaises(review.ReviewError) as ctx:
            publication.begin(
                self.db,
                self.root,
                self.version_id,
                "@intansuarkartika",
                enforce_schedule=True,
                now_dt=wrong_time,
            )
        self.assertIn("Di luar jendela jadwal publikasi resmi untuk isk", str(ctx.exception))
        self.assertIn("12:00 WIB", str(ctx.exception))

    def test_case_a_rejects_publishing_after_window_expires(self):
        """Publisher halts if current time is past the allowed publish window (e.g. 14:30 WIB)."""
        self._grant_telegram_approval(self.version_id)
        past_window_time = datetime(2026, 11, 10, 14, 30, tzinfo=WIB)
        with self.assertRaises(review.ReviewError) as ctx:
            publication.begin(
                self.db,
                self.root,
                self.version_id,
                "@intansuarkartika",
                enforce_schedule=True,
                now_dt=past_window_time,
            )
        self.assertIn("Di luar jendela jadwal publikasi resmi", str(ctx.exception))

    def test_case_a_allows_publishing_within_scheduled_window(self):
        """Publisher allows submission when within the 12:00–14:00 WIB window."""
        self._grant_telegram_approval(self.version_id)
        valid_time = datetime(2026, 11, 10, 12, 5, tzinfo=WIB)
        result = publication.begin(
            self.db,
            self.root,
            self.version_id,
            "@intansuarkartika",
            enforce_schedule=True,
            now_dt=valid_time,
        )
        self.assertIsNotNone(result.get("publication_id"))
        self.assertEqual(result["account"], "@intansuarkartika")

    # --- CASE B: Missing / Unauthenticated Telegram ACC ---

    def test_case_b_rejects_without_any_approval(self):
        """Publisher halts if version has no approval recorded."""
        valid_time = datetime(2026, 11, 10, 12, 0, tzinfo=WIB)
        with self.assertRaises(review.ReviewError) as ctx:
            publication.begin(
                self.db,
                self.root,
                self.version_id,
                "@intansuarkartika",
                enforce_schedule=True,
                now_dt=valid_time,
            )
        self.assertIn("Paket belum memiliki ACC yang berlaku", str(ctx.exception))

    def test_case_b_rejects_ad_hoc_chat_approval_without_telegram_callback(self):
        """Publisher halts if approval was written from chat without Telegram delivery callback."""
        # Insert ad-hoc approval like legacy scripts did
        self.db.execute(
            """INSERT INTO approvals 
               (id, version_id, decision, reviewer_id, channel, external_event_id, created_at)
               VALUES (?, ?, 'approved', '2001', 'chat_explicit', 'chat:manual_01', ?)""",
            (uuid.uuid4().hex, self.version_id, review.now()),
        )
        self.db.commit()

        valid_time = datetime(2026, 11, 10, 12, 0, tzinfo=WIB)
        with self.assertRaises(review.ReviewError) as ctx:
            publication.begin(
                self.db,
                self.root,
                self.version_id,
                "@intansuarkartika",
                enforce_schedule=True,
                now_dt=valid_time,
            )
        self.assertIn("ACC belum memiliki jejak callback Telegram yang sah", str(ctx.exception))

    def test_case_b_rejects_unauthorized_telegram_reviewer(self):
        """Publisher halts if callback came from unauthorized user or chat."""
        # Grant approval from unapproved chat / user
        self._grant_telegram_approval(self.version_id, chat_id=999999, user_id="888888")
        valid_time = datetime(2026, 11, 10, 12, 0, tzinfo=WIB)
        with self.assertRaises(review.ReviewError) as ctx:
            publication.begin(
                self.db,
                self.root,
                self.version_id,
                "@intansuarkartika",
                enforce_schedule=True,
                now_dt=valid_time,
            )
        self.assertIn("ACC belum memiliki jejak callback Telegram yang sah", str(ctx.exception))

    # --- CASE C: Media File / Hash Alteration ---

    def test_case_c_rejects_tampered_media_bytes(self):
        """Publisher halts if video file on disk is modified after ACC was given."""
        self._grant_telegram_approval(self.version_id)
        # Tamper the file bytes
        self.media_file.write_bytes(self.initial_video_bytes + b"_tampered_data")

        valid_time = datetime(2026, 11, 10, 12, 0, tzinfo=WIB)
        with self.assertRaises(review.ReviewError) as ctx:
            publication.begin(
                self.db,
                self.root,
                self.version_id,
                "@intansuarkartika",
                enforce_schedule=True,
                now_dt=valid_time,
            )
        self.assertIn("Media/caption berubah; buat versi baru dan minta ACC ulang", str(ctx.exception))

    def test_case_c_rejects_deleted_media_file(self):
        """Publisher halts if video file was removed from disk."""
        self._grant_telegram_approval(self.version_id)
        self.media_file.unlink()

        valid_time = datetime(2026, 11, 10, 12, 0, tzinfo=WIB)
        with self.assertRaises(review.ReviewError):
            publication.begin(
                self.db,
                self.root,
                self.version_id,
                "@intansuarkartika",
                enforce_schedule=True,
                now_dt=valid_time,
            )

    # --- CASE D: Caption Exact Match & DraftEditor Assertion ---

    def test_case_d_caption_verification_rejects_truncated_text(self):
        """Caption assertion fails when DraftEditor text is truncated or missing words."""
        truncated_editor_text = (
            "Paku Cap Keris diproduksi langsung dari kawat baja pilihan."
        )
        res = verify_editor_caption(truncated_editor_text, self.approved_caption)
        self.assertFalse(res["ok"])
        self.assertFalse(res["is_exact_match"])

    def test_case_d_caption_verification_rejects_filename_placeholder(self):
        """Caption assertion fails when DraftEditor text contains filename placeholders."""
        bad_placeholder_text = (
            f"final_vlog_morning.mp4 {self.approved_caption}"
        )
        res = verify_editor_caption(bad_placeholder_text, self.approved_caption)
        self.assertFalse(res["ok"])
        self.assertTrue(res["is_bad_placeholder"])

    def test_case_d_caption_verification_passes_exact_match(self):
        """Caption assertion passes when DraftEditor text matches 100% normalized."""
        # Simulated whitespace variation from DraftEditor DOM
        dom_editor_text = f"  {self.approved_caption}\n\n"
        res = verify_editor_caption(dom_editor_text, self.approved_caption)
        self.assertTrue(res["ok"])
        self.assertTrue(res["is_exact_match"])
        self.assertFalse(res["is_bad_placeholder"])

    def test_case_d_mismatch_marks_publication_unknown(self):
        """If caption fails in browser, publication attempt must be marked 'unknown' in SQLite."""
        self._grant_telegram_approval(self.version_id)
        valid_time = datetime(2026, 11, 10, 12, 0, tzinfo=WIB)
        attempt = publication.begin(
            self.db,
            self.root,
            self.version_id,
            "@intansuarkartika",
            enforce_schedule=True,
            now_dt=valid_time,
        )
        pub_id = attempt["publication_id"]

        # Simulate caption mismatch detection in publisher:
        bad_caption = "Teks caption yang salah atau terpotong..."
        verify_res = verify_editor_caption(bad_caption, self.approved_caption)
        if not verify_res["ok"]:
            publication.mark_unknown(self.db, pub_id)

        # Verify database state
        row = self.db.execute("SELECT state FROM publications WHERE id=?", (pub_id,)).fetchone()
        self.assertEqual(row["state"], "unknown")

        # Verify that retrying immediately is BLOCKED until reconciled
        with self.assertRaises(review.ReviewError) as ctx:
            publication.begin(
                self.db,
                self.root,
                self.version_id,
                "@intansuarkartika",
                enforce_schedule=True,
                now_dt=valid_time,
            )
        self.assertIn("Konten sudah diajukan atau statusnya belum pasti", str(ctx.exception))

    def test_case_e_rejects_more_than_one_post_per_day_for_same_character(self):
        """Publisher blocks a second distinct content_id for the same character on the same WIB day."""
        self._grant_telegram_approval(self.version_id)
        valid_time = datetime(2026, 11, 10, 12, 0, tzinfo=WIB)
        first = publication.begin(
            self.db,
            self.root,
            self.version_id,
            "@intansuarkartika",
            enforce_schedule=True,
            now_dt=valid_time,
        )
        publication.confirm(
            self.db,
            first["publication_id"],
            "https://www.tiktok.com/@intansuarkartika/video/7706332486086839999",
        )
        # Ensure confirmed_at matches today's test date in WIB
        self.db.execute(
            "UPDATE publications SET confirmed_at=? WHERE id=?",
            (valid_time.isoformat(), first["publication_id"]),
        )
        self.db.commit()

        second_vid = review.register(
            self.db,
            self.root,
            "isk",
            "isk_pk_second_today",
            "video",
            "characters/isk/content/sample/sample_isk.mp4",
            "Video kedua hari ini tanpa emoji.",
        )
        self._grant_telegram_approval(second_vid)
        with self.assertRaises(review.ReviewError) as ctx:
            publication.begin(
                self.db,
                self.root,
                second_vid,
                "@intansuarkartika",
                enforce_schedule=True,
                now_dt=valid_time + timedelta(minutes=15),
            )
        self.assertIn("Batas maksimal 1 kali posting per hari untuk isk", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
