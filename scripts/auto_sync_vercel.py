#!/usr/bin/env python3
"""
Auto Sync Watcher Daemon for Vercel Deployment (Cara 3)
Monitors changes to SQLite database, content plans, and operations data.
Automatically commits and pushes updates to GitHub ('origin/main')
so Vercel redeploys with the latest live data automatically.
"""

import os
import sys
import time
import signal
import hashlib
import logging
import argparse
import subprocess
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent.parent
OPERATIONS_DIR = BASE_DIR / "operations"
PLANS_DIR = OPERATIONS_DIR / "plans"
BRIEFS_DIR = OPERATIONS_DIR / "research-briefs"
DB_PATH = OPERATIONS_DIR / "production.sqlite"
CONFIG_FLOW = BASE_DIR / "config" / "flow_accounts.json"

PID_FILE = OPERATIONS_DIR / "auto_sync_vercel.pid"
LOG_FILE = OPERATIONS_DIR / "auto_sync_vercel.log"

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(str(LOG_FILE), encoding="utf-8"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("auto_sync_vercel")

try:
    from app.system_monitor import get_host_services_status
except Exception:
    get_host_services_status = None

def get_file_hash(path: Path) -> str:
    if not path.exists():
        return "not_found"
    try:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            while chunk := f.read(65536):
                h.update(chunk)
        return h.hexdigest()
    except Exception as e:
        return f"err_{e}"

def compute_state_signature() -> str:
    """Computes a lightweight signature of all monitored operational data."""
    parts = []
    # 1. SQLite database
    parts.append(get_file_hash(DB_PATH))
    # 2. Config flow accounts
    parts.append(get_file_hash(CONFIG_FLOW))
    # 3. Plans directory
    if PLANS_DIR.exists():
        for p in sorted(PLANS_DIR.glob("*.json")):
            parts.append(f"{p.name}:{p.stat().st_mtime}:{p.stat().st_size}")
    # 4. Research briefs directory
    if BRIEFS_DIR.exists():
        for b in sorted(BRIEFS_DIR.glob("*.json")):
            parts.append(f"{b.name}:{b.stat().st_mtime}:{b.stat().st_size}")
    
    return hashlib.sha256(";".join(parts).encode("utf-8")).hexdigest()

def run_cmd(cmd: list, cwd: Path = BASE_DIR) -> tuple[int, str, str]:
    try:
        res = subprocess.run(
            cmd,
            cwd=str(cwd),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=45
        )
        return res.returncode, res.stdout.strip(), res.stderr.strip()
    except Exception as e:
        return -1, "", str(e)

def perform_sync(reason: str = "data modification") -> bool:
    """Stages operational data, commits, and pushes to origin/main."""
    logger.info(f"🔄 Triggering sync to Vercel (Reason: {reason})...")

    # Refresh host agent snapshot
    if get_host_services_status:
        try:
            get_host_services_status()
            logger.info("📡 Refreshed host agent status snapshot.")
        except Exception as e:
            logger.warning(f"Failed to refresh host status snapshot: {e}")
    
    # Files to stage
    paths_to_stage = [
        "operations/production.sqlite",
        "operations/host_agent_status.json",
        "operations/plans",
        "operations/research-briefs",
        "config/flow_accounts.json",
        ".gitignore"
    ]
    
    existing_paths = [p for p in paths_to_stage if (BASE_DIR / p).exists()]
    if not existing_paths:
        logger.warning("No target paths exist to stage.")
        return False

    code, out, err = run_cmd(["git", "add"] + existing_paths)
    if code != 0:
        logger.error(f"git add failed: {err}")
        return False

    # Check if there are staged changes
    code, out, err = run_cmd(["git", "diff", "--staged", "--quiet"])
    if code == 0:
        logger.info("ℹ️ No staged differences found. Nothing to sync.")
        return True

    # Commit
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S WIB")
    commit_msg = f"auto-sync: update production database & operations [{now_str}]"
    code, out, err = run_cmd(["git", "commit", "-m", commit_msg])
    if code != 0:
        logger.error(f"git commit failed: {err}")
        return False
    logger.info(f"✅ Committed changes: {commit_msg}")

    # Push to origin main
    logger.info("🚀 Pushing to GitHub (origin/main) to trigger Vercel deployment...")
    code, out, err = run_cmd(["git", "push", "origin", "main"])
    if code != 0:
        logger.error(f"❌ git push failed: {err}")
        return False

    logger.info("🎉 Berhasil sync ke GitHub & Vercel! Deployment akan terupdate dalam ~20-30 detik.")
    return True

def run_daemon(poll_interval: float = 10.0, debounce_wait: float = 20.0):
    # Write PID
    PID_FILE.write_text(str(os.getpid()))
    logger.info(f"🚀 Auto-Sync Daemon Vercel dimulai (PID: {os.getpid()})")
    logger.info(f"👀 Memantau database: {DB_PATH}")
    logger.info(f"⏱️ Interval polling: {poll_interval}s, Debounce: {debounce_wait}s")

    def handle_exit(signum, frame):
        logger.info("Menghentikan Auto-Sync Daemon...")
        if PID_FILE.exists():
            PID_FILE.unlink(missing_ok=True)
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_exit)
    signal.signal(signal.SIGTERM, handle_exit)

    last_sig = compute_state_signature()
    change_detected_at = None

    try:
        while True:
            time.sleep(poll_interval)
            current_sig = compute_state_signature()

            if current_sig != last_sig:
                if change_detected_at is None:
                    logger.info("📝 Perubahan data terdeteksi! Menunggu debounce stabil...")
                change_detected_at = time.time()
                last_sig = current_sig
            elif change_detected_at is not None:
                # Signature is stable now, check debounce
                if time.time() - change_detected_at >= debounce_wait:
                    logger.info(f"⏱️ Debounce stabil ({debounce_wait}s terpenuhi). Menjalankan sinkronisasi...")
                    success = perform_sync(reason="database / plans modified")
                    change_detected_at = None
                    last_sig = compute_state_signature()
    finally:
        if PID_FILE.exists():
            PID_FILE.unlink(missing_ok=True)

