#!/usr/bin/env python3
"""Historical ISK & Soft-Selling Paku Cap Keris Video Generator.
Implements the 2-clip x 10-second formula:
- Clip 1 (10s): 0-3s Hook, 3-5s Reaction, 5-9s Main Action, 9-10s Hold
- Clip 2 (10s): Starts from clean final frame of Clip 1
- Official Outro Bumper (4.06s): Brand bumper with wa.me/62819889350
- Neural TTS Voiceover tailored by character (Ardi / Gadis)
- SQLite package registration & Telegram review delivery

Strict 0% Emoji Policy.
"""
import argparse
import asyncio
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

FFMPEG = "/Users/zidane/.hermes/tools/ffmpeg-9.0.1-darwin-arm64/ffmpeg"
SQLITE_DB = ROOT / "operations" / "production.sqlite"
TEMPLATES_JSON = ROOT / "characters" / "isk" / "templates" / "prompt_rules_and_variations.json"
OUTRO_BUMPER = ROOT / "characters" / "isk" / "assets" / "brand" / "outro_keris_isk.mp4"


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


async def synthesize_voiceover(text, voice_name, output_path, rate="+4%"):
    import edge_tts
    print(f"[ISK Generator] Sintesis suara AI ({voice_name})...")
    comm = edge_tts.Communicate(text, voice_name, rate=rate)
    await comm.save(str(output_path))
    print(f"[ISK Generator] Voiceover tersimpan: {output_path}")


def render_scene_card(text_hook, text_subtitle, duration_sec, bg_color, out_path, font_size=52):
    """Render a clean 9:16 background card with high-contrast text overlay."""
    safe_hook = text_hook.replace("'", "\\'").replace(":", "\\:")
    safe_sub = text_subtitle.replace("'", "\\'").replace(":", "\\:")
    
    cmd = [
        FFMPEG, "-y",
        "-f", "lavfi", "-i", f"color=c={bg_color}:s=1080x1920:d={duration_sec}", "-r", "30",
        "-vf", (
            f"drawtext=text='PT INTAN SUAR KARTIKA':fontcolor=0xA0AEC0:fontsize=36:x=(w-text_w)/2:y=240,"
            f"drawtext=text='{safe_hook}':fontcolor=0xF7FAFC:fontsize={font_size}:x=(w-text_w)/2:y=860,"
            f"drawtext=text='{safe_sub}':fontcolor=0xE5A93C:fontsize=32:x=(w-text_w)/2:y=960"
        ),
        "-c:v", "libx264", "-preset", "fast", "-crf", "19", "-pix_fmt", "yuv420p",
        "-t", str(duration_sec),
        str(out_path)
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)


