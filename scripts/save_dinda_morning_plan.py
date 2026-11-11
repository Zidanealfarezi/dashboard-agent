import json
import sqlite3
from pathlib import Path
from datetime import datetime, timezone
from app import autopilot, review

root = Path('/Users/zidane/Documents/ChatGPT/AI INFLUENCER')
db_path = root / 'operations/production.sqlite'

conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row

# Ensure slot is video 10s
with conn:
    conn.execute("UPDATE daily_slots SET kind = 'video', duration_seconds = 10 WHERE id = 'dinda-2026-11-10'")

# Load research brief for trend sources
brief_path = root / 'operations/research-briefs/tiktok-trend-dinda-2026-11-10.json'
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

prompt = (
    "shot on smartphone vlog camera, natural clean daylight neutral white balance at 5500K, "
    "true-to-life colors, realistic matte human skin with visible fine pores, no plastic shine, "
    "no waxy skin, no glass skin, no yellow or orange tint, no artificial golden glow, zero CGI, "
    "authentic non-AI documentary look. Dinda Kemala, Indonesian woman in her twenties wearing a "
    "sage green crinkle linen blouse and cream culottes with a neat cream pashmina hijab, stands "
    "in the open courtyard near Museum Sultan Mahmud Badaruddin II Palembang in the soft morning daylight. "
    "She smiles warmly at the camera, speaks naturally to the lens about the upcoming traditional game event, "
    "gesturing gently with her hand. Handheld vertical 9:16 framing, subject centered, stable face, "
    "natural micro-expressions, honest morning street-vlog atmosphere, no text overlay, no camera information bar, no fps or color-temperature readout, no location label, no timestamps, no watermarks, no logo."
)

plan = {
    "character_id": "dinda",
    "kind": "video",
    "duration_seconds": 10,
    "title": "Besok Mainan Tradisional Palembang Ramai di Museum SMB II, Jajanannya 50 UMKM",
    "hook": "Besok Museum SMB II ramai lagi karena ada permainan tradisional bingen dan puluhan tenant UMKM jajanan Palembang.",
    "story": "Dinda mampir ke pelataran Museum Sultan Mahmud Badaruddin II pada pagi hari yang sejuk, menceritakan persiapan event Pesona Budaya Sehat besok dan mengajak warga Palembang bernostalgia dengan mainan tradisional bingen serta berburu aneka jajanan UMKM.",
    "caption": "Besok Museum Sultan Mahmud Badaruddin II mulai diramaikan event Pesona Budaya Sehat. Ada permainan tradisional bingen yang dulu sering kita mainkan waktu kecil, health check, museum tour, dan yang paling bikin aku tertarik tentu puluhan tenant UMKM jajanan khas kota ini. Rencananya besok pagi aku ke sana, sekalian jajan dan lihat permainannya. Kalau ke museum, kalian langsung ke koleksi atau jajan dulu? #palembang #museumsmb2 #jajananbingen #kulinerpalembang #eventpalembang #dailyvlog",
    "image_prompt": "Use existing verified Dinda master ingredient with sage green blouse. No separate image generation.",
    "role_tags": ["kuliner", "lifestyle"],
    "role_reason": "Eksplorasi budaya lokal dan kuliner UMKM Palembang sesuai pilar konten Dinda.",
    "shots": [
        {
            "seconds": 10,
            "prompt": prompt
        }
    ],
    "new_biography_facts": [],
    "promotional": False,
    "trend_sources": trend_sources,
    "source_note": "Berdasarkan riset tren TikTok, BMKG Palembang, dan ExtraNews 10 November 2026."
}

# Run save_plan
autopilot.save_plan(conn, root, 'dinda-2026-11-10', plan)
print("Plan saved successfully!")

# Check slot
row = conn.execute("SELECT id, state, duration_seconds FROM daily_slots WHERE id = 'dinda-2026-11-10'").fetchone()
print(dict(row))
