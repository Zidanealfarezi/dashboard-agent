#!/bin/bash
# Script untuk menghentikan server dan tunnel Kantor AI Virtual Office

echo "Menghentikan KANTOR AI server dan tunnel..."
pkill -f "python3.*server.py" 2>/dev/null
pkill -f "cloudflared.*5173" 2>/dev/null
pkill -f "ngrok http 5173" 2>/dev/null
echo "✓ KANTOR AI berhasil dinonaktifkan."
