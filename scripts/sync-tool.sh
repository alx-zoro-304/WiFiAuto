#!/usr/bin/env bash
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$ROOT/public/downloads"
mkdir -p "$OUT"

cp "$ROOT"/tool/*.py "$ROOT"/tool/*.bat "$ROOT"/tool/*.exe "$ROOT"/tool/*.zip "$OUT/"
cp "$ROOT/tool/start.sh" "$OUT/"

rm -f "$OUT/WiFiAuto_v2-linux.tar.gz"
tar -czf "$OUT/WiFiAuto_v2-linux.tar.gz" \
    -C "$ROOT/tool" wifi_auto_gui.py mac_changer_pro.py updater.py \
    start.sh start.bat start_changer.bat 2>/dev/null || \
tar -czf "$OUT/WiFiAuto_v2-linux.tar.gz" \
    -C "$ROOT/tool" wifi_auto_gui.py updater.py start.sh

cp "$ROOT/version.json" "$ROOT/public/version.json"
echo "Synced tool files + version.json -> public/ (ready for local build)"