def is_running() -> tuple[bool, int]:
    if not PID_FILE.exists():
        return False, 0
    try:
        pid = int(PID_FILE.read_text().strip())
        os.kill(pid, 0)
        return True, pid
    except Exception:
        return False, 0

def stop_daemon():
    running, pid = is_running()
    if not running:
        print("Auto-Sync Daemon tidak sedang berjalan.")
        if PID_FILE.exists():
            PID_FILE.unlink(missing_ok=True)
        return
    try:
        os.kill(pid, signal.SIGTERM)
        print(f"Mengirim sinyal stop ke daemon (PID: {pid})...")
        time.sleep(1)
        if PID_FILE.exists():
            PID_FILE.unlink(missing_ok=True)
        print("Daemon berhasil dihentikan.")
    except Exception as e:
        print(f"Gagal menghentikan daemon: {e}")

def main():
    parser = argparse.ArgumentParser(description="Auto Sync Daemon for Vercel Hub")
    parser.add_argument("--once", action="store_true", help="Jalankan sinkronisasi 1x jika ada perubahan lalu keluar")
    parser.add_argument("--daemon", action="store_true", help="Jalankan sebagai background daemon")
    parser.add_argument("--status", action="store_true", help="Periksa status daemon")
    parser.add_argument("--stop", action="store_true", help="Hentikan daemon yang berjalan")
    parser.add_argument("--interval", type=float, default=10.0, help="Interval pengecekan (detik)")
    parser.add_argument("--debounce", type=float, default=20.0, help="Jeda debounce sebelum sync (detik)")

    args = parser.parse_args()

    if args.status:
        running, pid = is_running()
        if running:
            print(f"✅ Auto-Sync Daemon SEDANG BERJALAN di PID {pid}")
            if LOG_FILE.exists():
                print(f"📄 Log terakhir ({LOG_FILE}):")
                with open(LOG_FILE, "r") as f:
                    lines = f.readlines()
                    for l in lines[-8:]:
                        print("  " + l.strip())
        else:
            print("❌ Auto-Sync Daemon TIDAK AKTIF.")
        return

    if args.stop:
        stop_daemon()
        return

    if args.once:
        perform_sync(reason="manual trigger --once")
        return

    if args.daemon:
        running, pid = is_running()
        if running:
            print(f"Daemon sudah berjalan di PID {pid}.")
            return
        run_daemon(poll_interval=args.interval, debounce_wait=args.debounce)
        return

    # Default to --once if no arguments given
    perform_sync(reason="default run")

if __name__ == "__main__":
    main()
