#!/usr/bin/env python3
"""Historical ISK Automated Modular Video Assembler Pipeline.
Reads structured brief JSON, generates voiceover via Neural TTS,
assembles 9:16 scenes with text overlays and static outro bumper,
and registers the completed package into SQLite production database.

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
import uuid

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

FFMPEG = "/Users/zidane/.hermes/tools/ffmpeg-9.0.1-darwin-arm64/ffmpeg"
SQLITE_DB = ROOT / "operations" / "production.sqlite"


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


async def generate_voiceover(scenes, output_path):
    import edge_tts
    script_lines = []
    for s in scenes:
        script_lines.append(s["voiceover_text"].strip())
    full_text = " ".join(script_lines)

    print(f"[ISK Pipeline] Menghasilkan voiceover AI (id-ID-ArdiNeural)...")
    comm = edge_tts.Communicate(full_text, "id-ID-ArdiNeural", rate="+6%")
    await comm.save(str(output_path))
    print(f"[ISK Pipeline] Voiceover tersimpan: {output_path}")


def create_scene_clip(scene, out_path, font_scale=54):
    """Generate a clean 9:16 background clip with text overlay for a scene."""
    duration = scene["duration_sec"]
    overlay_text = scene["overlay_text"].replace("'", "\\'").replace(":", "\\:")
    
    # Industrial color gradients matching PT Intan Suar Kartika
    colors = {
        1: "0x1A1E29", # Dark Charcoal
        2: "0x202B3C", # Deep Steel Navy
        3: "0x1C2D2B", # Industrial Forest Slate
        4: "0x2A201A", # Warm Brick Charcoal
    }
    bg_color = colors.get(scene["scene_number"], "0x1A1E29")

    cmd = [
        FFMPEG, "-y",
        "-f", "lavfi", "-i", f"color=c={bg_color}:s=1080x1920:d={duration}", "-r", "30",
        "-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=44100",
        "-vf", (
            f"drawtext=text='PT INTAN SUAR KARTIKA':fontcolor=0xA0AEC0:fontsize=38:x=(w-text_w)/2:y=240,"
            f"drawtext=text='{overlay_text}':fontcolor=0xF7FAFC:fontsize={font_scale}:x=(w-text_w)/2:y=880,"
            f"drawtext=text='PAKU CAP KERIS - MUTU EKSPOR':fontcolor=0xE5A93C:fontsize=34:x=(w-text_w)/2:y=980"
        ),
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-t", str(duration),
        str(out_path)
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)


def assemble_full_video(scene_clips, outro_clip, voiceover_path, output_path):
    print(f"[ISK Pipeline] Menggabungkan {len(scene_clips)} adegan + outro bumper resmi...")
    inputs = []
    filter_inputs = ""
    for i, clip in enumerate(scene_clips):
        inputs.extend(["-i", str(clip.resolve())])
        filter_inputs += f"[{i}:v]"
    
    outro_idx = len(scene_clips)
    inputs.extend(["-i", str(outro_clip.resolve())])
    filter_inputs += f"[{outro_idx}:v]"
    
    vo_idx = outro_idx + 1
    inputs.extend(["-i", str(voiceover_path.resolve())])
    
    total_scenes = len(scene_clips) + 1
    filter_complex = f"{filter_inputs}concat=n={total_scenes}:v=1:a=0[v];[{vo_idx}:a]apad[a]"
    
    cmd = [
        FFMPEG, "-y",
        *inputs,
        "-filter_complex", filter_complex,
        "-map", "[v]", "-map", "[a]",
        "-c:v", "libx264", "-preset", "fast", "-crf", "19", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k",
        "-t", "20.06",
        str(output_path)
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    print(f"[ISK Pipeline] Video final selesai dibuat: {output_path}")


def register_to_database(brief, video_path):
    video_id = brief["video_id"]
    content_id = f"isk_{video_id.lower()}"
    caption = brief["caption"]
    media_rel = str(video_path.relative_to(ROOT))
    media_hash = sha256_file(video_path)
    caption_hash = hashlib.sha256(caption.encode("utf-8")).hexdigest()
    now_iso = subprocess.check_output(["date", "-u", "+%Y-%m-%dT%H:%M:%SZ"]).decode().strip()

    conn = sqlite3.connect(str(SQLITE_DB))
    c = conn.cursor()
    c.execute("PRAGMA foreign_keys = ON;")

    # 1. Content table
    c.execute("INSERT OR REPLACE INTO content (id, character_id, kind, created_at) VALUES (?, ?, ?, ?)",
              (content_id, "isk", "video", now_iso))

    # 2. Versions table - dynamically calculate next immutable revision
    c.execute("SELECT COALESCE(MAX(revision), 0) + 1 FROM versions WHERE content_id = ?", (content_id,))
    next_rev = c.fetchone()[0]

    version_id = f"ver_{content_id}_rev{next_rev}_{int(Path(video_path).stat().st_mtime)}"
    c.execute("""
        INSERT INTO versions 
        (id, content_id, revision, media_path, media_sha256, caption, caption_sha256, destination_account, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, '@intansuarkartika', ?)
    """, (version_id, content_id, next_rev, media_rel, media_hash, caption, caption_hash, now_iso))

    conn.commit()
    conn.close()

    print(f"[ISK Pipeline] Berhasil didaftarkan ke SQLite:")
    print(f"  Content ID: {content_id}")
    print(f"  Version ID: {version_id}")
    print(f"  Media Hash: {media_hash[:16]}...")
    print(f"  Target Akun: @intansuarkartika")
    return version_id


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--brief", type=Path, default=ROOT / "characters/isk/briefs/ISK_PK_001.json",
                        help="Path ke file brief JSON")
    args = parser.parse_args()

    if not args.brief.exists():
        sys.exit(f"Brief file tidak ditemukan: {args.brief}")

    with open(args.brief, "r", encoding="utf-8") as f:
        brief = json.load(f)

    video_id = brief["video_id"]
    work_dir = ROOT / "characters" / "isk" / "content" / video_id
    work_dir.mkdir(parents=True, exist_ok=True)

    # 1. Voiceover
    vo_path = work_dir / "voiceover.mp3"
    asyncio.run(generate_voiceover(brief["scenes"], vo_path))

    # 2. Scenes
    scene_clips = []
    for sc in brief["scenes"]:
        sc_num = sc["scene_number"]
        clip_path = work_dir / f"scene_{sc_num}.mp4"
        print(f"[ISK Pipeline] Merender adegan {sc_num}: {sc['overlay_text']} ({sc['duration_sec']}s)...")
        create_scene_clip(sc, clip_path)
        scene_clips.append(clip_path)

    # 3. Outro Bumper
    outro_path = ROOT / "characters" / "isk" / brief["outro"]["static_asset_path"]
    if not outro_path.exists():
        sys.exit(f"Outro bumper tidak ditemukan di: {outro_path}")

    # 4. Assemble
    final_video_path = work_dir / f"{video_id}_final_18s.mp4"
    assemble_full_video(scene_clips, outro_path, vo_path, final_video_path)

    # 5. Database Register
    version_id = register_to_database(brief, final_video_path)
    print(f"\n[ISK Pipeline] SUKSES: Video siap untuk proses ACC Owner!")
    print(f"File output: {final_video_path}")


if __name__ == "__main__":
    raise SystemExit("Arsip. Pakai app.autopilot dan app.media sesuai panduan ISK.")
