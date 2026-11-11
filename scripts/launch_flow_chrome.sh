#!/bin/bash
# Launcher Chrome dengan Remote Debugging Port 9222 untuk Automasi Bebas Pop-up
PROFILE_DIR="$HOME/Library/Application Support/Google/Chrome-Flow"
mkdir -p "$PROFILE_DIR"

echo "Membuka Google Chrome khusus automasi Google Flow di port 9222..."
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --remote-debugging-port=9222 \
  --user-data-dir="$PROFILE_DIR" \
  --no-first-run \
  --no-default-browser-check \
  "https://flow.google.com/" &
