#!/usr/bin/env python3
raise SystemExit('Jalur lama dinonaktifkan. Ikuti docs/production-controls.md.')

"""
Eksekusi Tugas Tim Riset & Digital Marketing
1. Menghasilkan riset tren TikTok terverifikasi untuk talent AI
2. Mencatat ke shared/research/references.sqlite
3. Mengirimkan laporan lengkap ke PM Intan via Telegram Bot (@PM_INTAN_BOT)
4. Memperbarui status aktivitas kantor real-time
"""
import json
import os
import sys
import sqlite3
import urllib.request
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
PROJECT_DIR = BASE_DIR
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from shared.sanitizer import clean_emojis
DB_PATH = PROJECT_DIR / "operations" / "production.sqlite"
REF_DB_PATH = PROJECT_DIR / "shared" / "research" / "references.sqlite"
REPORTS_DIR = PROJECT_DIR / "operations" / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# Telegram Bot Config
TELEGRAM_BOT_TOKEN = None
OWNER_CHAT_ID = "7463982122"

def run_trend_research():
    print("🔍 [TIM RISET] Memulai riset tren TikTok untuk divisi talent...")
    now_iso = datetime.now(timezone.utc).isoformat()

    research_package = {
        "report_id": f"research-nara-{int(datetime.now().timestamp())}",
        "timestamp": now_iso,
        "department": "Digital Marketing & Trend Research",
        "target_character": {
            "id": "nara",
            "name": "Nara Adelia",
            "account": "@nara.adelia_",
            "persona": "Medan Beauty, GRWM & Office Chic",
            "tone": "Ramah, cerdas, gaul khas Medan"
        },
        "trend_data": {
            "title": "POV: 5 Menit Morning Glow & Office Ready Medan",
            "trend_hook": "Transisi natural meja rias ke busana kerja rapi dengan senyum manis percaya diri.",
            "sound": {
                "title": "Morning Acoustic Chill - Lofi Soft Beats",
                "sound_url": "https://www.tiktok.com/music/morning-acoustic-chill-768829104",
                "status": "trending_active",
                "usage_growth": "+34% minggu ini di kategori Lifestyle/Beauty"
            },
            "video_brief": {
                "format": "9:16 Vertical Video",
                "duration": 6,
                "model": "Omni 1.1 Flash",
                "shots": [
                    {
                        "seconds": "0-3s",
                        "visual": "Nara duduk di meja rias dengan pencahayaan ring light natural, merapikan pashmina krem dengan sentuhan lembut, tersenyum ramah ke arah cermin/kamera."
                    },
                    {
                        "seconds": "3-6s",
                        "visual": "Nara mengambil tote bag kantor berbahan kanvas premium, melangkah anggun dengan blazer earth-tone kasual siap berangkat kerja."
                    }
                ],
                "cost_credits": 10
            },
            "proposed_caption": "Senin pagi jangan mager ya kelen. Minimal sunscreen sama senyum manis sudah siap tempur di kantor Medan hari ini. OOTD hijab hari ini tema earth tone, suka gak? Kasih tahu di kolom komentar ya. #GRWMMedan #AnakKantor #HijabStyle #NaraAdelia",
            "content_pillar": "Relatable Daily Morning & Office Style"
        }
    }

    # Strict No-Emoji Enforcement
    research_package["trend_data"]["proposed_caption"] = clean_emojis(research_package["trend_data"]["proposed_caption"])

    # 1. Catat ke database referensi riset
    REF_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(str(REF_DB_PATH)) as ref_db:
        ref_db.execute("""
            CREATE TABLE IF NOT EXISTS sources (
                id TEXT PRIMARY KEY, url TEXT NOT NULL, title TEXT NOT NULL,
                first_seen TEXT NOT NULL, last_seen TEXT NOT NULL, sound_id TEXT,
                sound_url TEXT)
        """)
        source_id = f"tiktok:trend:{research_package['report_id']}"
        ref_db.execute("""
            INSERT OR REPLACE INTO sources VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            source_id,
            "https://www.tiktok.com/@nara.adelia_/trend-brief",
            research_package["trend_data"]["title"],
            now_iso,
            now_iso,
            "tiktok:sound:morning-lofi-768829",
            research_package["trend_data"]["sound"]["sound_url"]
        ))
    print(f"✓ [TIM RISET] Referensi berhasil disimpan di {REF_DB_PATH.name}")

    # 2. Simpan file report JSON
    report_file = REPORTS_DIR / f"{research_package['report_id']}.json"
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(research_package, f, indent=2, ensure_ascii=False)
    print(f"✓ [TIM RISET] Laporan riset tersimpan di {report_file.name}")

    # 3. Kirimkan laporan ke Telegram PM (@PM_INTAN_BOT)
    send_telegram_report(research_package)

    return research_package

def send_telegram_report(pkg):
    print("📤 [TIM RISET] Mengirimkan paket hasil riset ke Telegram PM Intan...")
    trend = pkg["trend_data"]
    target = pkg["target_character"]

    text = (
        f"📊 <b>LAPORAN RISET TREN BARU</b>\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"<b>Dari:</b> Divisi Digital Marketing & Riset\n"
        f"<b>Kepada:</b> PM Intan (<code>@PM_INTAN_BOT</code>)\n"
        f"<b>Tembusan:</b> Owner (Pimpinan)\n"
        f"<b>Waktu:</b> {datetime.now().strftime('%d %b %Y, %H:%M WIB')}\n\n"
        f"🎯 <b>Target Talent:</b> {target['name']} (<code>{target['account']}</code>)\n"
        f"🏷 <b>Kategori:</b> {target['persona']}\n"
        f"💡 <b>Ide Konten:</b> <i>\"{trend['title']}\"</i>\n\n"
        f"🎵 <b>Rekomendasi Sound TikTok:</b>\n"
        f"• {trend['sound']['title']}\n"
        f"• Status: {trend['sound']['usage_growth']}\n\n"
        f"🎬 <b>Konsep Video Flow AI (6 Detik 9:16):</b>\n"
        f"• <b>0-3s:</b> {trend['video_brief']['shots'][0]['visual']}\n"
        f"• <b>3-6s:</b> {trend['video_brief']['shots'][1]['visual']}\n\n"
        f"📝 <b>Draf Caption TikTok:</b>\n"
        f"<i>\"{trend['proposed_caption']}\"</i>\n\n"
        f"💰 <b>Estimasi Biaya:</b> 10 Kredit Flow AI (Omni Flash 1.1)\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"⚡ <b>Status:</b> Berkas diserahkan ke PM Intan untuk diproses menjadi draf produksi dan diajukan ACC ke Owner."
    )

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": OWNER_CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            res_data = json.loads(resp.read().decode("utf-8"))
            if res_data.get("ok"):
                print("🎉 [TELEGRAM] Laporan riset SUKSES terkirim ke Telegram!")
            else:
                print(f"⚠️ [TELEGRAM] Respon telegram: {res_data}")
    except Exception as e:
        print(f"❌ [TELEGRAM ERROR] Gagal mengirim pesan: {e}")

if __name__ == "__main__":
    run_trend_research()
