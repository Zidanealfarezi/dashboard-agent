#!/bin/bash
# Script untuk menjalankan KANTOR AI Virtual Office & membukanya ke Internet via Cloudflare Tunnel (Tanpa Warning Page)

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

echo "=================================================="
echo "🏢 MENJALANKAN KANTOR AI INTAN VIRTUAL OFFICE"
echo "=================================================="

# 1. Jalankan web server lokal jika belum berjalan
if ! lsof -i :5173 > /dev/null 2>&1; then
    echo "▶ Memulai server lokal di http://localhost:5173..."
    python3 server.py > /tmp/virtual-office-server.log 2>&1 &
    sleep 1
else
    echo "✓ Server lokal sudah aktif di http://localhost:5173"
fi

# 2. Jalankan Cloudflare Tunnel jika belum berjalan
CF_BIN="$DIR/bin/cloudflared"
if ! pgrep -f "cloudflared.*5173" > /dev/null 2>&1; then
    echo "▶ Membuka tunnel online Cloudflare (Tanpa layar verifikasi)..."
    "$CF_BIN" tunnel --url http://localhost:5173 > /tmp/cloudflared.log 2>&1 &
    
    # Tunggu URL terbentuk
    PUBLIC_URL=""
    for i in {1..12}; do
        sleep 1
        PUBLIC_URL=$(grep -o "https://[-a-zA-Z0-9]*\.trycloudflare\.com" /tmp/cloudflared.log 2>/dev/null | head -n 1)
        if [ -n "$PUBLIC_URL" ]; then
            break
        fi
    done
else
    PUBLIC_URL=$(grep -o "https://[-a-zA-Z0-9]*\.trycloudflare\.com" /tmp/cloudflared.log 2>/dev/null | head -n 1)
    echo "✓ Cloudflare Tunnel sudah aktif"
fi

echo ""
echo "🎉 KANTOR AI INTAN SEKARANG SUDAH ONLINE!"
echo "--------------------------------------------------"
echo "🌐 URL Publik (Bisa dibuka langsung di HP / Siapa saja):"
echo "   $PUBLIC_URL"
echo ""
echo "💻 URL Lokal (Di Mac ini):"
echo "   http://localhost:5173"
echo "--------------------------------------------------"
echo "⚡ Keunggulan Cloudflare: Langsung terbuka cepat tanpa ada tombol 'Visit Site'!"