def assemble_package(clip_1_path, clip_2_path, outro_path, vo_path, output_path):
    print(f"[ISK Generator] Menggabungkan Klip 1 (10s) + Klip 2 (10s) + Outro Resmi (4.06s)...")
    cmd = [
        FFMPEG, "-y",
        "-i", str(clip_1_path),
        "-i", str(clip_2_path),
        "-i", str(outro_path),
        "-i", str(vo_path),
        "-filter_complex", "[0:v][1:v][2:v]concat=n=3:v=1:a=0[v];[3:a]apad[a]",
        "-map", "[v]", "-map", "[a]",
        "-c:v", "libx264", "-preset", "fast", "-crf", "19", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k",
        "-t", "24.06",
        str(output_path)
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    print(f"[ISK Generator] Video selesai dirakit: {output_path}")


def register_version_and_send_review(character_id, content_id, video_path, caption, destination_account, chat_id=7463982122):
    media_rel = str(video_path.relative_to(ROOT))
    media_hash = sha256_file(video_path)
    caption_hash = hashlib.sha256(caption.encode("utf-8")).hexdigest()
    now_iso = subprocess.check_output(["date", "-u", "+%Y-%m-%dT%H:%M:%SZ"]).decode().strip()

    conn = sqlite3.connect(str(SQLITE_DB))
    c = conn.cursor()
    c.execute("PRAGMA foreign_keys = ON;")

    # 1. Content table
    c.execute("INSERT OR REPLACE INTO content (id, character_id, kind, created_at) VALUES (?, ?, ?, ?)",
              (content_id, character_id, "video", now_iso))

    # 2. Versions table - calculate next revision
    c.execute("SELECT COALESCE(MAX(revision), 0) + 1 FROM versions WHERE content_id = ?", (content_id,))
    next_rev = c.fetchone()[0]

    version_id = f"ver_{content_id}_rev{next_rev}_{int(Path(video_path).stat().st_mtime)}"
    c.execute("""
        INSERT INTO versions 
        (id, content_id, revision, media_path, media_sha256, caption, caption_sha256, destination_account, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (version_id, content_id, next_rev, media_rel, media_hash, caption, caption_hash, destination_account, now_iso))

    conn.commit()
    conn.close()

    print(f"[ISK Generator] Terdaftar di SQLite:")
    print(f"  Version ID: {version_id}")
    print(f"  Akun Tujuan: {destination_account}")

    # 3. Prepare & Send via app/review.py
    try:
        prep_cmd = ["python3", str(ROOT / "app" / "review.py"), "prepare", "--version", version_id]
        delivery_id = subprocess.check_output(prep_cmd, cwd=str(ROOT)).decode().strip()
        print(f"[ISK Generator] Review delivery siap: {delivery_id}")

        send_cmd = ["python3", str(ROOT / "app" / "review.py"), "send", "--review", delivery_id]
        send_out = subprocess.check_output(send_cmd, cwd=str(ROOT)).decode().strip()
        print(f"[ISK Generator] Pengiriman Telegram: {send_out}")
    except Exception as e:
        print(f"[ISK Generator] Peringatan: Pengiriman Telegram tertahan ({e})")

    return version_id


def generate_variant(variant_key):
    with open(TEMPLATES_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)

    variant = None
    char_id = "isk"
    dest_account = "@intansuarkartika"
    voice = "id-ID-ArdiNeural"

    # Search in track A
    for item in data["content_tracks"]["track_a_official_isk"]:
        if item["id"] == variant_key or variant_key == "isk_official":
            variant = item
            char_id = "isk"
            dest_account = "@intansuarkartika"
            voice = "id-ID-ArdiNeural"
            break

    # Search in track B
    if not variant:
        for item in data["content_tracks"]["track_b_soft_selling_influencers"]:
            if item["id"] == variant_key:
                variant = item
                if "RANIA" in variant_key:
                    char_id = "rania"
                    dest_account = "@rania.meutia"
                    voice = "id-ID-GadisNeural"
                elif "DINDA" in variant_key:
                    char_id = "dinda"
                    dest_account = "@dinda.kemala_"
                    voice = "id-ID-GadisNeural"
                elif "NARA" in variant_key:
                    char_id = "nara"
                    dest_account = "@nara.adelia_"
                    voice = "id-ID-GadisNeural"
                break

    if not variant:
        raise ValueError(f"Varian konten tidak ditemukan: {variant_key}")

    print(f"\n========================================================")
    print(f"[ISK Generator] Menjalankan Varian: {variant['title']}")
    print(f"  Karakter: {char_id} | Akun: {dest_account}")
    print(f"========================================================")

    work_dir = ROOT / "characters" / char_id / "content" / variant["id"]
    work_dir.mkdir(parents=True, exist_ok=True)

    # 1. Voiceover
    vo_text = f"{variant['clip_1']['dialogue']} {variant['clip_2']['dialogue']}"
    vo_path = work_dir / "voiceover.mp3"
    asyncio.run(synthesize_voiceover(vo_text, voice, vo_path))

    # 2. Clips
    clip_1_path = work_dir / "clip_1_10s.mp4"
    clip_2_path = work_dir / "clip_2_10s.mp4"

    render_scene_card(
        text_hook=variant['clip_1']['dialogue'][:45] + "...",
        text_subtitle="PAKU CAP KERIS - 0-3s HOOK & AKSI",
        duration_sec=10,
        bg_color="0x1E2430",
        out_path=clip_1_path
    )

    render_scene_card(
        text_hook=variant['clip_2']['dialogue'][:45] + "...",
        text_subtitle="KOKOH & TIMBANGAN PAS 25 KG",
        duration_sec=10,
        bg_color="0x263328",
        out_path=clip_2_path
    )

    # 3. Assemble
    final_video = work_dir / f"{variant['id']}_final_24s.mp4"
    assemble_package(clip_1_path, clip_2_path, OUTRO_BUMPER, vo_path, final_video)

    # 4. Caption & Register
    caption = f"{variant['title']}. Pekerjaan rapi dan konstruksi kokoh selalu berawal dari paku bermutu ekspor. Paku Cap Keris dari PT Intan Suar Kartika, timbangan pas 25 kg dan batang kokoh anti bengkok. Hubungi WhatsApp wa.me/62819889350 untuk pasokan proyek atau toko bangunan Anda."
    content_id = f"{char_id}_{variant['id'].lower()}"
    version_id = register_version_and_send_review(char_id, content_id, final_video, caption, dest_account)

    print(f"\n[ISK Generator] SUKSES: Paket {variant['id']} telah masuk sistem!")
    return version_id


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--variant", default="ISK_OFFICIAL_001",
                        choices=["ISK_OFFICIAL_001", "RANIA_SOFT_001", "DINDA_SOFT_001", "NARA_SOFT_001"],
                        help="ID varian konten yang akan dihasilkan")
    args = parser.parse_args()
    generate_variant(args.variant)


if __name__ == "__main__":
    raise SystemExit("Arsip. Pakai app.autopilot dan app.media sesuai panduan ISK.")
