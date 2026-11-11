#!/usr/bin/env python3
"""
Kantor AI Intan - Secure Virtual Office Server
Serves 3D Virtual Office on http://localhost:5173
Secured with PIN/Token Authentication Gate
"""
import http.server
import socketserver
import json
import os
import sqlite3
import urllib.parse
from pathlib import Path
from office_status import get_office_status

PORT = 5173
BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent
DB_PATH = PROJECT_DIR / "operations" / "production.sqlite"
CONFIG_ACCESS_PATH = PROJECT_DIR / "config" / "access.json"

def load_access_config():
    default_cfg = {
        "pin": "7463982122",
        "passphrase": "intan",
        "secret_token": "token_intan_ai_hq_88329104"
    }
    if CONFIG_ACCESS_PATH.exists():
        try:
            with open(CONFIG_ACCESS_PATH, "r", encoding="utf-8") as f:
                return {**default_cfg, **json.load(f)}
        except Exception:
            pass
    return default_cfg

class SecureVirtualOfficeHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(BASE_DIR), **kwargs)

    def is_authenticated(self):
        cfg = load_access_config()
        secret = cfg.get("secret_token")

        # 1. Check Authorization Header: Bearer <token>
        auth_header = self.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header.split(" ", 1)[1].strip()
            if token == secret:
                return True

        # 2. Check Query parameter: ?token=<token>
        parsed = urllib.parse.urlparse(self.path)
        qs = urllib.parse.parse_qs(parsed.query)
        if "token" in qs and qs["token"][0] == secret:
            return True

        # 3. Check Cookie: access_token=<token>
        cookie_header = self.headers.get("Cookie", "")
        for c in cookie_header.split(";"):
            parts = c.strip().split("=", 1)
            if len(parts) == 2 and parts[0] == "access_token" and parts[1] == secret:
                return True

        return False

    def do_POST(self):
        if self.path == "/api/logout":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Set-Cookie", "access_token=; Path=/; HttpOnly; SameSite=Lax; Max-Age=0")
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(b'{"ok":true}')
        elif self.path == "/api/auth":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode("utf-8")
            try:
                data = json.loads(body)
            except Exception:
                data = {}

            input_pin = str(data.get("pin", "")).strip()
            cfg = load_access_config()

            # Accepts Owner ID PIN (7463982122) or passphrase (intan)
            valid_pins = [str(cfg.get("pin", "")).strip(), str(cfg.get("passphrase", "")).strip()]

            if input_pin and input_pin in valid_pins:
                token = cfg.get("secret_token")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.send_header("Set-Cookie", f"access_token={token}; Path=/; SameSite=Lax; Max-Age=2592000")
                self.end_headers()
                res = {
                    "authenticated": True,
                    "token": token,
                    "role": "Owner / Executive",
                    "message": "Akses Diterima. Selamat datang di Kantor AI Intan."
                }
                self.wfile.write(json.dumps(res).encode("utf-8"))
            else:
                self.send_response(401)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                res = {
                    "authenticated": False,
                    "error": "PIN / Kata Sandi Tidak Valid. Akses Ditolak."
                }
                self.wfile.write(json.dumps(res).encode("utf-8"))
        elif self.path == "/api/trigger-evaluation":
            # Run weekly evaluation
            try:
                import subprocess
                script_path = PROJECT_DIR / "scripts" / "generate_weekly_evaluation.py"
                out = subprocess.check_output(["python3", str(script_path)], stderr=subprocess.STDOUT).decode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps({"ok": True, "output": out}).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps({"ok": False, "error": str(e)}).encode("utf-8"))
        else:
            self.send_error(404, "Endpoint not found")

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)

        if parsed.path == "/api/status":
            if not self.is_authenticated():
                self.send_response(401)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                res = {
                    "error": "Akses Ditolak. Harap verifikasi PIN keamanan Kantor AI Intan.",
                    "authenticated": False
                }
                self.wfile.write(json.dumps(res).encode("utf-8"))
                return

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            data = self.get_production_status()
            self.wfile.write(json.dumps(data, indent=2).encode("utf-8"))
        else:
            super().do_GET()

    def get_production_status(self):
        res = {
            "characters": [],
            "stats": {
                "total_jobs": 0,
                "completed_jobs": 0,
                "credits_used": 0,
                "total_approved": 0,
                "flow_credits_remaining": 458
            },
            "recent_jobs": [],
            "recent_approvals": [],
            "active_renders": [],
            "pending_accs": [],
            "active_publications": [],
            "department_states": {},
            "office": get_office_status(PROJECT_DIR)
        }

        if not DB_PATH.exists():
            return res

        try:
            conn = sqlite3.connect(DB_PATH.as_uri() + "?mode=ro", uri=True)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()

            # Characters
            cur.execute("SELECT id, name, account FROM characters")
            res["characters"] = [dict(r) for r in cur.fetchall()]

            # Jobs stats
            cur.execute("SELECT count(*) as c, sum(actual_credits) as credits FROM generation_jobs WHERE state='completed'")
            row = cur.fetchone()
            if row:
                res["stats"]["completed_jobs"] = row["c"] or 0
                res["stats"]["credits_used"] = row["credits"] or 0

            cur.execute("SELECT count(*) as c FROM generation_jobs")
            row = cur.fetchone()
            if row:
                res["stats"]["total_jobs"] = row["c"] or 0

            # Approvals stats
            cur.execute("SELECT count(*) as c FROM approvals WHERE decision='approved'")
            row = cur.fetchone()
            if row:
                res["stats"]["total_approved"] = row["c"] or 0

            # Recent jobs
            cur.execute("SELECT id, character_id, model, state, actual_credits, created_at FROM generation_jobs ORDER BY created_at DESC LIMIT 5")
            res["recent_jobs"] = [dict(r) for r in cur.fetchall()]

            # Recent approvals
            cur.execute("SELECT id, decision, reviewer_id, channel, created_at FROM approvals ORDER BY created_at DESC LIMIT 5")
            res["recent_approvals"] = [dict(r) for r in cur.fetchall()]

            # Active ongoing tasks (Live Work Monitoring)
            cur.execute("SELECT * FROM generation_jobs WHERE state IN ('running', 'submitted', 'awaiting_budget')")
            active_renders = [dict(r) for r in cur.fetchall()]
            res["active_renders"] = active_renders

            cur.execute("""
                SELECT rd.id, rd.version_id, rd.chat_id, rd.state, rd.created_at, v.caption, v.media_path, v.destination_account 
                FROM review_deliveries rd 
                JOIN versions v ON rd.version_id = v.id 
                WHERE rd.state = 'sent' AND (rd.decision IS NULL OR rd.decision = '')
            """)
            pending_accs = [dict(r) for r in cur.fetchall()]
            res["pending_accs"] = pending_accs

            cur.execute("SELECT * FROM publications WHERE state IN ('submitted', 'planned')")
            active_pubs = [dict(r) for r in cur.fetchall()]
            res["active_publications"] = active_pubs

            # Latest research report
            reports_dir = PROJECT_DIR / "operations" / "reports"
            latest_research = None
            if reports_dir.exists():
                r_files = sorted(reports_dir.glob("research-*.json"), key=os.path.getmtime, reverse=True)
                if r_files:
                    try:
                        with open(r_files[0], "r", encoding="utf-8") as rf:
                            latest_research = json.load(rf)
                    except Exception:
                        pass
            res["latest_research"] = latest_research

            # Department live states mapping
            res["department_states"] = {
                "pm": {
                    "state": "reviewing_brief" if latest_research and not pending_accs else ("waiting_acc" if pending_accs else "standby"),
                    "task": f"Menelaah Riset: {latest_research['target_character']['name']}" if latest_research and not pending_accs else (f"Menunggu ACC Owner: {pending_accs[0]['destination_account']}" if pending_accs else "Standby • Monitoring Kalender & Naskah"),
                    "badge": "⚡ REVIEW BRIEF" if latest_research and not pending_accs else ("🔔 BUTUH ACC" if pending_accs else "● STANDBY")
                },
                "flow": {
                    "state": "rendering" if active_renders else "standby",
                    "task": f"Merender {len(active_renders)} Video (Omni 1.1 Flash)" if active_renders else "Standby • GPU Siap (0% Load)",
                    "badge": "⚡ RENDERING" if active_renders else "● STANDBY"
                },
                "dinda": {
                    "state": "publishing" if any(p.get("destination_account") == "@dinda.kemala_" for p in active_pubs) else "standby",
                    "task": "Memantau Komentar & DM TikTok" if not active_pubs else "Mengunggah Video Baru...",
                    "badge": "● AKTIF MEDSOS"
                },
                "nara": {
                    "state": "standby",
                    "task": "Standby • Target Riset Konten Pagi",
                    "badge": "● AKTIF MEDSOS"
                },
                "rania": {
                    "state": "standby",
                    "task": "Standby • Menjawab DM Budaya Aceh",
                    "badge": "● AKTIF MEDSOS"
                },
                "trend": {
                    "state": "completed_recent" if latest_research else "standby",
                    "task": f"Riset Terkirim: {latest_research['trend_data']['title']}" if latest_research else "Memantau Sound & Audio Viral TikTok",
                    "badge": "✓ RISET SELESAI" if latest_research else "● MONITORING"
                }
            }

            conn.close()
        except Exception as e:
            res["error"] = str(e)

        return res

if __name__ == "__main__":
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), SecureVirtualOfficeHandler) as httpd:
        print(f"🔒 Kantor AI Intan (SECURE MODE) running at: http://localhost:{PORT}")
        print(f"📁 Serving: {BASE_DIR}")
        print(f"🔑 Protected with PIN & Token Verification")
        httpd.serve_forever()
