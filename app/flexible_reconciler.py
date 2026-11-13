"""
app/flexible_reconciler.py
Mekanisme toleransi waktu fleksibel (Option A) dan pemulihan mandiri (Auto-Recovery)
untuk pipeline produksi AI Influencer.

Aturan Utama:
1. Cutoff H-1 Jam: Retry diperbolehkan dari jam produksi hingga maksimal 1 jam sebelum jam tayang.
   - Dinda: 09:00 s/d 10:30 WIB (tayang 11:30)
   - ISK: 10:00 s/d 12:00 WIB (tayang 13:00)
   - Bang Ray: 14:00 s/d 15:00 WIB (tayang 16:00)
   - Pak Vincent: 15:00 s/d 17:00 WIB (tayang 18:00)
2. Kemandirian Penuh:
   - Coba pemulihan otomatis (auto-open tab via CDP, sinkronisasi saldo).
3. Protokol Notifikasi:
   - Percobaan 1: Silent auto-recovery (tanpa mengganggu Owner).
   - Percobaan 2: Jika masih gagal karena butuh campur tangan manusia (login/captcha/kredit habis),
     kirim Alert Kritis ke Telegram Owner.
   - Lewat Cutoff: Kirim info jadwal bahwa slot dilewati agar tidak bentrok dengan publikasi.
"""

from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import sqlite3
import subprocess
import sys

WIB = timezone(timedelta(hours=7))

DEFAULT_SCHEDULES = {
    "dinda": {"production_time_wib": "09:00", "publish_time_wib": "11:30"},
    "isk": {"production_time_wib": "10:00", "publish_time_wib": "13:00"},
    "bang_ray": {"production_time_wib": "14:00", "publish_time_wib": "16:00"},
    "pak_vincent": {"production_time_wib": "15:00", "publish_time_wib": "18:00"}
}

TALENT_LABELS = {
    "dinda": "Dinda Kemala (@dinda.kemala_)",
    "isk": "Intan Suar Kartika (@intansuarkartika)",
    "bang_ray": "Bang Ray (@teuku.rayyan00)",
    "pak_vincent": "Pak Vincent (@pakvincent.riau)"
}


def get_wib_now(ref_dt=None):
    if ref_dt is None:
        return datetime.now(WIB)
    if ref_dt.tzinfo is None:
        return ref_dt.replace(tzinfo=WIB)
    return ref_dt.astimezone(WIB)


