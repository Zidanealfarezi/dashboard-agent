#!/usr/bin/env python3
"""Lightweight single-instance watcher that processes Telegram ACC/Revisi/Tolak callbacks promptly.

Wraps the single-shot app.review.receive_once() function so clicking an inline button on
@ISKAGENT_BOT records the durable decision in SQLite and updates the visible Telegram card
within seconds, while keeping app/review.py itself free of daemon code.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import sqlite3
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app import review


def poll_once(root: Path = ROOT, api_factory=None) -> dict:
    """Run one safe review callback poll cycle and return status metadata."""
    try:
        review.live_config(root)
    except (review.ReviewError, OSError, ValueError) as exc:
        return {"ok": False, "skipped": True, "processed": 0, "reason": str(exc)}

    api = api_factory(root) if api_factory is not None else review.Telegram(root)
    try:
        with review.connect(root) as db:
            processed = review.receive_once(db, root, api)
        return {"ok": True, "skipped": False, "processed": int(processed)}
    except (review.ReviewError, OSError, ValueError, sqlite3.Error) as exc:
        return {"ok": False, "skipped": False, "processed": 0, "reason": str(exc)}


def watch_loop(root: Path = ROOT, interval: float = 3.0, max_cycles: int | None = None, api_factory=None) -> int:
    """Continuously poll Telegram review callbacks at a gentle fixed interval."""
    cycles = 0
    while max_cycles is None or cycles < max_cycles:
        result = poll_once(root=root, api_factory=api_factory)
        cycles += 1
        if result.get("processed", 0) > 0:
            print(f"[ReviewWatcher] Processed {result['processed']} Telegram callback(s).", flush=True)
        elif not result.get("ok") and not result.get("skipped"):
            print(f"[ReviewWatcher] Poll deferred: {result.get('reason', 'unknown error')}", file=sys.stderr, flush=True)
        if max_cycles is not None and cycles >= max_cycles:
            break
        time.sleep(max(1.0, float(interval)))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--once", action="store_true", help="Jalankan tepat satu siklus lalu keluar")
    parser.add_argument("--interval", type=float, default=3.0, help="Jeda antar poll dalam detik (default: 3.0)")
    args = parser.parse_args()

    if args.once:
        res = poll_once(root=ROOT)
        print(f"[ReviewWatcher] once: {res}", flush=True)
        return 0 if res.get("ok") or res.get("skipped") else 1

    print(f"[ReviewWatcher] Memulai pemantau tombol ACC Telegram (interval {max(1.0, args.interval):.1f}s)...", flush=True)
    return watch_loop(root=ROOT, interval=args.interval)


if __name__ == "__main__":
    raise SystemExit(main())
