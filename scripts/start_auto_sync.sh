#!/bin/bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"
cd "$DIR"

echo "Memeriksa status Auto-Sync Daemon..."
python3 scripts/auto_sync_vercel.py --status | grep -q "SEDANG BERJALAN"
if [ $? -eq 0 ]; then
  echo "Auto-Sync Daemon sudah aktif."
  exit 0
fi

echo "Menjalankan Auto-Sync Daemon Vercel di background..."
nohup python3 scripts/auto_sync_vercel.py --daemon > /dev/null 2>&1 &
sleep 1.5

python3 scripts/auto_sync_vercel.py --status
