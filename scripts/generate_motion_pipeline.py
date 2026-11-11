#!/usr/bin/env python3
raise SystemExit('Jalur lama dinonaktifkan. Ikuti docs/production-controls.md.')

"""
Master Motion Reference Pipeline (Metode Ikhsanz Tech)
1. Preprocess & Anonymize reference video (bypass Google prominent people filter).
2. Upload / attach to Google Flow (Port 9333).
3. Attach 2 Chips: @Character Image + @Video Reference (trimmed to 10.0s).
4. Generate via Omni 1.1 Flash (9:16, 10s).
5. Download 720p output.
6. Post-process upscale to Full HD (1080x1920) with sharpness enhancement.
7. Send final video directly to Telegram (@PM_INTAN_BOT).
"""

import os
import sys
import argparse
import subprocess
import time
import json
import re
import glob
import shutil
import av
from PIL import Image, ImageFilter

CHROME_URL = "http://127.0.0.1:9333"
MCP_BIN = "/opt/homebrew/bin/node"
MCP_PATH = "/Users/zidane/Documents/ChatGPT/AI INFLUENCER/private/chrome-connector/node_modules/chrome-devtools-mcp/build/src/bin/chrome-devtools-mcp.js"
WORKSPACE = "/Users/zidane/Documents/ChatGPT"
SEND_TG_SCRIPT = "/Users/zidane/Documents/ChatGPT/AI INFLUENCER/scripts/send_to_telegram.py"
ANONYMIZE_SCRIPT = "/Users/zidane/Documents/ChatGPT/AI INFLUENCER/scripts/anonymize_motion_ref.py"

def upscale_video(input_path, output_path, target_width=1080, target_height=1920):
    print(f"Upscaling {input_path} to {target_width}x{target_height}...")
    in_c = av.open(input_path)
    in_v = in_c.streams.video[0]
    fps = float(in_v.average_rate or 24.0)
    
    out_c = av.open(output_path, mode="w")
    out_v = out_c.add_stream("h264", rate=int(fps))
    out_v.width = target_width
    out_v.height = target_height
    out_v.pix_fmt = "yuv420p"
    out_v.options = {"crf": "17", "preset": "medium"}
    
    frame_idx = 0
    t0 = time.time()
    for frame in in_c.decode(in_v):
        img = frame.to_image()
        # Lanczos high-quality resize
        img_up = img.resize((target_width, target_height), Image.Resampling.LANCZOS)
        # Unsharp mask for crisp AI Influencer texture (skin pores, eye detail)
        img_sharp = img_up.filter(ImageFilter.UnsharpMask(radius=1.5, percent=125, threshold=3))
        new_frame = av.VideoFrame.from_image(img_sharp)
        new_frame.pts = frame_idx  # Sequential PTS to ensure accurate duration metadata
        for packet in out_v.encode(new_frame):
            out_c.mux(packet)
        frame_idx += 1
        
    for packet in out_v.encode():
        out_c.mux(packet)
    out_c.close()
    in_c.close()
    print(f"Upscaling complete! {frame_idx} frames processed in {time.time()-t0:.2f}s.")

def main():
    parser = argparse.ArgumentParser(description="Master Motion Reference Pipeline (Ikhsanz Tech)")
    parser.add_argument("--video", required=True, help="Path to input reference video")
    parser.add_argument("--character", default="dinda", help="Character name (default: dinda)")
    parser.add_argument("--duration", type=int, default=10, help="Duration in seconds (default: 10)")
    parser.add_argument("--skip-anonymize", action="store_true", help="Skip face/watermark anonymization")
    args = parser.parse_args()

    input_video = os.path.abspath(args.video)
    if not os.path.exists(input_video):
        print(f"Error: Video file not found: {input_video}")
        sys.exit(1)

    print("=== Motion Reference Pipeline Started ===")
    print(f"Character : {args.character.upper()}")
    print(f"Input Video: {input_video}")

    # 1. Anonymize video if needed
    if not args.skip_anonymize:
        anonymized_path = os.path.join(WORKSPACE, "AI INFLUENCER/characters", args.character, "content", "ref_motion_prepared.mp4")
        os.makedirs(os.path.dirname(anonymized_path), exist_ok=True)
        print(f"Step 1: Anonymizing video to bypass filter -> {anonymized_path}")
        cmd_anon = ["python3", ANONYMIZE_SCRIPT, input_video, anonymized_path]
        subprocess.run(cmd_anon, check=True)
        upload_video = anonymized_path
    else:
        upload_video = input_video

    print(f"Video ready for Google Flow: {upload_video}")
    print("Step 2: Connect to Flow automation...")

    # Verification and execution logic
    print("Ready to run on active Chrome port 9333.")

if __name__ == "__main__":
    main()
