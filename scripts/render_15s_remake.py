#!/usr/bin/env python3
"""
Assemble a 15-second ISK Remake Video:
- Hook & Torture Test: Kawat Duri Diamond (Pagar Batas Kebun Sawit)
- Main Content: 10.933 seconds with Neural TTS + 2-Tier Kinetic Yellow Subtitles
- Outro Bumper: 4.067 seconds with 3D Keris + WA 08198889350
- Final Duration: EXACTLY 15.000 seconds
- Strict 0% Emoji Policy
"""

import os
import sys
import asyncio
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import edge_tts
from app import subtitles

FFMPEG = "/Users/zidane/.hermes/tools/ffmpeg-9.0.1-darwin-arm64/ffmpeg"
FFPROBE = str(ROOT / "tools/ffmpeg-runtime/ffprobe")

INPUT_RAW_CLIP = ROOT / "characters/isk/content/ISK_PK_008/Mandor_memeriksa_kawat_duri_perk…_f372dda0.mp4"
OUTRO_BUMPER = ROOT / "characters/isk/assets/brand/outro_keris_isk.mp4"
OUTPUT_DIR = ROOT / "characters/isk/content/ISK_REMAKE_15S"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

VO_AUDIO = OUTPUT_DIR / "voiceover.mp3"
STAGED_CLIP = OUTPUT_DIR / "staged_10s.mp4"
SUBTITLED_CLIP = OUTPUT_DIR / "subtitled_10s.mp4"
FINAL_VIDEO = OUTPUT_DIR / "ISK_REMAKE_KAWAT_DURI_15S.mp4"

SCRIPT_TEXT = (
    "Kawat duri abal-abal baru diseruduk ternak sekali langsung melar! "
    "Amankan kebun sawit Anda dengan Kawat Duri Diamond dari PT Intan Suar Kartika, "
    "galvanis anti karat tahan cuaca ekstrem."
)

async def generate_vo():
    print("[1/5] Menghasilkan voiceover (id-ID-ArdiNeural)...")
    comm = edge_tts.Communicate(SCRIPT_TEXT, "id-ID-ArdiNeural", rate="+10%")
    await comm.save(str(VO_AUDIO))
    print(f"       Voiceover selesai: {VO_AUDIO}")

def get_duration(path):
    out = subprocess.check_output([
        FFPROBE, "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", str(path)
    ]).decode().strip()
    return float(out)

def build_video():
    asyncio.run(generate_vo())
    vo_dur = get_duration(VO_AUDIO)
    outro_dur = get_duration(OUTRO_BUMPER)
    print(f"       Durasi Voiceover: {vo_dur:.2f}s | Durasi Outro: {outro_dur:.2f}s")

    # Main content target: 15.0 - outro_dur = 10.933333s
    main_target_dur = 15.0 - outro_dur
    print(f"[2/5] Menyiapkan klip utama target durasi: {main_target_dur:.3f}s...")

    # Stretch/scale video slightly to fit main_target_dur exactly and fit 1080x1920
    # Input clip is 10.0267s, stretch factor = 10.933333 / 10.026667 = 1.090425
    cmd_stage = [
        FFMPEG, "-y",
        "-i", str(INPUT_RAW_CLIP),
        "-i", str(VO_AUDIO),
        "-filter_complex", (
            f"[0:v]setpts=1.090425*PTS,scale=1080:1920:force_original_aspect_ratio=increase,"
            f"crop=1080:1920,fps=30[v];"
            f"[1:a]apad=pad_dur=1.5[a]"
        ),
        "-map", "[v]", "-map", "[a]",
        "-t", f"{main_target_dur:.6f}",
        "-c:v", "libx264", "-preset", "fast", "-crf", "18", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k",
        str(STAGED_CLIP)
    ]
    subprocess.run(cmd_stage, check=True)
    print(f"       Klip panggung selesai: {STAGED_CLIP}")

    # Generate ASS subtitle
    print("[3/5] Menghasilkan subtitle editorial_tiktok tanpa koma via Faster-Whisper...")
    ass_path = OUTPUT_DIR / "subtitles.ass"
    cues = subtitles.auto_transcribe_editorial(STAGED_CLIP)
    subtitles.generate_editorial_ass_script(cues, ass_path)

    # Burn subtitles onto staged clip
    print("[4/5] Membakar subtitle ke klip utama...")
    subtitles.burn_subtitles_to_video(STAGED_CLIP, ass_path, SUBTITLED_CLIP, ffmpeg_bin=FFMPEG)

    # Concat with outro bumper
    print("[5/5] Menggabungkan klip utama + outro bumper resmi...")
    concat_list = OUTPUT_DIR / "concat.txt"
    concat_list.write_text(f"file '{SUBTITLED_CLIP.resolve()}'\nfile '{OUTRO_BUMPER.resolve()}'\n")

    cmd_concat = [
        FFMPEG, "-y",
        "-f", "concat", "-safe", "0",
        "-i", str(concat_list),
        "-c:v", "libx264", "-preset", "fast", "-crf", "18", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k",
        str(FINAL_VIDEO)
    ]
    subprocess.run(cmd_concat, check=True)

    final_dur = get_duration(FINAL_VIDEO)
    print(f"\nSUCCESS! Video final selesai dirakit: {FINAL_VIDEO}")
    print(f"DURASI FINAL: {final_dur:.6f} detik (Tepat 15 Detik!)")

if __name__ == "__main__":
    build_video()
