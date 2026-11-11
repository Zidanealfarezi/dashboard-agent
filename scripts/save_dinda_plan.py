import json
import sqlite3
from pathlib import Path
from datetime import datetime, timezone
from app import autopilot, review

root = Path(__file__).resolve().parent.parent
db_path = root / 'operations/production.sqlite'

conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row

# Set slot to video 10s
with conn:
    conn.execute("UPDATE daily_slots SET kind = 'video', duration_seconds = 10 WHERE id = 'dinda-2026-11-09'")

# Load draft plan
draft_path = root / 'operations/plans/dinda-2026-11-09-1900-draft.json'
with open(draft_path, 'r', encoding='utf-8') as f:
    draft = json.load(f)

# Load research brief for trend sources
brief_path = root / 'operations/research-briefs/tiktok-trend-dinda-2026-11-09.json'
with open(brief_path, 'r', encoding='utf-8') as f:
    brief = json.load(f)

trend_sources = [
    {
        "url": c["url"],
        "title": c["title"],
        "evidence": c["evidence"],
        "observed_at": c["observed_at"]
    }
    for c in brief["candidates"][:3]
]

plan = {
    "character_id": "dinda",
    "kind": "video",
    "duration_seconds": 10,
    "title": "Gulo Palu dan Jajanan Bingen: Rasa Tempo Dulu Saat Palembang Mulai Hujan",
    "hook": "Jajanan tempo dulu yang rasanya masih akrab saat Palembang hujan",
    "story": "Dinda mampir ke kedai jajanan bingen di Palembang saat sore mulai hujan, mencicipi gulo palu hangat dan mengajak penonton berbagi kenangan jajanan masa kecil.",
    "caption": "Malam di Palembang paling pas kalau ada gulo palu dan bingen hangat. Jajanan tempo dulu yang rasanya masih akrab sampai sekarang. Kamu paling suka camilan malam apa lur? Tulis di komen peh. #palembang #kulinerpalembang #jajanantradisional #malamdipalembang #wongkito",
    "image_prompt": "Use the existing verified Dinda master ingredient with chocolate cardigan. No separate image generation.",
    "role_tags": ["kuliner", "lifestyle"],
    "role_reason": "Eksplorasi kuliner tradisional Palembang sesuai pilar konten Dinda.",
    "shots": [
        {
            "seconds": 10,
            "prompt": draft["shots"][0]["prompt"]
        }
    ],
    "new_biography_facts": [],
    "promotional": False,
    "trend_sources": trend_sources,
    "source_note": "Berdasarkan riset tren TikTok dan BMKG Palembang 9 November 2026."
}

# Run save_plan
autopilot.save_plan(conn, root, 'dinda-2026-11-09', plan)
print("Plan saved successfully!")

# Check slot
row = conn.execute("SELECT * FROM daily_slots WHERE id = 'dinda-2026-11-09'").fetchone()
print(dict(row))
