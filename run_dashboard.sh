#!/bin/bash
# AI Influencer Database Web Dashboard & Vercel Auto-Sync Launcher
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

echo "Memeriksa proses server dashboard..."
PID=$(lsof -ti:8080)
if [ -n "$PID" ]; then
  echo "Server dashboard sudah aktif di PID $PID."
else
  echo "Menjalankan server dashboard di http://localhost:8080..."
  nohup python3 app/dashboard_server.py > operations/dashboard_server.log 2>&1 &
  sleep 1
fi

echo "Memeriksa Auto-Sync Daemon ke Vercel..."
./scripts/start_auto_sync.sh

echo "Membuka browser ke http://localhost:8080..."
open "http://localhost:8080" 2>/dev/null || xdg-open "http://localhost:8080" 2>/dev/null