def get_schedule_windows(root: Path, now_dt=None) -> dict:
    """Menghitung jendela waktu produksi dan batas cutoff H-1 jam untuk tiap karakter."""
    now_wib = get_wib_now(now_dt)
    today_str = now_wib.strftime("%Y-%m-%d")

    project_cfg_path = root / "config/project.json"
    schedules = DEFAULT_SCHEDULES.copy()
    if project_cfg_path.exists():
        try:
            cfg = json.loads(project_cfg_path.read_text())
            configured_sched = cfg.get("publication_schedules", {})
            for k, v in configured_sched.items():
                if "production_time_wib" in v and "publish_time_wib" in v:
                    schedules[k] = v
        except Exception:
            pass

    windows = {}
    for cid, sched in schedules.items():
        prod_h, prod_m = map(int, sched["production_time_wib"].split(":"))
        pub_h, pub_m = map(int, sched["publish_time_wib"].split(":"))

        prod_dt = now_wib.replace(hour=prod_h, minute=prod_m, second=0, microsecond=0)
        pub_dt = now_wib.replace(hour=pub_h, minute=pub_m, second=0, microsecond=0)
        cutoff_dt = pub_dt - timedelta(minutes=60)

        is_production_due = now_wib >= prod_dt
        is_within_retry_window = prod_dt <= now_wib < cutoff_dt
        is_past_cutoff = now_wib >= cutoff_dt
        remaining_secs = (cutoff_dt - now_wib).total_seconds()
        remaining_mins = max(0, int(remaining_secs // 60))

        windows[cid] = {
            "character_id": cid,
            "label": TALENT_LABELS.get(cid, cid),
            "date": today_str,
            "production_time_wib": sched["production_time_wib"],
            "publish_time_wib": sched["publish_time_wib"],
            "cutoff_time_wib": cutoff_dt.strftime("%H:%M"),
            "is_production_due": is_production_due,
            "is_within_retry_window": is_within_retry_window,
            "is_past_cutoff": is_past_cutoff,
            "minutes_to_cutoff": remaining_mins,
            "prod_dt": prod_dt.isoformat(),
            "pub_dt": pub_dt.isoformat(),
            "cutoff_dt": cutoff_dt.isoformat()
        }

    return windows


def get_reconciler_state_file(root: Path) -> Path:
    ops_dir = root / "operations"
    ops_dir.mkdir(parents=True, exist_ok=True)
    return ops_dir / "flexible_reconciler_state.json"


def load_reconciler_state(root: Path) -> dict:
    state_file = get_reconciler_state_file(root)
    if state_file.exists():
        try:
            return json.loads(state_file.read_text())
        except Exception:
            pass
    return {"date": "", "characters": {}}


def save_reconciler_state(root: Path, state: dict):
    state_file = get_reconciler_state_file(root)
    state_file.write_text(json.dumps(state, indent=2) + "\n")


def send_telegram_alert(root: Path, message_text: str) -> bool:
    """Mengirim pesan alert resmi ke Telegram Owner (Chat ID 7463982122)."""
    try:
        from app import review
        tg = review.Telegram(root)
        config = review.live_config(root)
        chat_id = config.get("allowed_chat_ids", [7463982122])[0]
        tg.call("sendMessage", {
            "chat_id": chat_id,
            "text": message_text,
            "link_preview_options": {"is_disabled": True}
        })
        return True
    except Exception as e:
        print(f"[flexible_reconciler] Telegram notice failed: {e}", file=sys.stderr)
        return False


def run_cdp_auto_recovery(root: Path, character_id: str) -> dict:
    """Memicu auto-open tab Flow dan sinkronisasi saldo via scripts/sync_flow_status.js."""
    script_path = root / "scripts/sync_flow_status.js"
    if not script_path.exists():
        return {"ok": False, "reason": "sync_flow_status.js not found"}

    try:
        cmd = ["node", str(script_path), "--character", character_id, "--ensure-360p"]
        proc = subprocess.run(cmd, cwd=str(root), capture_output=True, text=True, timeout=30)
        output_raw = proc.stdout.strip()
        try:
            data = json.loads(output_raw)
            return {"ok": proc.returncode == 0, "details": data}
        except Exception:
            return {"ok": proc.returncode == 0, "raw_output": output_raw}
    except Exception as e:
        return {"ok": False, "reason": str(e)}


def evaluate_and_reconcile(db: sqlite3.Connection, root: Path, now_dt=None, dry_run: bool = False) -> dict:
    """
    Evaluasi slot hari ini terhadap batas toleransi H-1 jam:
    - Jika dalam jendela retry dan slot masih belum selesai -> lakukan percobaan auto-recovery.
    - Jika gagal 2x karena masalah yang butuh manusia -> kirim alert kritis Telegram.
    - Jika telah melewati batas cutoff H-1 jam -> tandai skip dan beri tahu Telegram.
    """
    now_wib = get_wib_now(now_dt)
    today_str = now_wib.strftime("%Y-%m-%d")
    windows = get_schedule_windows(root, now_wib)
    state = load_reconciler_state(root)

    # Reset jika ganti hari
    if state.get("date") != today_str:
        state = {"date": today_str, "characters": {}}

    db.row_factory = sqlite3.Row
    actions_taken = []

    for cid, win in windows.items():
        char_state = state["characters"].setdefault(cid, {
            "attempts": 0,
            "last_attempt_at": None,
            "last_error": None,
            "alerted_critical": False,
            "skipped_due_to_cutoff": False
        })

        # Cek slot harian di database
        slot = db.execute(
            "SELECT * FROM daily_slots WHERE character_id = ? AND day = ?",
            (cid, today_str)
        ).fetchone()

        slot_state = slot["state"] if slot else "needs_plan"
        version_id = slot["version_id"] if slot else None

        # Jika sudah berstatus review_ready atau awaiting_review dengan versi valid -> Sukses
        if slot_state in ("review_ready", "awaiting_review") and version_id:
            char_state["completed"] = True
            continue

        # Kasus A: Dalam Jendela Toleransi Retry (Prod Time <= Now < Cutoff Time)
        if win["is_within_retry_window"]:
            if char_state["attempts"] == 0:
                # Percobaan 1: Silent auto-recovery
                action_info = {
                    "character_id": cid,
                    "action": "silent_auto_recovery_attempt_1",
                    "minutes_to_cutoff": win["minutes_to_cutoff"]
                }
                if not dry_run:
                    rec_res = run_cdp_auto_recovery(root, cid)
                    char_state["attempts"] = 1
                    char_state["last_attempt_at"] = now_wib.isoformat()
                    if not rec_res.get("ok"):
                        char_state["last_error"] = rec_res.get("reason", "Sync Flow failed")
                    action_info["result"] = rec_res
                actions_taken.append(action_info)

            elif char_state["attempts"] >= 1 and not char_state.get("alerted_critical"):
                # Percobaan 2: Cek apakah error butuh campur tangan manusia
                last_err = char_state.get("last_error") or "Sesi browser / verifikasi saldo tertahan"
                alert_text = (
                    f"⚠️ PERINGATAN TOLERANSI WAKTU\n"
                    f"Karakter: {win['label']}\n"
                    f"Jadwal Produksi: {win['production_time_wib']} WIB\n"
                    f"Batas Waktu Toleransi: {win['cutoff_time_wib']} WIB (sisa {win['minutes_to_cutoff']} menit)\n"
                    f"Kendala: {last_err}\n\n"
                    f"Sistem telah mencoba pemulihan otomatis (percobaan ke-2). "
                    f"Mohon periksa sesi Chrome di port 9333 sebelum batas toleransi habis."
                )
                action_info = {
                    "character_id": cid,
                    "action": "critical_telegram_alert_attempt_2",
                    "reason": last_err
                }
                if not dry_run:
                    sent = send_telegram_alert(root, alert_text)
                    char_state["attempts"] += 1
                    char_state["alerted_critical"] = True
                    char_state["last_attempt_at"] = now_wib.isoformat()
                    action_info["telegram_sent"] = sent
                actions_taken.append(action_info)

        # Kasus B: Melewati Batas Toleransi H-1 Jam (Now >= Cutoff Time)
        elif win["is_past_cutoff"]:
            if not char_state.get("completed") and not char_state.get("skipped_due_to_cutoff"):
                skip_text = (
                    f"ℹ️ INFORMASI JADWAL - SLOT DILEWATI\n"
                    f"Karakter: {win['label']}\n"
                    f"Jadwal Tayang: {win['publish_time_wib']} WIB\n"
                    f"Batas Toleransi: {win['cutoff_time_wib']} WIB telah terlewati.\n\n"
                    f"Sesuai aturan toleransi Option A (maksimal H-1 jam sebelum tayang), "
                    f"slot produksi hari ini otomatis dilewati (skip) agar tidak bentrok dengan jadwal tayang."
                )
                action_info = {
                    "character_id": cid,
                    "action": "skip_due_to_cutoff_exceeded",
                    "cutoff_time": win["cutoff_time_wib"]
                }
                if not dry_run:
                    send_telegram_alert(root, skip_text)
                    char_state["skipped_due_to_cutoff"] = True
                    char_state["last_attempt_at"] = now_wib.isoformat()
                actions_taken.append(action_info)

    if not dry_run:
        save_reconciler_state(root, state)

    return {
        "timestamp_wib": now_wib.strftime("%Y-%m-%d %H:%M:%S WIB"),
        "windows": windows,
        "state": state,
        "actions_taken": actions_taken
    }


def main():
    root = Path(__file__).resolve().parents[1]
    db_path = root / "operations/production.sqlite"
    if not db_path.exists():
        print(f"Database not found: {db_path}", file=sys.stderr)
        sys.exit(1)

    db = sqlite3.connect(str(db_path), timeout=10)
    try:
        res = evaluate_and_reconcile(db, root)
        print(json.dumps(res, indent=2))
    finally:
        db.close()


if __name__ == "__main__":
    main()
