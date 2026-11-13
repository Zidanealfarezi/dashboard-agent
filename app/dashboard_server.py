#!/usr/bin/env python3
"""
AI Influencer - Database & Operations Web Dashboard Server
Super Finti / Metabase Hybrid Theme
Inspired by modern Dribbble FinTech dashboards & Metabase Content Marketing Analytics.
"""

import os
import sys
import json
import sqlite3
import mimetypes
import urllib.parse
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "operations/production.sqlite"
CONFIG_DIR = BASE_DIR / "config"
CHARACTERS_DIR = BASE_DIR / "characters"
FOTO_DIR = BASE_DIR / "FOTO_KARAKTER"

PORT = 8080

def get_db():
    try:
        conn = sqlite3.connect(f"file:{DB_PATH.resolve()}?mode=ro", uri=True)
    except Exception:
        conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn

def load_json(path):
    if path.exists():
        try:
            return json.loads(path.read_text())
        except Exception:
            return None
    return None

try:
    from app.system_monitor import get_combined_agent_status
except Exception:
    try:
        from system_monitor import get_combined_agent_status
    except Exception:
        get_combined_agent_status = None

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True

class DashboardHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        sys.stderr.write(f"[{self.log_date_time_string()}] {self.command} {self.path} -> {args[1] if len(args) > 1 else ''}\n")

    def _resolve_request(self):
        # Resolve path safely (handling Vercel rewrites where self.path might be /api/index.py)
        raw = self.path
        if raw in ('/api/index.py', '/api', '/api/'):
            fwd = self.headers.get('x-forwarded-uri') or self.headers.get('x-matched-path')
            if fwd:
                raw = fwd
        parsed = urllib.parse.urlparse(raw)
        return parsed.path, urllib.parse.parse_qs(parsed.query)

    def send_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False, default=str).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS, HEAD')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_HEAD(self):
        path, _ = self._resolve_request()
        if path.startswith('/assets/'):
            target = (BASE_DIR / path[8:]).resolve()
            if str(target).startswith(str(BASE_DIR)) and target.exists() and target.is_file():
                mime_type, _ = mimetypes.guess_type(str(target))
                self.send_response(200)
                self.send_header('Content-Type', mime_type or 'application/octet-stream')
                self.send_header('Content-Length', str(target.stat().st_size))
                self.end_headers()
                return
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        path, query = self._resolve_request()

        if path in ('', '/', '/index.html'):
            self.serve_html()
        elif path == '/favicon.ico':
            self.send_response(204)
            self.end_headers()
        elif path.startswith('/assets/'):
            self.serve_asset(path[8:])
        elif path == '/api/overview':
            self.handle_api_overview()
        elif path == '/api/agents_status':
            self.handle_api_agents_status()
        elif path == '/api/characters':
            self.handle_api_characters()
        elif path == '/api/publications':
            self.handle_api_publications(query)
        elif path == '/api/approvals':
            self.handle_api_approvals()
        elif path == '/api/tables':
            self.handle_api_tables()
        elif path.startswith('/api/table/'):
            table_name = path[11:]
            self.handle_api_table_data(table_name, query)
        else:
            self.send_error(404, "Not Found")

    def do_POST(self):
        path, _ = self._resolve_request()
        if path == '/api/query':
            content_length = int(self.headers.get('Content-Length', 0))
            post_body = self.rfile.read(content_length)
            try:
                payload = json.loads(post_body.decode('utf-8'))
                sql = payload.get('sql', '').strip()
                if not sql.lower().startswith('select') and not sql.lower().startswith('pragma') and not sql.lower().startswith('explain'):
                    self.send_json({'error': 'Hanya query baca (SELECT / PRAGMA) yang diizinkan demi keamanan database.'}, status=400)
                    return
                with get_db() as conn:
                    cur = conn.cursor()
                    cur.execute(sql)
                    cols = [desc[0] for desc in cur.description] if cur.description else []
                    rows = [dict(zip(cols, r)) for r in cur.fetchall()]
                    self.send_json({'columns': cols, 'rows': rows, 'count': len(rows)})
            except Exception as e:
                self.send_json({'error': str(e)}, status=400)
        else:
            self.send_error(404, "Not Found")

    def serve_asset(self, subpath):
        target = (BASE_DIR / subpath).resolve()
        if not str(target).startswith(str(BASE_DIR)) or not target.exists() or not target.is_file():
            self.send_error(404, "File not found")
            return
        mime_type, _ = mimetypes.guess_type(str(target))
        mime_type = mime_type or 'application/octet-stream'
        data = target.read_bytes()
        self.send_response(200)
        self.send_header('Content-Type', mime_type)
        self.send_header('Content-Length', str(len(data)))
        self.send_header('Cache-Control', 'max-age=3600')
        self.end_headers()
        self.wfile.write(data)

    def handle_api_overview(self):
        with get_db() as conn:
            cur = conn.cursor()
            tables = ["characters", "content", "versions", "approvals", "publications", "generation_jobs", "trend_memory", "daily_slots"]
            counts = {}
            for t in tables:
                try:
                    counts[t] = cur.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
                except Exception:
                    counts[t] = 0

            flow_cfg = load_json(CONFIG_DIR / "flow_accounts.json") or {}
            flow_accounts = flow_cfg.get("accounts", [])
            total_credits = sum((acc.get("verified_balance") or acc.get("reported_monthly_credits") or 0) for acc in flow_accounts)

            recent_pubs = cur.execute("""
                SELECT 
                    p.id as pub_id, p.state, p.platform_post_id, p.post_url, p.confirmed_at,
                    v.id as version_id, c.character_id, ch.name as character_name, ch.account,
                    v.media_path, v.caption, a.decision as approval_decision
                FROM publications p
                LEFT JOIN versions v ON p.version_id = v.id
                LEFT JOIN content c ON v.content_id = c.id
                LEFT JOIN characters ch ON c.character_id = ch.id
                LEFT JOIN approvals a ON a.version_id = v.id
                ORDER BY p.ROWID DESC
                LIMIT 15
            """).fetchall()

            recent_acc = cur.execute("""
                SELECT a.id, a.version_id, a.decision, a.reviewer_id, a.channel, a.created_at,
                       c.character_id, ch.name as character_name, ch.account
                FROM approvals a
                LEFT JOIN versions v ON a.version_id = v.id
                LEFT JOIN content c ON v.content_id = c.id
                LEFT JOIN characters ch ON c.character_id = ch.id
                ORDER BY a.ROWID DESC
                LIMIT 10
            """).fetchall()

            project_cfg = load_json(CONFIG_DIR / "project.json") or {}

            agents_status = get_combined_agent_status(conn) if get_combined_agent_status else {}

            self.send_json({
                'counts': counts,
                'total_credits': total_credits,
                'flow_accounts': flow_accounts,
                'recent_publications': [dict(r) for r in recent_pubs],
                'recent_approvals': [dict(r) for r in recent_acc],
                'schedules': project_cfg.get('publication_schedules', {}),
                'agents_status': agents_status
            })

    def handle_api_agents_status(self):
        with get_db() as conn:
            if get_combined_agent_status:
                data = get_combined_agent_status(conn)
            else:
                data = {'status': 'error', 'error': 'System monitor unavailable'}
            self.send_json(data)

    def handle_api_characters(self):
        with get_db() as conn:
            cur = conn.cursor()
            rows = cur.execute("SELECT * FROM characters").fetchall()
            chars = []
            for r in rows:
                c_dict = dict(r)
                cid = c_dict['id']
                profile_path = CHARACTERS_DIR / cid / "profile.json"
                prof = load_json(profile_path) or {}
                
                pub_count = cur.execute("""
                    SELECT COUNT(*) FROM publications p
                    JOIN versions v ON p.version_id = v.id
                    JOIN content c ON v.content_id = c.id
                    WHERE c.character_id = ?
                """, (cid,)).fetchone()[0]

                avatar_url = None
                if cid == 'pak_vincent':
                    avatar_url = '/assets/FOTO_KARAKTER/PakVincent/pakvincent_profile_avatar.jpg'
                elif cid == 'bang_ray':
                    avatar_url = '/assets/FOTO_KARAKTER/BangRay/bangray_profile_avatar.jpg'
                elif cid == 'dinda':
                    avatar_url = '/assets/FOTO_KARAKTER/Dinda/dinda.jpg'
                elif cid == 'isk':
                    avatar_url = None
                elif cid == 'nara':
                    avatar_url = '/assets/FOTO_KARAKTER/Nara/Photorealistic_four-view_character_reference_sheet.png_e3d7c474.jpg'
                elif cid == 'rania':
                    avatar_url = '/assets/FOTO_KARAKTER/Rania/Person_portrait_in_natural_light_a467b5c6.jpg'

                c_dict.update({
                    'avatar_url': avatar_url,
                    'age': prof.get('age'),
                    'origin': prof.get('origin', 'Indonesia'),
                    'job_title': prof.get('job_title', prof.get('employment', 'Talent Kreator')),
                    'content_pillars': prof.get('content_pillars', []),
                    'signature_wardrobe': prof.get('signature_wardrobe'),
                    'flow_account_id': prof.get('flow_account_id'),
                    'publication_count': pub_count
                })
                chars.append(c_dict)
            self.send_json(chars)

    def handle_api_publications(self, query):
        char_filter = query.get('character', [None])[0]
        sql = """
            SELECT 
                p.id as pub_id, p.state, p.platform_post_id, p.post_url, p.confirmed_at,
                v.id as version_id, c.character_id, ch.name as character_name, ch.account,
                v.media_path, v.caption, a.decision as approval_decision
            FROM publications p
            LEFT JOIN versions v ON p.version_id = v.id
            LEFT JOIN content c ON v.content_id = c.id
            LEFT JOIN characters ch ON c.character_id = ch.id
            LEFT JOIN approvals a ON a.version_id = v.id
        """
        params = []
        if char_filter:
            sql += " WHERE c.character_id = ?"
            params.append(char_filter)
        sql += " ORDER BY p.ROWID DESC"
        with get_db() as conn:
            cur = conn.cursor()
            rows = cur.execute(sql, params).fetchall()
            self.send_json([dict(r) for r in rows])

    def handle_api_approvals(self):
        with get_db() as conn:
            cur = conn.cursor()
            rows = cur.execute("""
                SELECT a.id, a.version_id, a.decision, a.reviewer_id, a.channel, a.created_at,
                       c.character_id, ch.name as character_name, ch.account, v.media_path, v.caption
                FROM approvals a
                LEFT JOIN versions v ON a.version_id = v.id
                LEFT JOIN content c ON v.content_id = c.id
                LEFT JOIN characters ch ON c.character_id = ch.id
                ORDER BY a.ROWID DESC
            """).fetchall()
            self.send_json([dict(r) for r in rows])

    def handle_api_tables(self):
        with get_db() as conn:
            cur = conn.cursor()
            t_rows = cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()
            tables = []
            for r in t_rows:
                name = r[0]
                cols = [c[1] for c in cur.execute(f"PRAGMA table_info({name})").fetchall()]
                count = cur.execute(f"SELECT COUNT(*) FROM {name}").fetchone()[0]
                tables.append({'name': name, 'columns': cols, 'count': count})
            self.send_json(tables)

    def handle_api_table_data(self, table_name, query):
        limit = min(int(query.get('limit', [100])[0]), 500)
        offset = int(query.get('offset', [0])[0])
        search = query.get('search', [''])[0].strip()

        with get_db() as conn:
            cur = conn.cursor()
            valid_tables = [r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
            if table_name not in valid_tables:
                self.send_error(404, "Table not found")
                return

            cols = [c[1] for c in cur.execute(f"PRAGMA table_info({table_name})").fetchall()]
            sql = f"SELECT * FROM {table_name}"
            params = []
            if search and cols:
                conds = [f"CAST({c} AS TEXT) LIKE ?" for c in cols]
                sql += " WHERE " + " OR ".join(conds)
                params.extend([f"%{search}%"] * len(cols))

            count_sql = f"SELECT COUNT(*) FROM ({sql})"
            total_count = cur.execute(count_sql, params).fetchone()[0]

            sql += f" LIMIT {limit} OFFSET {offset}"
            rows = cur.execute(sql, params).fetchall()

            self.send_json({
                'table': table_name,
                'columns': cols,
                'total_count': total_count,
                'rows': [dict(r) for r in rows]
            })

    def serve_html(self):
        html = """<!DOCTYPE html>
<html lang="id">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>AI Influencer & Content Operations Hub</title>
  <!-- Tailwind CSS CDN -->
  <script src="https://cdn.tailwindcss.com"></script>
  <!-- Google Fonts: Inter & Plus Jakarta Sans -->
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;700&display=swap" rel="stylesheet">
  <!-- Lucide Icons -->
  <script src="https://unpkg.com/lucide@latest"></script>
  <script>
    tailwind.config = {
      theme: {
        extend: {
          fontFamily: {
            sans: ['"Plus Jakarta Sans"', 'sans-serif'],
            mono: ['"JetBrains Mono"', 'monospace']
          },
          colors: {
            finti: {
              purple: '#5e27d6',
              purpleDark: '#4416ad',
              purpleLight: '#7b40f2',
              mint: '#d4fbe4',
              coral: '#ff694a',
              cyan: '#00d5dc',
              bg: '#f1f3f9',
              sidebar: '#ffffff',
              card: '#ffffff'
            }
          }
        }
      }
    }
  </script>
  <style>
    body {
      font-family: 'Plus Jakarta Sans', sans-serif;
      background-color: #f1f3f9;
      color: #1e293b;
    }
    .custom-scroll::-webkit-scrollbar { width: 6px; height: 6px; }
    .custom-scroll::-webkit-scrollbar-track { background: #f1f5f9; }
    .custom-scroll::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 4px; }
    .custom-scroll::-webkit-scrollbar-thumb:hover { background: #94a3b8; }
    
    /* Bar glow effects from the inspiration image */
    .bar-glow-coral { box-shadow: 0 8px 16px -2px rgba(255, 105, 74, 0.4); }
    .bar-glow-purple { box-shadow: 0 8px 16px -2px rgba(94, 39, 214, 0.4); }
    .bar-glow-cyan { box-shadow: 0 8px 16px -2px rgba(0, 213, 220, 0.4); }
    
    /* Organic wave background on mint card */
    .mint-wave-bg {
      background-color: #d8fae7;
      background-image: radial-gradient(circle at 100% 0%, #b8f5d0 30%, transparent 60%),
                        radial-gradient(circle at 0% 100%, #c4f7d9 25%, transparent 50%);
    }

    /* Top banner organic glass shapes */
    .purple-banner-bg {
      background: linear-gradient(135deg, #4f22bd 0%, #6830cf 45%, #4614ad 100%);
      position: relative;
      overflow: hidden;
    }
    .purple-banner-bg::before {
      content: "";
      position: absolute;
      top: -60px;
      right: 15%;
      width: 260px;
      height: 260px;
      border-radius: 50%;
      background: radial-gradient(circle, rgba(255,255,255,0.12) 0%, rgba(255,255,255,0) 70%);
      pointer-events: none;
    }
    .purple-banner-bg::after {
      content: "";
      position: absolute;
      bottom: -40px;
      left: 30%;
      width: 220px;
      height: 220px;
      border-radius: 50%;
      background: radial-gradient(circle, rgba(255,255,255,0.08) 0%, rgba(255,255,255,0) 70%);
      pointer-events: none;
    }
  </style>
</head>
<body class="min-h-screen flex text-slate-800 antialiased selection:bg-purple-500 selection:text-white">

  <!-- ================= LEFT SIDEBAR (SUPER FINTI STYLE) ================= -->
  <aside class="w-64 bg-white border-r border-slate-200/80 p-5 flex flex-col justify-between shrink-0 shadow-sm z-30">
    <div class="space-y-6">
      <!-- App Brand Logo -->
      <div class="flex items-center space-x-3 px-2">
        <div class="w-9 h-9 rounded-xl bg-gradient-to-tr from-[#4f22bd] to-[#7e42f5] flex items-center justify-center text-white shadow-md shadow-purple-500/25">
          <i data-lucide="sparkles" class="w-5 h-5"></i>
        </div>
        <div>
          <span class="text-base font-extrabold tracking-tight text-slate-900">AI Influencer</span>
          <span class="block text-[10px] text-purple-600 font-bold uppercase tracking-wider">Marketing Hub</span>
        </div>
      </div>

      <!-- Main Navigation -->
      <div class="space-y-1">
        <p class="text-[11px] font-bold text-slate-400 uppercase tracking-wider px-3 mb-2">Main Navigation</p>
        
        <button onclick="switchTab('overview')" id="nav-btn-overview" class="nav-item w-full flex items-center justify-between px-3 py-2.5 rounded-xl text-xs font-semibold transition-all bg-purple-50 text-purple-700">
          <div class="flex items-center space-x-3">
            <i data-lucide="layout-grid" class="w-4 h-4 text-purple-600"></i>
            <span>Dashboard</span>
          </div>
          <i data-lucide="chevron-right" class="w-3.5 h-3.5 text-purple-400"></i>
        </button>

        <button onclick="switchTab('agents')" id="nav-btn-agents" class="nav-item w-full flex items-center justify-between px-3 py-2.5 rounded-xl text-xs font-medium text-slate-600 hover:bg-slate-50 hover:text-slate-900 transition-all">
          <div class="flex items-center space-x-3">
            <i data-lucide="activity" class="w-4 h-4 text-slate-400"></i>
            <span>Agent & Host Monitor</span>
          </div>
          <span class="text-[10px] bg-emerald-100 text-emerald-700 px-2 py-0.5 rounded-full font-bold flex items-center space-x-1">
            <span class="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
            <span>Live</span>
          </span>
        </button>

        <button onclick="switchTab('publications')" id="nav-btn-publications" class="nav-item w-full flex items-center justify-between px-3 py-2.5 rounded-xl text-xs font-medium text-slate-600 hover:bg-slate-50 hover:text-slate-900 transition-all">
          <div class="flex items-center space-x-3">
            <i data-lucide="video" class="w-4 h-4 text-slate-400"></i>
            <span>TikTok Live Feed</span>
          </div>
          <span id="badge-nav-pubs" class="text-[10px] bg-slate-100 text-slate-600 px-2 py-0.5 rounded-full font-bold">15</span>
        </button>

        <button onclick="switchTab('characters')" id="nav-btn-characters" class="nav-item w-full flex items-center justify-between px-3 py-2.5 rounded-xl text-xs font-medium text-slate-600 hover:bg-slate-50 hover:text-slate-900 transition-all">
          <div class="flex items-center space-x-3">
            <i data-lucide="users" class="w-4 h-4 text-slate-400"></i>
            <span>Talent & Creators</span>
          </div>
          <span class="text-[10px] bg-purple-100 text-purple-700 px-2 py-0.5 rounded-full font-bold">7</span>
        </button>

        <button onclick="switchTab('approvals')" id="nav-btn-approvals" class="nav-item w-full flex items-center justify-between px-3 py-2.5 rounded-xl text-xs font-medium text-slate-600 hover:bg-slate-50 hover:text-slate-900 transition-all">
          <div class="flex items-center space-x-3">
            <i data-lucide="shield-check" class="w-4 h-4 text-slate-400"></i>
            <span>Telegram ACC Gate</span>
          </div>
          <i data-lucide="chevron-right" class="w-3.5 h-3.5 text-slate-300"></i>
        </button>
      </div>

      <!-- Settings & Database Studio -->
      <div class="space-y-1 pt-2 border-t border-slate-100">
        <p class="text-[11px] font-bold text-slate-400 uppercase tracking-wider px-3 mb-2">Metabase & Data Studio</p>

        <button onclick="switchTab('tables')" id="nav-btn-tables" class="nav-item w-full flex items-center justify-between px-3 py-2.5 rounded-xl text-xs font-medium text-slate-600 hover:bg-slate-50 hover:text-slate-900 transition-all">
          <div class="flex items-center space-x-3">
            <i data-lucide="database" class="w-4 h-4 text-slate-400"></i>
            <span>Database Tables</span>
          </div>
          <span class="text-[10px] bg-slate-100 text-slate-600 px-2 py-0.5 rounded-full font-bold">16</span>
        </button>

        <button onclick="switchTab('sql')" id="nav-btn-sql" class="nav-item w-full flex items-center justify-between px-3 py-2.5 rounded-xl text-xs font-medium text-slate-600 hover:bg-slate-50 hover:text-slate-900 transition-all">
          <div class="flex items-center space-x-3">
            <i data-lucide="terminal" class="w-4 h-4 text-slate-400"></i>
            <span>SQL Query Studio</span>
          </div>
          <i data-lucide="chevron-right" class="w-3.5 h-3.5 text-slate-300"></i>
        </button>
      </div>
    </div>

    <!-- Bottom Help / Info Widget Card (like in the user screenshot) -->
    <div class="mt-6 bg-gradient-to-b from-[#fef5e7] to-[#fed99b] rounded-2xl p-4 text-center space-y-2.5 border border-[#fed48f] shadow-sm relative overflow-hidden">
      <div class="w-8 h-8 rounded-full bg-white text-amber-500 font-bold mx-auto flex items-center justify-center shadow-sm text-sm">
        ?
      </div>
      <div>
        <h4 class="text-xs font-bold text-slate-900">Operations Status</h4>
        <p class="text-[10.5px] text-slate-600 leading-snug mt-0.5">Semua pipeline AI Influencer & TikTok Studio aktif normal.</p>
      </div>
      <button onclick="triggerManualRefresh()" class="w-full py-1.5 px-3 bg-white text-slate-900 hover:bg-slate-50 rounded-xl text-xs font-bold shadow-sm transition-all border border-slate-200/50 flex items-center justify-center space-x-1.5">
        <i data-lucide="refresh-cw" class="w-3.5 h-3.5 text-purple-600"></i>
        <span>Sync Database Sekarang</span>
      </button>
    </div>
  </aside>

  <!-- ================= RIGHT MAIN CONTENT AREA ================= -->
  <div class="flex-1 flex flex-col min-w-0 overflow-y-auto custom-scroll">

    <!-- PURPLE GRADIENT TOP HERO HEADER -->
    <section class="purple-banner-bg pt-6 pb-20 px-8 text-white relative">
      <div class="max-w-6xl mx-auto flex flex-col md:flex-row md:items-center justify-between gap-4">
        <!-- Search bar inside purple banner -->
        <div class="relative w-full max-w-xs">
          <i data-lucide="search" class="w-4 h-4 text-purple-200 absolute left-3.5 top-1/2 -translate-y-1/2"></i>
          <input type="text" id="global-search" placeholder="Cari konten, creator, topik..." oninput="handleGlobalSearch(this.value)" class="w-full pl-10 pr-4 py-2 rounded-xl bg-white/15 border border-white/20 text-white placeholder-purple-200 text-xs focus:outline-none focus:bg-white/25 transition-all">
        </div>

        <!-- Top Right Action Links & User Profile -->
        <div class="flex items-center space-x-4 md:space-x-6 text-xs font-medium">
          <!-- Live Auto-Sync Status & Refresh Controls (Cara 3) -->
          <div class="flex items-center space-x-2 bg-white/10 backdrop-blur-md px-3 py-1.5 rounded-xl border border-white/20 text-xs shadow-sm">
            <span class="relative flex h-2.5 w-2.5">
              <span id="live-pulse" class="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span id="live-dot" class="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-400"></span>
            </span>
            <span id="live-status-text" class="text-white font-medium text-[11px] whitespace-nowrap">Auto-Sync 15s</span>
            <button id="btn-toggle-autosync" onclick="toggleAutoSync()" class="px-2 py-0.5 text-[10px] bg-white/20 hover:bg-white/30 rounded text-white font-semibold transition-colors" title="Nyalakan/matikan auto refresh">Jeda</button>
            <button id="btn-manual-refresh" onclick="triggerManualRefresh()" class="p-1 hover:bg-white/20 rounded text-white transition-colors" title="Segarkan sekarang">
              <i data-lucide="refresh-cw" id="icon-refresh" class="w-3.5 h-3.5"></i>
            </button>
            <span id="last-updated-text" class="text-[10px] text-purple-200 hidden sm:inline ml-1 font-mono">Memuat...</span>
          </div>

          <div class="hidden md:flex items-center space-x-4 text-purple-100">
            <span class="hover:text-white cursor-pointer transition-colors" onclick="switchTab('overview')">Ringkasan</span>
            <span class="hover:text-white cursor-pointer transition-colors" onclick="switchTab('publications')">Publikasi Live</span>
            <span class="hover:text-white cursor-pointer transition-colors" onclick="switchTab('tables')">Tabel SQLite</span>
          </div>

          <div class="flex items-center space-x-3 pl-4 border-l border-white/20">
            <div class="text-right">
              <span class="block text-xs font-bold text-white">Hi, Zidane</span>
              <span class="block text-[10px] text-purple-200 font-mono">Owner &bull; Pro</span>
            </div>
            <img src="/assets/FOTO_KARAKTER/PakVincent/pakvincent_profile_avatar.jpg" class="w-9 h-9 rounded-full object-cover border-2 border-white/80 shadow-md">
          </div>
        </div>
      </div>
    </section>

    <!-- FLOATING 3 HERO CARDS OVERLAPPING THE PURPLE BANNER -->
    <div class="max-w-6xl w-full mx-auto px-8 -mt-14 z-20">
      <div class="grid grid-cols-1 md:grid-cols-3 gap-5">
        
        <!-- CARD 1: MINT GREEN (CREATOR IDENTITY) -->
        <div class="mint-wave-bg rounded-2xl p-5 text-slate-800 shadow-md flex flex-col justify-between border border-[#b8f5d0] min-h-[145px]">
          <div class="flex items-center justify-between">
            <div class="w-8 h-8 rounded-lg bg-emerald-800 text-emerald-100 flex items-center justify-center font-black text-xs">
              PV
            </div>
            <span class="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full bg-emerald-800/10 text-emerald-800">BARU LIVE HARI INI</span>
          </div>
          <div>
            <p class="text-[11px] font-bold text-emerald-800 uppercase tracking-wider font-mono">TIKTOK DEBUT VIDEO</p>
            <h3 class="text-base font-extrabold text-slate-900 tracking-tight font-mono">7706823640918019349</h3>
          </div>
          <div class="flex items-center justify-between text-xs border-t border-emerald-800/10 pt-2 text-emerald-900">
            <div>
              <span class="block text-[9px] uppercase font-bold text-emerald-800/70">Creator Name</span>
              <span class="font-bold">Pak Vincent (@pakvincent.riau)</span>
            </div>
            <div class="text-right">
              <span class="block text-[9px] uppercase font-bold text-emerald-800/70">Durasi</span>
              <span class="font-bold">08.04s (1080P)</span>
            </div>
          </div>
        </div>

        <!-- CARD 2: VIBRANT CORAL ORANGE (ACC APPROVAL RATE) -->
        <div class="bg-gradient-to-br from-[#ff6b4a] to-[#ff8469] rounded-2xl p-5 text-white shadow-md flex flex-col justify-between border border-[#ff5a36] min-h-[145px]">
          <div class="flex items-center justify-between">
            <span class="text-xs font-semibold text-white/90">Telegram ACC Status</span>
            <span class="w-5 h-5 rounded-full bg-white/20 flex items-center justify-center text-[10px] font-bold">i</span>
          </div>
          <div class="flex items-center space-x-3.5 my-1">
            <div class="w-11 h-11 rounded-full bg-white flex items-center justify-center text-[#ff6b4a] shadow-sm">
              <i data-lucide="check-check" class="w-6 h-6 stroke-[2.5]"></i>
            </div>
            <div>
              <span class="text-2xl font-black text-white leading-none">100%</span>
              <p class="text-[11px] text-white/90 font-medium mt-0.5">Semua video lolos otorisasi</p>
            </div>
          </div>
          <div class="flex items-center justify-between text-xs border-t border-white/20 pt-2 text-white/90">
            <span>Total Otorisasi: <strong class="text-white">16 ACC</strong></span>
            <span class="text-[10px] bg-white/20 px-2 py-0.5 rounded-full font-bold">Strict 0% Emoji</span>
          </div>
        </div>

        <!-- CARD 3: VIVID CYAN (WORKING FLOW CREDITS) -->
        <div class="bg-gradient-to-br from-[#00d5dc] to-[#25e2e8] rounded-2xl p-5 text-slate-900 shadow-md flex flex-col justify-between border border-[#00c5cc] min-h-[145px]">
          <div class="flex items-center justify-between">
            <span class="text-xs font-bold text-slate-800">Total Working Flow Balance</span>
            <span class="text-[10px] px-2 py-0.5 rounded-md bg-slate-900/10 font-bold uppercase">5 Akun Pro</span>
          </div>
          <div>
            <h2 id="hero-total-credits" class="text-2xl font-black text-slate-950 tracking-tight">2,772 <span class="text-sm font-semibold">KREDIT</span></h2>
            <p class="text-[11px] text-slate-800 font-medium">Resolusi Baku 360p &bull; Varian 3 M4 Upscale</p>
          </div>
          <div class="flex items-center justify-between text-xs border-t border-slate-900/10 pt-2">
            <span class="text-[11px] text-slate-800">Kapasitas Produksi:</span>
            <span class="font-bold text-slate-950">~115 Video Baru</span>
          </div>
        </div>

      </div>
    </div>

    <!-- METABASE ANALYTICS & MICRO-CHARTS ROW -->
    <div class="max-w-6xl w-full mx-auto px-8 mt-6">
      <div class="grid grid-cols-1 md:grid-cols-3 gap-5">
        
        <!-- MICRO CHART 1: PRODUKSI MINGGUAN -->
        <div class="bg-white rounded-2xl p-4 shadow-sm border border-slate-200/70 flex items-center justify-between">
          <div>
            <p class="text-xs text-slate-500 font-medium">Produksi Mingguan</p>
            <div class="flex items-baseline space-x-2 mt-1">
              <span class="text-xl font-extrabold text-slate-900">15 Video</span>
              <span class="text-[10px] font-bold text-emerald-600 bg-emerald-50 px-1.5 py-0.5 rounded-md">+100% ↗</span>
            </div>
            <p class="text-[10px] text-slate-400 mt-0.5">Bulan Berjalan</p>
          </div>
          <!-- Bar visual representation -->
          <div class="flex items-end space-x-1.5 h-12">
            <div class="w-2.5 h-4 bg-slate-100 rounded-t-sm"></div>
            <div class="w-2.5 h-6 bg-slate-200 rounded-t-sm"></div>
            <div class="w-2.5 h-10 bg-gradient-to-t from-orange-500 to-orange-400 rounded-t-sm bar-glow-coral"></div>
            <div class="w-2.5 h-7 bg-orange-200 rounded-t-sm"></div>
            <div class="w-2.5 h-5 bg-slate-100 rounded-t-sm"></div>
          </div>
        </div>

        <!-- MICRO CHART 2: RISET TREN SAWIT & LOKAL -->
        <div class="bg-white rounded-2xl p-4 shadow-sm border border-slate-200/70 flex items-center justify-between">
          <div>
            <p class="text-xs text-slate-500 font-medium">Bank Riset Tren</p>
            <div class="flex items-baseline space-x-2 mt-1">
              <span class="text-xl font-extrabold text-slate-900">68 Topik</span>
              <span class="text-[10px] font-bold text-purple-600 bg-purple-50 px-1.5 py-0.5 rounded-md">Active ↗</span>
            </div>
            <p class="text-[10px] text-slate-400 mt-0.5">Riau, Palembang, Aceh</p>
          </div>
          <!-- Bar visual representation -->
          <div class="flex items-end space-x-1.5 h-12">
            <div class="w-2.5 h-5 bg-slate-100 rounded-t-sm"></div>
            <div class="w-2.5 h-7 bg-purple-200 rounded-t-sm"></div>
            <div class="w-2.5 h-5 bg-purple-300 rounded-t-sm"></div>
            <div class="w-2.5 h-11 bg-gradient-to-t from-purple-600 to-purple-400 rounded-t-sm bar-glow-purple"></div>
            <div class="w-2.5 h-6 bg-slate-100 rounded-t-sm"></div>
          </div>
        </div>

        <!-- MICRO CHART 3: KREDIT PER TALENT -->
        <div class="bg-white rounded-2xl p-4 shadow-sm border border-slate-200/70 flex items-center justify-between">
          <div>
            <p class="text-xs text-slate-500 font-medium">Cadangan Flow Kredit</p>
            <div class="flex items-baseline space-x-2 mt-1">
              <span class="text-xl font-extrabold text-slate-900">5 Akun Pro</span>
              <span class="text-[10px] font-bold text-cyan-600 bg-cyan-50 px-1.5 py-0.5 rounded-md">Healthy</span>
            </div>
            <p class="text-[10px] text-slate-400 mt-0.5">Semua Profil Terisolasi</p>
          </div>
          <!-- Bar visual representation -->
          <div class="flex items-end space-x-1.5 h-12">
            <div class="w-2.5 h-6 bg-slate-100 rounded-t-sm"></div>
            <div class="w-2.5 h-8 bg-cyan-200 rounded-t-sm"></div>
            <div class="w-2.5 h-10 bg-gradient-to-t from-cyan-500 to-cyan-400 rounded-t-sm bar-glow-cyan"></div>
            <div class="w-2.5 h-7 bg-cyan-300 rounded-t-sm"></div>
            <div class="w-2.5 h-5 bg-slate-100 rounded-t-sm"></div>
          </div>
        </div>

      </div>
    </div>

    <!-- MAIN DASHBOARD CONTENT AREA -->
    <main class="max-w-6xl w-full mx-auto px-8 py-6 flex-1">

      <!-- ================= TAB 1: OVERVIEW ================= -->
      <div id="tab-overview" class="tab-content space-y-6">
        
        <!-- COMBINED AGENT HEARTBEAT & HOST HEALTH SUMMARY CARD -->
        <div class="bg-white rounded-3xl p-6 shadow-sm border border-slate-200/70 space-y-4">
          <div class="flex flex-col md:flex-row md:items-center justify-between gap-3 border-b border-slate-100 pb-4">
            <div class="flex items-center space-x-3.5">
              <div class="w-10 h-10 rounded-2xl bg-gradient-to-tr from-purple-600 to-indigo-600 text-white flex items-center justify-center shadow-md shadow-purple-500/20">
                <i data-lucide="activity" class="w-5 h-5"></i>
              </div>
              <div>
                <div class="flex items-center space-x-2">
                  <h3 class="text-base font-extrabold text-slate-900 tracking-tight">Status Agen & Pipeline Produksi Aktif</h3>
                  <span id="overview-host-mode-badge" class="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">
                    <span class="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
                    <span>Host Online</span>
                  </span>
                </div>
                <p class="text-xs text-slate-400">Kombinasi Heartbeat Tugas Karakter (Application Level) & Host Daemon Mac mini (System Level).</p>
              </div>
            </div>
            <div class="flex items-center space-x-2">
              <button onclick="switchTab('agents')" class="px-3.5 py-1.5 bg-purple-50 hover:bg-purple-100 text-purple-700 text-xs font-bold rounded-xl transition-all flex items-center space-x-1.5 border border-purple-200/60 shadow-sm">
                <span>Buka Detail Monitor</span>
                <i data-lucide="arrow-right" class="w-3.5 h-3.5"></i>
              </button>
            </div>
          </div>

          <!-- HOST SERVICE STATUS PILLS -->
          <div class="flex flex-wrap items-center gap-2 pt-1 text-xs" id="overview-host-services-pills">
            <div class="text-xs text-slate-400 flex items-center space-x-1.5 py-1">
              <i data-lucide="loader" class="w-3.5 h-3.5 animate-spin text-purple-600"></i>
              <span>Memuat status daemon...</span>
            </div>
          </div>

          <!-- 4 TALENT PIPELINE PROGRESS MINI CARDS -->
          <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3.5 pt-1" id="overview-talent-pipeline-grid">
            <!-- Dynamically populated from JS -->
          </div>
        </div>

        <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">

          <!-- LEFT COLUMN (2/3): LATEST TRANSACTIONS / TIKTOK POSTS -->
          <div class="lg:col-span-2 bg-white rounded-3xl p-6 shadow-sm border border-slate-200/70 space-y-5">
            <div class="flex items-center justify-between">
              <div>
                <h3 class="text-base font-extrabold text-slate-900 tracking-tight">Postingan TikTok Terkini</h3>
                <p class="text-xs text-slate-400">Daftar video yang telah berhasil dipublikasikan dan live di akun TikTok.</p>
              </div>
              <div class="flex items-center space-x-2 text-slate-400">
                <button onclick="switchTab('publications')" class="p-1.5 hover:bg-slate-100 rounded-lg transition-colors text-xs text-purple-600 font-bold flex items-center space-x-1">
                  <span>Lihat Semua</span>
                  <i data-lucide="arrow-right" class="w-3.5 h-3.5"></i>
                </button>
              </div>
            </div>

            <!-- Date Grouped Items -->
            <div class="space-y-4" id="overview-transactions-list">
              <!-- Dynamically populated -->
            </div>
          </div>

          <!-- RIGHT COLUMN (1/3): UPCOMING TRANSACTIONS / SCHEDULED SLOTS -->
          <div class="bg-white rounded-3xl p-6 shadow-sm border border-slate-200/70 space-y-5 flex flex-col justify-between">
            <div class="space-y-4">
              <div class="flex items-center justify-between">
                <div>
                  <h3 class="text-base font-extrabold text-slate-900 tracking-tight">Jadwal Harian Baku</h3>
                  <p class="text-xs text-slate-400">SOP Produksi & Penayangan</p>
                </div>
                <span class="text-[11px] text-purple-600 font-bold bg-purple-50 px-2.5 py-1 rounded-full">Slot Rutin</span>
              </div>

              <div class="space-y-3.5 text-xs">
                <!-- Schedule item 1: Dinda -->
                <div class="flex items-center justify-between p-3 rounded-2xl bg-slate-50 border border-slate-100">
                  <div class="flex items-center space-x-3">
                    <div class="w-9 h-9 rounded-xl bg-purple-600 text-white flex items-center justify-center font-bold text-xs shadow-sm">
                      DK
                    </div>
                    <div>
                      <h4 class="font-bold text-slate-900">Dinda Kemala</h4>
                      <p class="text-[11px] text-slate-500">Palembang &bull; Vlog Burgo</p>
                    </div>
                  </div>
                  <div class="text-right">
                    <span class="font-bold text-slate-900 block">11:30 WIB</span>
                    <span class="text-[10px] text-emerald-600 font-semibold">Live Done</span>
                  </div>
                </div>

                <!-- Schedule item 2: ISK -->
                <div class="flex items-center justify-between p-3 rounded-2xl bg-slate-50 border border-slate-100">
                  <div class="flex items-center space-x-3">
                    <div class="w-9 h-9 rounded-xl bg-rose-500 text-white flex items-center justify-center font-bold text-xs shadow-sm">
                      IK
                    </div>
                    <div>
                      <h4 class="font-bold text-slate-900">PT Intan Suar Kartika</h4>
                      <p class="text-[11px] text-slate-500">Proyek &bull; Safety Officer</p>
                    </div>
                  </div>
                  <div class="text-right">
                    <span class="font-bold text-slate-900 block">13:00 WIB</span>
                    <span class="text-[10px] text-emerald-600 font-semibold">Live Done</span>
                  </div>
                </div>

                <!-- Schedule item 3: Bang Ray -->
                <div class="flex items-center justify-between p-3 rounded-2xl bg-slate-50 border border-slate-100">
                  <div class="flex items-center space-x-3">
                    <div class="w-9 h-9 rounded-xl bg-blue-500 text-white flex items-center justify-center font-bold text-xs shadow-sm">
                      BR
                    </div>
                    <div>
                      <h4 class="font-bold text-slate-900">Bang Ray</h4>
                      <p class="text-[11px] text-slate-500">Aceh &bull; Edukasi Bangunan</p>
                    </div>
                  </div>
                  <div class="text-right">
                    <span class="font-bold text-slate-900 block">16:00 WIB</span>
                    <span class="text-[10px] text-emerald-600 font-semibold">Live Done</span>
                  </div>
                </div>

                <!-- Schedule item 4: Pak Vincent -->
                <div class="flex items-center justify-between p-3 rounded-2xl bg-amber-50/60 border border-amber-100">
                  <div class="flex items-center space-x-3">
                    <div class="w-9 h-9 rounded-xl bg-emerald-600 text-white flex items-center justify-center font-bold text-xs shadow-sm">
                      PV
                    </div>
                    <div>
                      <h4 class="font-bold text-slate-900">Pak Vincent</h4>
                      <p class="text-[11px] text-slate-500">Riau &bull; Kebun Sawit</p>
                    </div>
                  </div>
                  <div class="text-right">
                    <span class="font-bold text-slate-900 block">18:00 WIB</span>
                    <span class="text-[10px] text-emerald-600 font-semibold">Live Done</span>
                  </div>
                </div>
              </div>
            </div>

            <!-- Flow Accounts Mini Summary -->
            <div class="pt-4 border-t border-slate-100">
              <span class="text-[11px] font-bold text-slate-400 uppercase tracking-wider block mb-2">Akun Google Flow</span>
              <div class="grid grid-cols-2 gap-2 text-xs">
                <div class="p-2 bg-slate-50 rounded-xl">
                  <span class="text-[10px] text-slate-500 block">flow_3 (Bang Ray)</span>
                  <span class="font-bold text-purple-700 font-mono">1,026 Kredit</span>
                </div>
                <div class="p-2 bg-slate-50 rounded-xl">
                  <span class="text-[10px] text-slate-500 block">flow_2 (ISK)</span>
                  <span class="font-bold text-purple-700 font-mono">710 Kredit</span>
                </div>
              </div>
            </div>
          </div>

        </div>
      </div>

      <!-- ================= TAB: AGENT & HOST MONITOR (COMBINED APPROACH 1 & 2) ================= -->
      <div id="tab-agents" class="tab-content hidden space-y-6">

        <!-- 1. SYSTEM LEVEL: HOST SERVER & DAEMON HEALTH (APPROACH 2) -->
        <div class="bg-white rounded-3xl p-6 shadow-sm border border-slate-200/70 space-y-5">
          <div class="flex flex-col md:flex-row md:items-center justify-between gap-3 border-b border-slate-100 pb-4">
            <div class="flex items-center space-x-3.5">
              <div class="w-10 h-10 rounded-2xl bg-gradient-to-tr from-purple-600 to-indigo-600 text-white flex items-center justify-center shadow-md shadow-purple-500/20">
                <i data-lucide="cpu" class="w-5 h-5"></i>
              </div>
              <div>
                <div class="flex items-center space-x-2">
                  <h3 class="text-base font-extrabold text-slate-900 tracking-tight">Host Server & Daemon Health</h3>
                  <span id="agents-env-badge" class="text-[10px] font-mono px-2 py-0.5 rounded-md bg-purple-100 text-purple-800 font-bold uppercase">Local Host</span>
                </div>
                <p class="text-xs text-slate-400">Monitoring level sistem untuk daemon latar belakang Mac mini Apple M4 & sinkronisasi cloud.</p>
              </div>
            </div>
            <div class="flex items-center space-x-3 text-xs">
              <span id="agents-server-time" class="text-slate-500 font-mono text-[11px] bg-slate-50 border border-slate-100 px-3 py-1.5 rounded-xl">-</span>
              <button onclick="loadAgentsStatus(true)" class="p-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl transition-colors flex items-center space-x-1 font-bold" title="Segarkan status host">
                <i data-lucide="refresh-cw" id="icon-refresh-agents" class="w-3.5 h-3.5 text-purple-600"></i>
                <span class="text-xs">Segarkan</span>
              </button>
            </div>
          </div>

          <!-- HARDWARE METRICS SUMMARY -->
          <div class="grid grid-cols-2 sm:grid-cols-4 gap-3.5" id="agents-hardware-metrics">
            <div class="p-4 rounded-2xl bg-slate-50 border border-slate-100/80 space-y-1">
              <span class="text-[10px] text-slate-400 uppercase font-bold tracking-wider block">Chipset & OS</span>
              <span class="text-xs font-bold text-slate-900 block truncate" id="hw-chip">Apple M4 Mac mini</span>
              <span class="text-[10px] text-slate-500 block truncate" id="hw-plat">Darwin arm64</span>
            </div>
            <div class="p-4 rounded-2xl bg-slate-50 border border-slate-100/80 space-y-1">
              <span class="text-[10px] text-slate-400 uppercase font-bold tracking-wider block">CPU Load (1m, 5m, 15m)</span>
              <span class="text-xs font-bold text-slate-900 block font-mono" id="hw-cpu">-</span>
              <span class="text-[10px] text-emerald-600 font-semibold block">Multi-core Optimal</span>
            </div>
            <div class="p-4 rounded-2xl bg-slate-50 border border-slate-100/80 space-y-1">
              <span class="text-[10px] text-slate-400 uppercase font-bold tracking-wider block">Memori Sistem</span>
              <span class="text-xs font-bold text-slate-900 block font-mono" id="hw-ram">16.0 GB RAM</span>
              <span class="text-[10px] text-slate-500 block">Unified Architecture</span>
            </div>
            <div class="p-4 rounded-2xl bg-slate-50 border border-slate-100/80 space-y-1">
              <span class="text-[10px] text-slate-400 uppercase font-bold tracking-wider block">Ruang Disk Rendisi</span>
              <span class="text-xs font-bold text-slate-900 block font-mono" id="hw-disk">- GB Bebas</span>
              <span class="text-[10px] text-slate-500 block" id="hw-disk-pct">Kapasitas Aman</span>
            </div>
          </div>

          <!-- SERVICES GRID -->
          <div class="space-y-3 pt-2">
            <div class="flex items-center justify-between">
              <h4 class="text-xs font-bold text-slate-500 uppercase tracking-wider">Layanan Host & Daemon Latar Belakang (Mac mini)</h4>
              <span class="text-[10px] text-slate-400">6 Layanan Terpantau</span>
            </div>
            <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3.5" id="agents-services-grid">
              <!-- Dynamically populated -->
            </div>
          </div>
        </div>

        <!-- 2. APPLICATION LEVEL: CHARACTER TASK HEARTBEAT & PIPELINE (APPROACH 1) -->
        <div class="bg-white rounded-3xl p-6 shadow-sm border border-slate-200/70 space-y-5">
          <div class="flex flex-col md:flex-row md:items-center justify-between gap-3 border-b border-slate-100 pb-4">
            <div class="flex items-center space-x-3.5">
              <div class="w-10 h-10 rounded-2xl bg-gradient-to-tr from-emerald-500 to-teal-600 text-white flex items-center justify-center shadow-md shadow-emerald-500/20">
                <i data-lucide="git-commit" class="w-5 h-5"></i>
              </div>
              <div>
                <h3 class="text-base font-extrabold text-slate-900 tracking-tight">Heartbeat Pipeline Produksi Karakter</h3>
                <p class="text-xs text-slate-400">Status aktual 5 tahapan produksi video tiap talent dari perencanaan hingga tayang TikTok.</p>
              </div>
            </div>
            <div class="flex items-center space-x-2 text-xs">
              <span class="px-3 py-1 rounded-xl bg-purple-50 text-purple-700 font-bold border border-purple-200/60 font-mono">Durasi: 10s - 18s</span>
              <span class="px-3 py-1 rounded-xl bg-emerald-50 text-emerald-700 font-bold border border-emerald-200/60 font-mono">4 Slot Baku Harian</span>
            </div>
          </div>

          <!-- 4 DETAILED PIPELINE CARDS -->
          <div class="space-y-4" id="agents-pipeline-detailed-list">
            <!-- Dynamically populated from JS -->
          </div>
        </div>

      </div>

      <!-- ================= TAB 2: TALENT & CREATORS ================= -->
      <div id="tab-characters" class="tab-content hidden space-y-6">
        <div class="bg-white rounded-3xl p-6 shadow-sm border border-slate-200/70 space-y-4">
          <div class="flex items-center justify-between">
            <div>
              <h3 class="text-base font-extrabold text-slate-900 tracking-tight">Karakter & Talent Media Sosial</h3>
              <p class="text-xs text-slate-400">Daftar lengkap 7 profil agen AI dengan persona, domisili, niche, dan akun TikTok.</p>
            </div>
            <span class="text-xs font-bold bg-purple-50 text-purple-700 px-3 py-1 rounded-full">7 Talent Terdaftar</span>
          </div>
          <div id="creators-grid" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5 pt-2">
            <!-- Dynamically injected -->
          </div>
        </div>
      </div>

      <!-- ================= TAB 3: PUBLICATIONS ================= -->
      <div id="tab-publications" class="tab-content hidden space-y-6">
        <div class="bg-white rounded-3xl p-6 shadow-sm border border-slate-200/70 space-y-5">
          <div class="flex flex-col md:flex-row md:items-center justify-between gap-3">
            <div>
              <h3 class="text-base font-extrabold text-slate-900 tracking-tight">Feed Publikasi Live TikTok</h3>
              <p class="text-xs text-slate-400">Seluruh konten yang telah lolos ACC Telegram Owner dan terbit di TikTok Studio.</p>
            </div>
            <div class="flex items-center space-x-3">
              <select id="pubs-filter-char" onchange="filterPubs()" class="text-xs font-semibold bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 text-slate-700 focus:outline-none focus:border-purple-500">
                <option value="">Semua Talent</option>
                <option value="pak_vincent">Pak Vincent (@pakvincent.riau)</option>
                <option value="bang_ray">Bang Ray (@teuku.rayyan00)</option>
                <option value="dinda">Dinda Kemala (@dinda.kemala_)</option>
                <option value="isk">ISK (@intansuarkartika)</option>
              </select>
            </div>
          </div>

          <div class="overflow-x-auto custom-scroll">
            <table class="w-full text-left text-xs border-collapse">
              <thead>
                <tr class="border-b border-slate-100 text-slate-400 uppercase tracking-wider text-[10px]">
                  <th class="py-3 px-4">Talent</th>
                  <th class="py-3 px-4">Post ID & Tautan Video</th>
                  <th class="py-3 px-4">Waktu Publikasi</th>
                  <th class="py-3 px-4">Status</th>
                  <th class="py-3 px-4">Naskah Naratif (0% Emoji)</th>
                  <th class="py-3 px-4 text-right">Aksi</th>
                </tr>
              </thead>
              <tbody id="pubs-full-tbody" class="divide-y divide-slate-100 text-slate-700">
                <!-- Dynamically populated -->
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <!-- ================= TAB 4: APPROVALS ================= -->
      <div id="tab-approvals" class="tab-content hidden space-y-6">
        <div class="bg-white rounded-3xl p-6 shadow-sm border border-slate-200/70 space-y-5">
          <div class="flex items-center justify-between">
            <div>
              <h3 class="text-base font-extrabold text-slate-900 tracking-tight">Log Otorisasi ACC Telegram Owner</h3>
              <p class="text-xs text-slate-400">Audit trail persetujuan sebelum video dipublikasikan ke TikTok.</p>
            </div>
            <span class="text-xs font-bold bg-emerald-50 text-emerald-700 px-3 py-1 rounded-full">Gate Terverifikasi</span>
          </div>

          <div class="overflow-x-auto custom-scroll">
            <table class="w-full text-left text-xs border-collapse">
              <thead>
                <tr class="border-b border-slate-100 text-slate-400 uppercase tracking-wider text-[10px]">
                  <th class="py-3 px-4">Talent</th>
                  <th class="py-3 px-4">Keputusan</th>
                  <th class="py-3 px-4">Reviewer ID</th>
                  <th class="py-3 px-4">Kanal</th>
                  <th class="py-3 px-4">Waktu Keputusan</th>
                  <th class="py-3 px-4">Version ID</th>
                </tr>
              </thead>
              <tbody id="approvals-full-tbody" class="divide-y divide-slate-100 text-slate-700">
                <!-- Dynamically populated -->
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <!-- ================= TAB 5: DATABASE TABLES ================= -->
      <div id="tab-tables" class="tab-content hidden space-y-6">
        <div class="bg-white rounded-3xl p-6 shadow-sm border border-slate-200/70 space-y-5">
          <div class="flex flex-col md:flex-row md:items-center justify-between gap-3">
            <div>
              <h3 class="text-base font-extrabold text-slate-900 tracking-tight">Metabase Table Browser</h3>
              <p class="text-xs text-slate-400">Jelajahi dan telusuri seluruh 16 tabel dalam database <code>production.sqlite</code>.</p>
            </div>
            <div class="flex items-center space-x-3">
              <select id="tables-dropdown" onchange="loadSelectedTable()" class="text-xs font-semibold bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 text-slate-700 focus:outline-none focus:border-purple-500">
                <!-- Injected dynamically -->
              </select>
              <input type="text" id="table-search-input" placeholder="Cari dalam tabel..." oninput="debounceTableSearch()" class="text-xs bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 text-slate-700 placeholder-slate-400 focus:outline-none focus:border-purple-500 w-44">
            </div>
          </div>

          <div class="border border-slate-200 rounded-2xl overflow-hidden">
            <div class="p-3 bg-slate-50 border-b border-slate-200 flex items-center justify-between text-xs text-slate-500">
              <span id="table-stats-info">Memuat data...</span>
              <div class="flex items-center space-x-2">
                <button onclick="prevTablePage()" id="table-btn-prev" class="px-3 py-1 bg-white border border-slate-200 rounded-lg text-slate-700 hover:bg-slate-100 disabled:opacity-40 font-bold">&larr; Prev</button>
                <span id="table-page-number" class="font-mono text-xs font-bold text-slate-700">1 / 1</span>
                <button onclick="nextTablePage()" id="table-btn-next" class="px-3 py-1 bg-white border border-slate-200 rounded-lg text-slate-700 hover:bg-slate-100 disabled:opacity-40 font-bold">Next &rarr;</button>
              </div>
            </div>

            <div class="overflow-x-auto custom-scroll max-h-[550px]">
              <table class="w-full text-left text-xs border-collapse">
                <thead id="browser-thead" class="bg-slate-100/80 sticky top-0 border-b border-slate-200 text-slate-600 font-bold text-[10.5px]"></thead>
                <tbody id="browser-tbody" class="divide-y divide-slate-100 font-mono text-[11px] text-slate-700"></tbody>
              </table>
            </div>
          </div>
        </div>
      </div>

      <!-- ================= TAB 6: SQL QUERY STUDIO ================= -->
      <div id="tab-sql" class="tab-content hidden space-y-6">
        <div class="bg-white rounded-3xl p-6 shadow-sm border border-slate-200/70 space-y-4">
          <div class="flex items-center justify-between">
            <div>
              <h3 class="text-base font-extrabold text-slate-900 tracking-tight">Metabase SQL Query Studio</h3>
              <p class="text-xs text-slate-400">Jalankan kueri baca SQL (SELECT / PRAGMA) secara aman langsung dari browser.</p>
            </div>
            <span class="text-xs font-mono font-bold text-purple-700 bg-purple-50 px-2.5 py-1 rounded-lg">SQLite 3 Read-Only</span>
          </div>

          <!-- Query presets -->
          <div class="flex flex-wrap gap-2 text-xs">
            <span class="text-slate-400 py-1 font-medium">Contoh Kueri:</span>
            <button onclick="applySqlPreset('SELECT p.id, ch.name, p.platform_post_id, p.post_url, p.confirmed_at FROM publications p JOIN versions v ON p.version_id=v.id JOIN content c ON v.content_id=c.id JOIN characters ch ON c.character_id=ch.id ORDER BY p.ROWID DESC;')" class="px-3 py-1 bg-slate-50 hover:bg-slate-100 border border-slate-200 rounded-lg text-slate-700 font-medium transition-colors">Daftar Publikasi</button>
            <button onclick="applySqlPreset('SELECT c.character_id, count(*) as total_posts FROM publications p JOIN versions v ON p.version_id=v.id JOIN content c ON v.content_id=c.id GROUP BY c.character_id;')" class="px-3 py-1 bg-slate-50 hover:bg-slate-100 border border-slate-200 rounded-lg text-slate-700 font-medium transition-colors">Total Post per Talent</button>
            <button onclick="applySqlPreset('SELECT topic, category, platform, trend_score, created_at FROM trend_memory ORDER BY ROWID DESC LIMIT 15;')" class="px-3 py-1 bg-slate-50 hover:bg-slate-100 border border-slate-200 rounded-lg text-slate-700 font-medium transition-colors">Riset Tren Sawit/Lokal</button>
            <button onclick="applySqlPreset('SELECT * FROM generation_jobs ORDER BY ROWID DESC LIMIT 10;')" class="px-3 py-1 bg-slate-50 hover:bg-slate-100 border border-slate-200 rounded-lg text-slate-700 font-medium transition-colors">Job Flow 360p</button>
          </div>

          <div class="space-y-2">
            <textarea id="sql-editor" rows="4" class="w-full bg-slate-900 text-emerald-400 font-mono text-xs p-4 rounded-2xl focus:outline-none focus:ring-2 focus:ring-purple-500 custom-scroll" placeholder="Ketik SELECT query di sini...">SELECT * FROM publications ORDER BY ROWID DESC LIMIT 10;</textarea>
            <div class="flex items-center justify-between">
              <span id="sql-error-msg" class="text-xs text-rose-500 font-semibold"></span>
              <button onclick="executeSqlQuery()" class="px-5 py-2 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 text-white font-bold rounded-xl text-xs shadow-md shadow-purple-500/20 transition-all flex items-center space-x-1.5">
                <i data-lucide="play" class="w-3.5 h-3.5 fill-current"></i>
                <span>Jalankan Kueri</span>
              </button>
            </div>
          </div>

          <!-- SQL Result Table -->
          <div id="sql-result-wrapper" class="hidden border border-slate-200 rounded-2xl overflow-hidden mt-4">
            <div class="p-3 bg-slate-50 border-b border-slate-200 flex items-center justify-between text-xs text-slate-600">
              <span id="sql-row-count" class="font-bold">0 hasil</span>
              <button onclick="downloadSqlJson()" class="text-purple-600 hover:underline font-bold">Unduh JSON</button>
            </div>
            <div class="overflow-x-auto custom-scroll max-h-[500px]">
              <table class="w-full text-left text-xs border-collapse">
                <thead id="sql-thead" class="bg-slate-100 sticky top-0 border-b border-slate-200 text-slate-600 font-bold text-[10.5px]"></thead>
                <tbody id="sql-tbody" class="divide-y divide-slate-100 font-mono text-[11px] text-slate-700"></tbody>
              </table>
            </div>
          </div>
        </div>
      </div>

    </main>

  </div>

  <!-- MODAL FOR FULL CAPTION -->
  <div id="caption-modal" class="hidden fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4">
    <div class="bg-white rounded-3xl p-6 max-w-lg w-full shadow-2xl space-y-4 border border-slate-100">
      <div class="flex items-center justify-between border-b border-slate-100 pb-3">
        <div class="flex items-center space-x-2.5">
          <div class="w-8 h-8 rounded-xl bg-purple-100 text-purple-700 flex items-center justify-center font-bold text-xs">
            <i data-lucide="file-text" class="w-4 h-4"></i>
          </div>
          <div>
            <h3 id="modal-char-title" class="font-bold text-slate-900 text-sm">Naskah Konten</h3>
            <span class="text-[10px] text-slate-400">ACC Approved &bull; 0% Emoji</span>
          </div>
        </div>
        <button onclick="closeCaptionModal()" class="w-8 h-8 rounded-full bg-slate-100 hover:bg-slate-200 text-slate-500 flex items-center justify-center text-sm transition-colors">&times;</button>
      </div>

      <div class="space-y-1">
        <label class="text-[11px] font-bold text-slate-400 uppercase tracking-wider block">Teks Caption TikTok:</label>
        <div id="modal-caption-content" class="bg-slate-50 border border-slate-200 rounded-2xl p-4 text-xs text-slate-700 leading-relaxed max-h-60 overflow-y-auto custom-scroll whitespace-pre-wrap"></div>
      </div>

      <div class="flex items-center justify-between pt-2 border-t border-slate-100 text-xs text-slate-500">
        <span id="modal-char-counter">0 karakter</span>
        <button onclick="copyCaptionText()" id="btn-copy-caption" class="px-4 py-1.5 bg-purple-600 hover:bg-purple-700 text-white rounded-xl text-xs font-bold transition-all shadow-sm">
          Salin Teks
        </button>
      </div>
    </div>
  </div>

  <!-- JAVASCRIPT LOGIC -->
  <script>
    let activeTab = 'overview';
    let currentSelectedTable = 'characters';
    let tablePagingOffset = 0;
    const tablePagingLimit = 50;
    let tableSearchTimer = null;
    let sqlExportData = [];

    // AUTO-SYNC & LIVE POLLING CONFIGURATION (CARA 3)
    let autoSyncInterval = 15000; // polling setiap 15 detik
    let autoSyncTimer = null;
    let isAutoSyncEnabled = true;
    let isRefreshing = false;

    function setLastUpdated() {
      const now = new Date();
      const timeStr = now.toLocaleTimeString('id-ID', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
      const el = document.getElementById('last-updated-text');
      if (el) el.innerText = timeStr;
    }

    async function triggerManualRefresh() {
      const icon = document.getElementById('icon-refresh');
      if (icon) icon.classList.add('animate-spin');
      await performRefresh();
      setTimeout(() => {
        if (icon) icon.classList.remove('animate-spin');
      }, 700);
    }

    async function performRefresh() {
      if (isRefreshing) return;
      isRefreshing = true;
      try {
        await refreshData();
        if (activeTab === 'agents') await loadAgentsStatus();
        else if (activeTab === 'characters') await loadCreators();
        else if (activeTab === 'publications') await loadFullPublications();
        else if (activeTab === 'approvals') await loadFullApprovals();
        else if (activeTab === 'tables') {
          // Hanya refresh tabel jika input search tidak sedang difokuskan pengguna
          const searchInput = document.getElementById('table-search-input');
          if (document.activeElement !== searchInput) {
            await loadSelectedTable();
          }
        }
        setLastUpdated();
      } catch (err) {
        console.error("Auto-sync performRefresh error:", err);
      } finally {
        isRefreshing = false;
      }
    }

    function startAutoSync() {
      if (autoSyncTimer) clearInterval(autoSyncTimer);
      if (!isAutoSyncEnabled) return;
      autoSyncTimer = setInterval(async () => {
        // Hanya fetch jika tab browser sedang aktif/dilihat
        if (!document.hidden) {
          await performRefresh();
        }
      }, autoSyncInterval);
    }

    function toggleAutoSync() {
      isAutoSyncEnabled = !isAutoSyncEnabled;
      const pulse = document.getElementById('live-pulse');
      const dot = document.getElementById('live-dot');
      const statusText = document.getElementById('live-status-text');
      const btnToggle = document.getElementById('btn-toggle-autosync');

      if (isAutoSyncEnabled) {
        if (pulse) pulse.classList.remove('hidden');
        if (dot) { dot.classList.remove('bg-slate-400'); dot.classList.add('bg-emerald-400'); }
        if (statusText) statusText.innerText = 'Auto-Sync 15s';
        if (btnToggle) btnToggle.innerText = 'Jeda';
        startAutoSync();
        performRefresh();
      } else {
        if (pulse) pulse.classList.add('hidden');
        if (dot) { dot.classList.remove('bg-emerald-400'); dot.classList.add('bg-slate-400'); }
        if (statusText) statusText.innerText = 'Auto-Sync: Jeda';
        if (btnToggle) btnToggle.innerText = 'Mulai';
        if (autoSyncTimer) clearInterval(autoSyncTimer);
      }
    }

    async function initApp() {
      await performRefresh();
      await loadTableDropdownOptions();
      startAutoSync();
      lucide.createIcons();
    }

    function switchTab(tabId) {
      document.querySelectorAll('.tab-content').forEach(el => el.classList.add('hidden'));
      document.querySelectorAll('.nav-item').forEach(btn => {
        btn.classList.remove('bg-purple-50', 'text-purple-700');
        btn.classList.add('text-slate-600');
      });

      const target = document.getElementById('tab-' + tabId);
      const navBtn = document.getElementById('nav-btn-' + tabId);
      if (target) target.classList.remove('hidden');
      if (navBtn) {
        navBtn.classList.remove('text-slate-600');
        navBtn.classList.add('bg-purple-50', 'text-purple-700');
      }
      activeTab = tabId;

      if (tabId === 'agents') loadAgentsStatus();
      if (tabId === 'characters') loadCreators();
      if (tabId === 'publications') loadFullPublications();
      if (tabId === 'approvals') loadFullApprovals();
      if (tabId === 'tables') loadSelectedTable();
      lucide.createIcons();
    }

    async function refreshData() {
      try {
        const res = await fetch('/api/overview');
        const data = await res.json();

        // Hero credits
        document.getElementById('hero-total-credits').innerHTML = `${Number(data.total_credits).toLocaleString()} <span class="text-sm font-semibold">KREDIT</span>`;
        document.getElementById('badge-nav-pubs').innerText = data.counts.publications || 0;

        // Render agents status in overview if available
        if (data.agents_status) {
          renderOverviewAgents(data.agents_status);
        }

        // Render transactions list
        const txContainer = document.getElementById('overview-transactions-list');
        const todayDateStr = new Date().toLocaleDateString('id-ID', { weekday: 'long', day: 'numeric', month: 'short', year: 'numeric' });
        txContainer.innerHTML = `
          <div>
            <span class="text-[11px] font-bold text-slate-400 block mb-2">${todayDateStr}</span>
            <div class="space-y-2">
              ${data.recent_publications.slice(0, 5).map(p => `
                <div class="flex items-center justify-between p-3 rounded-2xl hover:bg-slate-50 transition-colors border border-transparent hover:border-slate-100">
                  <div class="flex items-center space-x-3.5">
                    <div class="w-10 h-10 rounded-xl bg-purple-50 text-purple-600 flex items-center justify-center">
                      <i data-lucide="arrow-up-right" class="w-5 h-5"></i>
                    </div>
                    <div>
                      <h4 class="font-bold text-xs text-slate-900">${p.character_name || p.character_id} &bull; <span class="text-slate-500 font-mono">${p.account || ''}</span></h4>
                      <p class="text-[11px] text-slate-400 truncate max-w-sm mt-0.5">${p.caption ? p.caption.slice(0, 75) + '...' : 'Video terbit'}</p>
                    </div>
                  </div>
                  <div class="flex items-center space-x-3">
                    <span class="font-mono text-xs font-bold text-slate-900">${p.platform_post_id}</span>
                    ${p.post_url ? `
                      <a href="${p.post_url}" target="_blank" class="p-1.5 rounded-lg bg-slate-100 hover:bg-purple-100 text-purple-700 transition-colors" title="Buka TikTok">
                        <i data-lucide="external-link" class="w-3.5 h-3.5"></i>
                      </a>
                    ` : ''}
                    <button onclick='openCaptionModal("${escapeJs(p.character_name)}", "${escapeJs(p.caption)}")' class="px-2 py-1 bg-slate-100 hover:bg-slate-200 rounded-lg text-[11px] font-semibold text-slate-600">
                      Naskah
                    </button>
                  </div>
                </div>
              `).join('')}
            </div>
          </div>
        `;
        lucide.createIcons();
      } catch (e) {
        console.error("Failed to load overview:", e);
      }
    }

    function renderOverviewAgents(data) {
      if (!data || !data.host_status) return;

      // 1. Host Mode Badge
      const hostModeEl = document.getElementById('overview-host-mode-badge');
      if (hostModeEl) {
        if (data.host_status.is_cloud) {
          hostModeEl.innerHTML = `<span class="w-1.5 h-1.5 rounded-full bg-indigo-500 animate-pulse"></span><span>Vercel Cloud Mirror</span>`;
          hostModeEl.className = 'inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-indigo-50 text-indigo-700 border border-indigo-200';
        } else {
          hostModeEl.innerHTML = `<span class="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span><span>Mac mini Host Live</span>`;
          hostModeEl.className = 'inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200';
        }
      }

      // 2. Host Services Pills
      const pillsContainer = document.getElementById('overview-host-services-pills');
      if (pillsContainer && data.host_status.services) {
        pillsContainer.innerHTML = data.host_status.services.map(s => {
          const isOnline = s.status === 'online';
          const dotColor = isOnline ? 'bg-emerald-500 animate-pulse' : (s.status === 'standby' ? 'bg-slate-400' : 'bg-rose-500');
          const badgeBg = isOnline ? 'bg-emerald-50 text-emerald-800 border-emerald-200/70' : (s.status === 'standby' ? 'bg-slate-50 text-slate-700 border-slate-200' : 'bg-rose-50 text-rose-700 border-rose-200');
          return `
            <span class="inline-flex items-center space-x-1.5 px-2.5 py-1 rounded-xl text-[11px] font-semibold ${badgeBg} border shadow-xs" title="${escapeHtml(s.details || '')}">
              <span class="w-2 h-2 rounded-full ${dotColor}"></span>
              <span class="font-bold">${s.name}:</span>
              <span class="font-mono text-[10px]">${s.status.toUpperCase()} ${s.port ? `(:${s.port})` : (s.pid ? `(PID ${s.pid})` : '')}</span>
            </span>
          `;
        }).join('');
      }

      // 3. 4-Talent Mini Cards
      const talentGrid = document.getElementById('overview-talent-pipeline-grid');
      if (talentGrid && data.pipeline_tasks) {
        talentGrid.innerHTML = data.pipeline_tasks.map(t => {
          const isDone = t.progress_percent === 100;
          const isRunning = t.status_tag === 'running';
          const isReview = t.status_tag === 'review';
          const borderStyle = isDone ? 'border-emerald-200 bg-emerald-50/40' : (isRunning ? 'border-purple-200 bg-purple-50/40' : (isReview ? 'border-amber-200 bg-amber-50/40' : 'border-slate-100 bg-slate-50/70'));
          const badgeStyle = isDone ? 'bg-emerald-100 text-emerald-800' : (isRunning ? 'bg-purple-100 text-purple-800' : (isReview ? 'bg-amber-100 text-amber-800' : 'bg-slate-100 text-slate-600'));
          
          return `
            <div onclick="switchTab('agents')" class="p-3.5 rounded-2xl border ${borderStyle} hover:shadow-md transition-all cursor-pointer flex flex-col justify-between space-y-2">
              <div class="flex items-center justify-between">
                <div class="flex items-center space-x-2">
                  ${t.avatar_url ? `
                    <img src="${t.avatar_url}" class="w-7 h-7 rounded-lg object-cover border border-white shadow-xs">
                  ` : `
                    <div class="w-7 h-7 rounded-lg bg-purple-600 text-white font-bold flex items-center justify-center text-xs shadow-xs">
                      ${t.character_name[0]}
                    </div>
                  `}
                  <div>
                    <h5 class="font-bold text-slate-900 text-xs">${t.character_name.split(' ')[0]}</h5>
                    <span class="text-[10px] text-slate-500 font-mono">${t.slot_time}</span>
                  </div>
                </div>
                <span class="text-[9.5px] font-bold px-2 py-0.5 rounded-md ${badgeStyle}">
                  ${t.stages[t.active_step - 1]?.short || 'Step ' + t.active_step}
                </span>
              </div>

              <div>
                <p class="text-[11px] text-slate-700 font-medium leading-snug line-clamp-2">${t.headline_status}</p>
              </div>

              <div class="space-y-1 pt-1 border-t border-slate-200/50">
                <div class="flex items-center justify-between text-[10px] font-mono text-slate-500">
                  <span>Step ${t.active_step}/5</span>
                  <span class="font-bold text-slate-700">${t.progress_percent}%</span>
                </div>
                <div class="w-full bg-slate-200/80 rounded-full h-1.5 overflow-hidden">
                  <div class="h-full bg-gradient-to-r from-purple-600 to-indigo-600 rounded-full transition-all duration-500" style="width: ${t.progress_percent}%"></div>
                </div>
              </div>
            </div>
          `;
        }).join('');
      }
      lucide.createIcons();
    }

    async function loadAgentsStatus(isManual = false) {
      const icon = document.getElementById('icon-refresh-agents');
      if (icon) icon.classList.add('animate-spin');
      try {
        const res = await fetch('/api/agents_status');
        const data = await res.json();
        if (data.status !== 'success') return;

        // Render Overview mini summary
        renderOverviewAgents(data);

        // Hardware & Platform
        const host = data.host_status;
        const metrics = host?.host_metrics || {};
        const envBadge = document.getElementById('agents-env-badge');
        if (envBadge) {
          envBadge.innerText = host.is_cloud ? 'Vercel Cloud Mirror' : 'Local Mac mini Host';
          envBadge.className = `text-[10px] font-mono px-2.5 py-0.5 rounded-md font-bold uppercase ${host.is_cloud ? 'bg-indigo-100 text-indigo-800' : 'bg-emerald-100 text-emerald-800'}`;
        }

        const serverTimeEl = document.getElementById('agents-server-time');
        if (serverTimeEl) {
          serverTimeEl.innerText = data.server_time_wib || metrics.timestamp_wib || '-';
        }

        const hwChip = document.getElementById('hw-chip');
        if (hwChip) hwChip.innerText = metrics.chip || 'Apple M4 Mac mini';

        const hwPlat = document.getElementById('hw-plat');
        if (hwPlat) hwPlat.innerText = metrics.platform || 'Darwin arm64';

        const hwCpu = document.getElementById('hw-cpu');
        if (hwCpu && metrics.cpu_load_1m_5m_15m) {
          hwCpu.innerText = metrics.cpu_load_1m_5m_15m.join(', ');
        }

        const hwRam = document.getElementById('hw-ram');
        if (hwRam) hwRam.innerText = metrics.ram_summary || '16.0 GB RAM';

        const hwDisk = document.getElementById('hw-disk');
        if (hwDisk) hwDisk.innerText = `${metrics.disk_free_gb || 0} GB Bebas`;

        const hwDiskPct = document.getElementById('hw-disk-pct');
        if (hwDiskPct) hwDiskPct.innerText = `${metrics.disk_used_percent || 0}% Digunakan (${metrics.disk_total_gb || 0} GB Total)`;

        // Services Grid
        const servicesGrid = document.getElementById('agents-services-grid');
        if (servicesGrid && host.services) {
          servicesGrid.innerHTML = host.services.map(s => {
            const isOnline = s.status === 'online';
            const statusBg = isOnline ? 'bg-emerald-50 text-emerald-700 border-emerald-200' : (s.status === 'standby' ? 'bg-slate-100 text-slate-700 border-slate-200' : 'bg-rose-50 text-rose-700 border-rose-200');
            const dotClass = isOnline ? 'bg-emerald-500 animate-pulse' : (s.status === 'standby' ? 'bg-slate-400' : 'bg-rose-500');
            const iconName = s.id.includes('chrome') ? 'globe' : (s.id.includes('router') ? 'shuffle' : (s.id.includes('telegram') ? 'send' : (s.id.includes('sync') ? 'cloud' : 'server')));

            return `
              <div class="p-4 rounded-2xl bg-white border border-slate-200/80 shadow-xs space-y-2.5 hover:shadow-sm transition-all">
                <div class="flex items-center justify-between">
                  <div class="flex items-center space-x-2.5">
                    <div class="w-8 h-8 rounded-xl bg-purple-50 text-purple-700 flex items-center justify-center font-bold text-xs">
                      <i data-lucide="${iconName}" class="w-4 h-4"></i>
                    </div>
                    <div>
                      <h5 class="font-bold text-slate-900 text-xs">${s.name}</h5>
                      <span class="text-[10px] text-slate-400 font-mono block">${s.label || s.type}</span>
                    </div>
                  </div>
                  <span class="inline-flex items-center space-x-1 px-2 py-0.5 rounded-full text-[10px] font-bold border ${statusBg}">
                    <span class="w-1.5 h-1.5 rounded-full ${dotClass}"></span>
                    <span>${s.status.toUpperCase()}</span>
                  </span>
                </div>

                <p class="text-[11px] text-slate-600 leading-snug">${s.details || '-'}</p>

                <div class="pt-2 border-t border-slate-100 flex items-center justify-between text-[10.5px] font-mono text-slate-500">
                  <span>${s.pid ? `PID: <strong class="text-slate-800">${s.pid}</strong>` : 'PID: -'}</span>
                  <span>${s.port ? `PORT: <strong class="text-purple-700">:${s.port}</strong>` : (s.browser_info ? `<span class="text-slate-700">${s.browser_info}</span>` : '')}</span>
                </div>
              </div>
            `;
          }).join('');
        }

        // Detailed Character Pipeline Tasks
        const pipelineContainer = document.getElementById('agents-pipeline-detailed-list');
        if (pipelineContainer && data.pipeline_tasks) {
          pipelineContainer.innerHTML = data.pipeline_tasks.map(t => {
            const isDone = t.progress_percent === 100;
            const isRunning = t.status_tag === 'running';
            const isReview = t.status_tag === 'review';
            const cardBg = isDone ? 'bg-emerald-50/20 border-emerald-200/80' : (isRunning ? 'bg-purple-50/20 border-purple-200/80' : (isReview ? 'bg-amber-50/20 border-amber-200/80' : 'bg-slate-50/50 border-slate-200/80'));

            return `
              <div class="p-5 rounded-3xl border ${cardBg} shadow-xs space-y-4 hover:shadow-md transition-all">
                <!-- Top Row: Talent Profile & Status -->
                <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-200/60 pb-3.5">
                  <div class="flex items-center space-x-3.5">
                    ${t.avatar_url ? `
                      <img src="${t.avatar_url}" class="w-12 h-12 rounded-2xl object-cover border-2 border-white shadow-sm">
                    ` : `
                      <div class="w-12 h-12 rounded-2xl bg-purple-600 text-white font-black flex items-center justify-center text-lg shadow-sm">
                        ${t.character_name[0]}
                      </div>
                    `}
                    <div>
                      <div class="flex items-center space-x-2">
                        <h4 class="font-extrabold text-slate-900 text-sm tracking-tight">${t.character_name}</h4>
                        <a href="https://www.tiktok.com/${t.account}" target="_blank" class="text-purple-600 hover:underline text-xs font-mono font-medium">
                          ${t.account}
                        </a>
                      </div>
                      <p class="text-[11px] text-slate-500 mt-0.5">${t.niche} &bull; Flow: <code class="font-bold text-slate-700">${t.flow_account}</code></p>
                    </div>
                  </div>

                  <div class="flex items-center space-x-2 text-xs">
                    <span class="px-2.5 py-1 rounded-xl bg-purple-100 text-purple-800 font-mono font-bold text-[11px]">
                      Slot ${t.slot_time}
                    </span>
                    <span class="px-2.5 py-1 rounded-xl bg-slate-100 text-slate-700 font-mono font-bold text-[11px]">
                      ${t.target_duration}s &bull; ${t.slot_policy}
                    </span>
                    <span class="px-2.5 py-1 rounded-xl ${isDone ? 'bg-emerald-100 text-emerald-800' : 'bg-amber-100 text-amber-800'} font-bold text-[11px]">
                      ${t.slot_state}
                    </span>
                  </div>
                </div>

                <!-- Headline Status & Progress Bar -->
                <div class="space-y-2">
                  <div class="flex flex-col sm:flex-row sm:items-center justify-between text-xs gap-1">
                    <div class="flex items-center space-x-2">
                      <span class="relative flex h-2.5 w-2.5">
                        <span class="animate-ping absolute inline-flex h-full w-full rounded-full ${isDone ? 'bg-emerald-400' : 'bg-purple-400'} opacity-75"></span>
                        <span class="relative inline-flex rounded-full h-2.5 w-2.5 ${isDone ? 'bg-emerald-500' : 'bg-purple-600'}"></span>
                      </span>
                      <span class="font-bold text-slate-900 text-xs">${t.headline_status}</span>
                    </div>
                    <span class="font-mono font-extrabold text-purple-700 text-xs">${t.progress_percent}% Progress</span>
                  </div>

                  <div class="w-full bg-slate-200/80 rounded-full h-2.5 overflow-hidden">
                    <div class="h-full bg-gradient-to-r from-purple-600 via-indigo-600 to-emerald-500 rounded-full transition-all duration-700" style="width: ${t.progress_percent}%"></div>
                  </div>
                </div>

                <!-- 5-Step Stepper -->
                <div class="grid grid-cols-2 sm:grid-cols-5 gap-2 pt-1 text-xs">
                  ${t.stages.map(st => {
                    const isStDone = st.status === 'done';
                    const isStActive = st.status === 'active';
                    const stBorder = isStDone ? 'border-emerald-300 bg-emerald-50/80 text-emerald-900' : (isStActive ? 'border-purple-300 bg-purple-50/80 text-purple-900' : 'border-slate-200 bg-white text-slate-400');
                    const numBadge = isStDone ? 'bg-emerald-600 text-white' : (isStActive ? 'bg-purple-600 text-white animate-pulse' : 'bg-slate-200 text-slate-600');
                    return `
                      <div class="p-2.5 rounded-2xl border ${stBorder} flex flex-col justify-between space-y-1">
                        <div class="flex items-center space-x-1.5">
                          <span class="w-4 h-4 rounded-full ${numBadge} text-[9px] font-bold flex items-center justify-center">${isStDone ? '✓' : st.num}</span>
                          <span class="font-bold text-[11px] truncate">${st.short}</span>
                        </div>
                        <p class="text-[10px] text-slate-500 leading-tight truncate" title="${escapeHtml(st.desc)}">${st.desc}</p>
                      </div>
                    `;
                  }).join('')}
                </div>

                <!-- Meta & Action Links -->
                <div class="pt-3 border-t border-slate-200/60 flex flex-wrap items-center justify-between text-xs text-slate-500 gap-2">
                  <div class="flex flex-wrap items-center space-x-3 font-mono text-[11px]">
                    ${t.job_id ? `<span>Job: <code class="text-slate-700">${t.job_id.slice(0, 8)}... (${t.job_state})</code></span>` : ''}
                    ${t.version_id ? `<span>Versi: <code class="text-slate-700">${t.version_id.slice(0, 8)}...</code></span>` : ''}
                    ${t.approval_decision ? `<span class="px-2 py-0.5 rounded-full ${t.approval_decision === 'approved' ? 'bg-emerald-100 text-emerald-800' : 'bg-rose-100 text-rose-800'} font-bold text-[10px]">ACC: ${t.approval_decision.toUpperCase()}</span>` : ''}
                  </div>

                  <div class="flex items-center space-x-2">
                    ${t.post_url ? `
                      <a href="${t.post_url}" target="_blank" class="px-3 py-1 bg-purple-50 hover:bg-purple-100 text-purple-700 rounded-xl text-xs font-bold transition-colors flex items-center space-x-1 border border-purple-200">
                        <span>Lihat di TikTok (${t.post_id || 'Live'})</span>
                        <i data-lucide="external-link" class="w-3 h-3 ml-1"></i>
                      </a>
                    ` : ''}
                    ${t.caption ? `
                      <button onclick='openCaptionModal("${escapeJs(t.character_name)}", "${escapeJs(t.caption)}")' class="px-3 py-1 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-xs font-semibold transition-colors">
                        Buka Naskah
                      </button>
                    ` : ''}
                  </div>
                </div>
              </div>
            `;
          }).join('');
        }

        lucide.createIcons();
      } catch (err) {
        console.error("Failed to load agents status:", err);
      } finally {
        if (icon) {
          setTimeout(() => icon.classList.remove('animate-spin'), 600);
        }
      }
    }

    async function loadCreators() {
      const res = await fetch('/api/characters');
      const chars = await res.json();
      const grid = document.getElementById('creators-grid');
      grid.innerHTML = chars.map(c => `
        <div class="bg-slate-50 border border-slate-100 rounded-3xl p-5 space-y-4 hover:shadow-md transition-all">
          <div class="flex items-center space-x-3.5">
            ${c.avatar_url ? `
              <img src="${c.avatar_url}" class="w-14 h-14 rounded-2xl object-cover border-2 border-white shadow-sm">
            ` : `
              <div class="w-14 h-14 rounded-2xl bg-purple-600 text-white font-bold flex items-center justify-center text-xl shadow-sm">
                ${c.name[0]}
              </div>
            `}
            <div>
              <h4 class="font-bold text-slate-900 text-sm">${c.name}</h4>
              <a href="https://www.tiktok.com/${c.account}" target="_blank" class="text-xs text-purple-600 hover:underline font-mono font-medium block">
                ${c.account}
              </a>
              <span class="text-[11px] text-slate-400">${c.origin} &bull; ${c.age ? c.age + ' Tahun' : 'Muda'}</span>
            </div>
          </div>

          <div class="space-y-1.5 text-xs">
            <span class="font-bold text-slate-800 block">${c.job_title}</span>
            <div class="flex flex-wrap gap-1 mt-1.5">
              ${(c.content_pillars || []).slice(0, 3).map(p => `
                <span class="px-2.5 py-0.5 rounded-full text-[10px] bg-white border border-slate-200 text-slate-600 font-medium">${p.split('(')[0]}</span>
              `).join('')}
            </div>
          </div>

          <div class="pt-3 border-t border-slate-200/60 flex items-center justify-between text-xs text-slate-500">
            <span>Flow: <code class="font-bold text-slate-700">${c.flow_account_id || '-'}</code></span>
            <span class="px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800 font-bold text-[10px]">${c.publication_count} Video Live</span>
          </div>
        </div>
      `).join('');
      lucide.createIcons();
    }

    async function loadFullPublications() {
      const char = document.getElementById('pubs-filter-char').value;
      const res = await fetch('/api/publications' + (char ? '?character=' + encodeURIComponent(char) : ''));
      const pubs = await res.json();
      const tbody = document.getElementById('pubs-full-tbody');
      tbody.innerHTML = pubs.map(p => `
        <tr class="hover:bg-slate-50 transition-colors">
          <td class="py-3 px-4 font-bold text-slate-900">
            ${p.character_name || p.character_id}
            <div class="text-[10px] font-mono text-purple-600 font-normal">${p.account || ''}</div>
          </td>
          <td class="py-3 px-4 font-mono font-bold">
            ${p.post_url ? `
              <a href="${p.post_url}" target="_blank" class="text-purple-600 hover:underline flex items-center space-x-1">
                <span>${p.platform_post_id}</span>
                <i data-lucide="external-link" class="w-3 h-3 ml-1"></i>
              </a>
            ` : (p.platform_post_id || '-')}
          </td>
          <td class="py-3 px-4 text-slate-500 font-mono text-[11px]">${formatDate(p.confirmed_at)}</td>
          <td class="py-3 px-4">
            <span class="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200 uppercase">${p.state}</span>
          </td>
          <td class="py-3 px-4 text-slate-600 max-w-xs truncate" title="${escapeHtml(p.caption || '')}">
            ${p.caption ? p.caption.slice(0, 80) + '...' : '-'}
          </td>
          <td class="py-3 px-4 text-right">
            <button onclick='openCaptionModal("${escapeJs(p.character_name)}", "${escapeJs(p.caption)}")' class="px-3 py-1 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-xs font-semibold">
              Buka
            </button>
          </td>
        </tr>
      `).join('');
      lucide.createIcons();
    }

    function filterPubs() {
      loadFullPublications();
    }

    async function loadFullApprovals() {
      const res = await fetch('/api/approvals');
      const accs = await res.json();
      const tbody = document.getElementById('approvals-full-tbody');
      tbody.innerHTML = accs.map(a => `
        <tr class="hover:bg-slate-50 transition-colors">
          <td class="py-3 px-4 font-bold text-slate-900">
            ${a.character_name || a.character_id}
            <div class="text-[10px] font-mono text-purple-600 font-normal">${a.account || ''}</div>
          </td>
          <td class="py-3 px-4">
            <span class="px-2.5 py-0.5 rounded-full text-[10px] font-bold ${a.decision === 'approved' ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' : 'bg-rose-50 text-rose-700 border border-rose-200'} uppercase">${a.decision}</span>
          </td>
          <td class="py-3 px-4 font-mono text-slate-500 text-[11px]">${a.reviewer_id || 'Owner Telegram'}</td>
          <td class="py-3 px-4 text-slate-600">${a.channel || 'Telegram'}</td>
          <td class="py-3 px-4 font-mono text-slate-500 text-[11px]">${formatDate(a.created_at)}</td>
          <td class="py-3 px-4 font-mono text-slate-400 text-[10.5px]">${a.version_id ? a.version_id.slice(0, 16) + '...' : '-'}</td>
        </tr>
      `).join('');
      lucide.createIcons();
    }

    async function loadTableDropdownOptions() {
      const res = await fetch('/api/tables');
      const tables = await res.json();
      const sel = document.getElementById('tables-dropdown');
      sel.innerHTML = tables.map(t => `<option value="${t.name}">${t.name} (${t.count} baris)</option>`).join('');
      currentSelectedTable = tables[0]?.name || 'characters';
    }

    async function loadSelectedTable() {
      currentSelectedTable = document.getElementById('tables-dropdown').value || currentSelectedTable;
      const search = document.getElementById('table-search-input').value.trim();
      const url = `/api/table/${currentSelectedTable}?limit=${tablePagingLimit}&offset=${tablePagingOffset}&search=${encodeURIComponent(search)}`;
      const res = await fetch(url);
      const data = await res.json();

      document.getElementById('table-stats-info').innerText = `Tabel: ${data.table} &bull; Total: ${data.total_count} baris (menampilkan ${data.rows.length})`;
      const totalPages = Math.ceil(data.total_count / tablePagingLimit) || 1;
      const curPage = Math.floor(tablePagingOffset / tablePagingLimit) + 1;
      document.getElementById('table-page-number').innerText = `${curPage} / ${totalPages}`;
      document.getElementById('table-btn-prev').disabled = tablePagingOffset === 0;
      document.getElementById('table-btn-next').disabled = (tablePagingOffset + tablePagingLimit) >= data.total_count;

      const thead = document.getElementById('browser-thead');
      thead.innerHTML = `<tr>${data.columns.map(c => `<th class="py-2.5 px-3 uppercase tracking-wider text-[10px]">${c}</th>`).join('')}</tr>`;

      const tbody = document.getElementById('browser-tbody');
      tbody.innerHTML = data.rows.map(r => `
        <tr class="hover:bg-slate-50 transition-colors">
          ${data.columns.map(c => `<td class="py-2 px-3 max-w-xs truncate" title="${escapeHtml(String(r[c] ?? ''))}">${r[c] === null ? '<span class="text-slate-300">NULL</span>' : escapeHtml(String(r[c]))}</td>`).join('')}
        </tr>
      `).join('');
    }

    function prevTablePage() {
      if (tablePagingOffset >= tablePagingLimit) {
        tablePagingOffset -= tablePagingLimit;
        loadSelectedTable();
      }
    }

    function nextTablePage() {
      tablePagingOffset += tablePagingLimit;
      loadSelectedTable();
    }

    function debounceTableSearch() {
      clearTimeout(tableSearchTimer);
      tableSearchTimer = setTimeout(() => {
        tablePagingOffset = 0;
        loadSelectedTable();
      }, 300);
    }

    function applySqlPreset(sql) {
      document.getElementById('sql-editor').value = sql;
      executeSqlQuery();
    }

    async function executeSqlQuery() {
      const sql = document.getElementById('sql-editor').value.trim();
      const errBox = document.getElementById('sql-error-msg');
      errBox.innerText = '';
      try {
        const res = await fetch('/api/query', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ sql })
        });
        const data = await res.json();
        if (data.error) {
          errBox.innerText = data.error;
          return;
        }

        sqlExportData = data.rows;
        document.getElementById('sql-result-wrapper').classList.remove('hidden');
        document.getElementById('sql-row-count').innerText = `${data.count} baris data ditemukan`;

        const thead = document.getElementById('sql-thead');
        thead.innerHTML = `<tr>${data.columns.map(c => `<th class="py-2.5 px-3 uppercase text-[10px]">${c}</th>`).join('')}</tr>`;

        const tbody = document.getElementById('sql-tbody');
        tbody.innerHTML = data.rows.map(r => `
          <tr class="hover:bg-slate-50">
            ${data.columns.map(c => `<td class="py-2 px-3 max-w-xs truncate" title="${escapeHtml(String(r[c] ?? ''))}">${r[c] === null ? '<span class="text-slate-300">NULL</span>' : escapeHtml(String(r[c]))}</td>`).join('')}
          </tr>
        `).join('');

      } catch (err) {
        errBox.innerText = String(err);
      }
    }

    function downloadSqlJson() {
      if (!sqlExportData || !sqlExportData.length) return;
      const blob = new Blob([JSON.stringify(sqlExportData, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'sql_result.json';
      a.click();
    }

    function openCaptionModal(charName, caption) {
      document.getElementById('modal-char-title').innerText = `Naskah: ${charName}`;
      document.getElementById('modal-caption-content').innerText = caption;
      document.getElementById('modal-char-counter').innerText = `${caption.length} karakter &bull; 0% Emoji`;
      document.getElementById('caption-modal').classList.remove('hidden');
    }

    function closeCaptionModal() {
      document.getElementById('caption-modal').classList.add('hidden');
    }

    function copyCaptionText() {
      const text = document.getElementById('modal-caption-content').innerText;
      navigator.clipboard.writeText(text);
      const btn = document.getElementById('btn-copy-caption');
      btn.innerText = 'Tersalin!';
      setTimeout(() => btn.innerText = 'Salin Teks', 2000);
    }

    function handleGlobalSearch(term) {
      if (!term.trim()) return;
      // Filter publications when searching
      document.getElementById('global-search').addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
          switchTab('publications');
        }
      });
    }

    function formatDate(isoStr) {
      if (!isoStr) return '-';
      try {
        const d = new Date(isoStr);
        return d.toLocaleString('id-ID', { dateStyle: 'medium', timeStyle: 'short' });
      } catch {
        return isoStr;
      }
    }

    function escapeHtml(str) {
      return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
    }

    function escapeJs(str) {
      if (!str) return '';
      return str.replace(/'/g, "\\'").replace(/"/g, '&quot;').replace(/\\n/g, ' ');
    }

    window.onload = initApp;
  </script>
</body>
</html>
"""
        body = html.encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

def run():
    server_address = ('', PORT)
    httpd = ThreadedHTTPServer(server_address, DashboardHandler)
    print(f"\n=======================================================")
    print(f"🚀 AI Influencer Super Finti / Metabase Hub is RUNNING!")
    print(f"🌐 Akses Website di: http://localhost:{PORT} atau http://127.0.0.1:{PORT}")
    print(f"📊 Menghubungkan database: {DB_PATH}")
    print(f"=======================================================\n")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping dashboard server...")
        httpd.server_close()

if __name__ == '__main__':
    run()
