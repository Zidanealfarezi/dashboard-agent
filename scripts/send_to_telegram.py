#!/usr/bin/env python3
raise SystemExit('Jalur lama dinonaktifkan. Ikuti docs/production-controls.md.')

"""
Utility pengiriman langsung aset/laporan ke Telegram Owner (@PM_INTAN_BOT).
Strict: No emoji on captions, direct one-shot HTTP call without daemon.
"""
import argparse
import json
import mimetypes
import sys
import urllib.request
import uuid
from pathlib import Path

TOKEN = None
CHAT_ID = "7463982122"

def send_file(method, file_param, file_path, caption=""):
    boundary = uuid.uuid4().hex
    headers = {"Content-Type": f"multipart/form-data; boundary={boundary}"}
    body = bytearray()
    
    body.extend(f'--{boundary}\r\nContent-Disposition: form-data; name="chat_id"\r\n\r\n{CHAT_ID}\r\n'.encode())
    if caption:
        body.extend(f'--{boundary}\r\nContent-Disposition: form-data; name="caption"\r\n\r\n{caption}\r\n'.encode())
        
    path = Path(file_path)
    mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    body.extend(f'--{boundary}\r\nContent-Disposition: form-data; name="{file_param}"; filename="{path.name}"\r\nContent-Type: {mime}\r\n\r\n'.encode())
    with open(path, "rb") as f:
        body.extend(f.read())
    body.extend(b"\r\n")
    body.extend(f"--{boundary}--\r\n".encode())
    
    req = urllib.request.Request(f"https://api.telegram.org/bot{TOKEN}/{method}", data=bytes(body), headers=headers)
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())

def send_text(text):
    payload = json.dumps({"chat_id": CHAT_ID, "text": text}).encode()
    headers = {"Content-Type": "application/json"}
    req = urllib.request.Request(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data=payload, headers=headers)
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Kirim file/pesan ke Telegram")
    parser.add_argument("--file", help="Path file media")
    parser.add_argument("--type", choices=["photo", "video", "document"], default="document")
    parser.add_argument("--caption", default="")
    parser.add_argument("--text", help="Pesan teks langsung")
    args = parser.parse_args()

    if args.text:
        res = send_text(args.text)
        print("Teks terkirim:", res.get("ok"))
    elif args.file:
        method = "sendPhoto" if args.type == "photo" else "sendVideo" if args.type == "video" else "sendDocument"
        param = "photo" if args.type == "photo" else "video" if args.type == "video" else "document"
        res = send_file(method, param, args.file, args.caption)
        print("File terkirim:", res.get("ok"))
