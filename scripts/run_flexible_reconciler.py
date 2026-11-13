#!/usr/bin/env python3
"""
scripts/run_flexible_reconciler.py
Daemon pemantau dan reconciler toleransi waktu fleksibel (Option A)
Memeriksa status slot setiap 3 menit:
- Menjalankan silent auto-recovery (CDP auto-open tab + balance sync) pada percobaan 1
- Mengirim alert kritis ke Telegram Owner pada percobaan 2 jika tertahan karena butuh manusia
- Menandai slot sebagai skipped jika telah melewati batas toleransi H-1 jam sebelum tayang.
"""

import argparse
import json
import os
import sqlite3
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app import flexible_reconciler


def run_once(db_path: Path):
    if not db_path.exists():
        print(f"[flexible_reconciler] DB not found at {db_path}", file=sys.stderr)
        return {"ok": False, "error": "db_not_found"}

    db = sqlite3.connect(str(db_path), timeout=10)
    try:
        result = flexible_reconciler.evaluate_and_reconcile(db, ROOT)
        return result
    finally:
        db.close()


def check_status(pid_file: Path):
    if pid_file.exists():
        try:
            pid = int(pid_file.read_text().strip())
            os.kill(pid, 0)
            print(f"[flexible_reconciler] SEDANG BERJALAN di PID {pid}")
            return True
        except (ValueError, OSError):
            pid_file.unlink(missing_ok=True)
    print("[flexible_reconciler] TIDAK AKTIF (Stopped)")
    return False


def stop_daemon(pid_file: Path):
    if pid_file.exists():
        try:
            pid = int(pid_file.read_text().strip())
            os.kill(pid, 15)
            time.sleep(0.5)
            print(f"[flexible_reconciler] Berhasil dihentikan (PID {pid})")
        except (ValueError, OSError):
            pass
        pid_file.unlink(missing_ok=True)
    else:
        print("[flexible_reconciler] Tidak ada proses yang aktif.")


def main():
    parser = argparse.ArgumentParser(description="AI Influencer Flexible Pipeline Reconciler")
    parser.add_argument("--daemon", action="store_true", help="Jalankan terus di latar belakang (loop)")
    parser.add_argument("--interval", type=int, default=180, help="Interval loop dalam detik (default 180s = 3 menit)")
    parser.add_argument("--status", action="store_true", help="Periksa apakah daemon sedang aktif")
    parser.add_argument("--stop", action="store_true", help="Hentikan daemon yang sedang berjalan")
    args = parser.parse_args()

    db_path = ROOT / "operations/production.sqlite"
    pid_file = ROOT / "operations/flexible_reconciler.pid"

    if args.status:
        check_status(pid_file)
        return

    if args.stop:
        stop_daemon(pid_file)
        return

    if args.daemon:
        pid_file.write_text(str(os.getpid()))
        print(f"[flexible_reconciler] Daemon aktif di PID {os.getpid()} (interval {args.interval}s)")
        try:
            while True:
                try:
                    res = run_once(db_path)
                    actions = res.get("actions_taken", [])
                    if actions:
                        print(f"[{res.get('timestamp_wib')}] Tindakan rekonsiliasi: {json.dumps(actions)}")
                except Exception as e:
                    print(f"[flexible_reconciler] Loop error: {e}", file=sys.stderr)
                time.sleep(args.interval)
        finally:
            if pid_file.exists():
                pid_file.unlink(missing_ok=True)
    else:
        res = run_once(db_path)
        print(json.dumps(res, indent=2))


if __name__ == "__main__":
    main()
