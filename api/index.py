#!/usr/bin/env python3
"""
Vercel Serverless Function entrypoint for AI Influencer Operations Hub.
Inherits from DashboardHandler in app/dashboard_server.py.
"""

import sys
from pathlib import Path
from http.server import BaseHTTPRequestHandler

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.dashboard_server import DashboardHandler, run

class handler(DashboardHandler):
    pass

if __name__ == '__main__':
    run()
