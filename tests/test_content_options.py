import importlib.util
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

BASE = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("gco", BASE / "scripts/generate_content_options.py")
gco = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gco)

SCHEMA = """
CREATE TABLE trend_memory (id TEXT PRIMARY KEY, character_id TEXT, category TEXT, topic TEXT,
    hook_text TEXT, script_outline TEXT, viral_sound_title TEXT, source_evidence TEXT,
    status TEXT, viral_score REAL, created_at TEXT);
CREATE TABLE trend_selections (id TEXT PRIMARY KEY, day TEXT, character_id TEXT, slot TEXT DEFAULT 'morning', trend_id TEXT,
    title TEXT, viral_score REAL, rationale TEXT, source_urls TEXT, score_breakdown TEXT,
    decided_by TEXT, created_at TEXT);
CREATE TABLE daily_slots (id TEXT PRIMARY KEY, day TEXT, character_id TEXT, kind TEXT,
    duration_seconds INTEGER, state TEXT, plan_json TEXT, profile_sha256 TEXT, job_id TEXT,
    version_id TEXT, delivery_id TEXT, created_at TEXT);
"""


def write_brief(path, sources=2, topic_candidates=None):
    cands = [
        {
            "url": f"https://example.test/source-{i}",
            "title": f"Sumber {i}",
            "evidence": "bukti yang benar-benar terbaca di halaman",
            "verification_status": "source_read",
            "published_at": "2026-11-08T05:00:00+07:00",
        }
        for i in range(sources)
    ]
    data = {"brief_id": "t", "character_id": "dinda", "candidates": cands}
    if topic_candidates is not None:
        data["topic_candidates"] = topic_candidates
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def candidate(code="X", title="Topik uji yang cukup panjang", hook="hook uji topik"):
    return {
        "code": code,
        "title": title,
        "hook": hook,
        "caption": "caption tanpa emoji dan tanpa hashtag nama diri",
        "sources": ["https://example.test/source-0"],
        "factors": {"momentum": 8, "local_relevance": 8, "format_fit": 8,
                    "evidence_strength": 8, "risk_safety": 8},
    }


class BriefTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.dir = Path(self.temp.name)

    def test_weak_evidence_stops_the_script(self):
        brief = write_brief(self.dir / "weak.json", sources=1)
        with self.assertRaises(SystemExit) as ctx:
            gco.load_brief(brief)
        self.assertIn("terlalu lemah", str(ctx.exception))

    def test_brief_without_topic_candidates_falls_back_to_defaults(self):
        # Kandidat bawaan menempel ke URL sumber nyata, jadi uji fallback memakai brief asli
        # tanpa blok topic_candidates.
        real = json.loads((BASE / "operations/research-briefs/tiktok-trend-dinda-2026-11-08.json")
                          .read_text(encoding="utf-8"))
        real.pop("topic_candidates", None)
        path = self.dir / "real_plain.json"
        path.write_text(json.dumps(real), encoding="utf-8")
        data, readable = gco.load_brief(path)
        self.assertGreaterEqual(len(readable), 2)
        built = gco.build_candidates("dinda", data)
        self.assertEqual([c["code"] for c in built], ["A", "B", "C"])

    def test_brief_topic_candidates_override_defaults(self):
        brief = write_brief(self.dir / "fresh.json", sources=2,
                            topic_candidates=[candidate("D"), candidate("E")])
        data, _ = gco.load_brief(brief)
        built = gco.build_candidates("dinda", data)
        self.assertEqual([c["code"] for c in built], ["D", "E"])

    def test_topic_candidate_missing_field_is_rejected(self):
        broken = candidate("D")
        del broken["caption"]
        brief = write_brief(self.dir / "broken.json", sources=2, topic_candidates=[broken])
        data, _ = gco.load_brief(brief)
        with self.assertRaises(SystemExit) as ctx:
            gco.build_candidates("dinda", data)
        self.assertIn("field wajib", str(ctx.exception))


class NoveltyMemoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.db = Path(self.temp.name) / "test.sqlite"
        conn = sqlite3.connect(self.db)
        conn.executescript(SCHEMA)
        conn.execute(
            "INSERT INTO trend_memory (id, character_id, topic, hook_text) VALUES (?,?,?,?)",
            ("opt_a", "dinda", "Mie Celor Pertama di Musim Hujan", "sarapan berkuah"),
        )
        conn.execute(
            "INSERT INTO trend_selections (id, day, character_id, trend_id, title) VALUES (?,?,?,?,?)",
            ("sel_1", "2026-11-07", "dinda", "opt_a", "Mie Celor Pertama di Musim Hujan"),
        )
        conn.commit()
        conn.close()
        patcher = patch.object(gco, "DB_PATH", self.db)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_unproduced_bank_topic_does_not_collapse_novelty(self):
        # Topik ada di bank ide & sudah dipilih, tetapi belum pernah diproduksi.
        self.assertEqual(gco.get_produced_topics("dinda", exclude_day="2026-11-08"), [])
        self.assertEqual(len(gco.get_unproduced_selections("dinda", "2026-11-08")), 1)
        ranked = gco.score_candidates([candidate("A", "Mie Celor Pertama di Musim Hujan")], [])
        # Novelty tinggi (9.0) dikurangi penalti ringan 1.0, bukan kolaps ke 0.
        self.assertGreaterEqual(ranked[0]["score_breakdown"]["novelty"], 7.9)

    def test_produced_topic_is_penalised(self):
        conn = sqlite3.connect(self.db)
        conn.execute(
            "INSERT INTO daily_slots (id, day, character_id, kind, state, version_id) VALUES (?,?,?,?,?,?)",
            ("slot_1", "2026-11-07", "dinda", "video", "review_ready", "ver_1"),
        )
        conn.commit()
        conn.close()
        produced = gco.get_produced_topics("dinda", exclude_day="2026-11-08")
        self.assertEqual(len(produced), 1)
        ranked = gco.score_candidates([candidate("A", "Mie Celor Pertama di Musim Hujan")], produced)
        self.assertLess(ranked[0]["score_breakdown"]["novelty"], 7.0)

    def test_non_dinda_character_pulls_from_trend_memory_not_dinda_defaults(self):
        conn = sqlite3.connect(self.db)
        conn.execute(
            "INSERT INTO trend_memory (id, character_id, category, topic, hook_text, viral_score, status) "
            "VALUES (?,?,?,?,?,?,?)",
            ("bang_ray_tip_x", "bang_ray", "keramik", "Pasang Keramik Anti Kopong",
             "Rakan, cek adukan sebelum tempel keramik!", 9.1, "discovered"),
        )
        conn.commit()
        conn.close()
        brief_path = Path(self.temp.name) / "bang_ray.json"
        write_brief(brief_path, sources=2)
        data, _ = gco.load_brief(brief_path)
        built = gco.build_candidates("bang_ray", data)
        self.assertEqual(len(built), 1)
        self.assertEqual(built[0]["existing_trend_id"], "bang_ray_tip_x")
        self.assertIn("Keramik", built[0]["title"])
        self.assertNotIn("Cardigan", built[0]["outfit"])


if __name__ == "__main__":
    unittest.main()
