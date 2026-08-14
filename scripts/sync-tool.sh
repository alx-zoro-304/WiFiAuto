#!/usr/bin/env bash
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$ROOT/public/downloads"
mkdir -p "$OUT"

# --- Windows package (tool/) ---
cp "$ROOT"/tool/*.py "$ROOT"/tool/*.bat "$ROOT"/tool/*.exe "$ROOT"/tool/*.zip "$OUT/"
cp "$ROOT/tool/start.sh" "$OUT/"

# --- Linux package (tool-linux/) ---
rm -f "$OUT/WiFiAuto_v2-linux.tar.gz"
tar -czf "$OUT/WiFiAuto_v2-linux.tar.gz" \
    -C "$ROOT/tool-linux" wifi_auto_gui.py mac_changer_pro.py updater.py \
    start_wifi_auto.sh start_changer.sh "WiFi Auto.desktop" \
    "MAC Changer.desktop" README.txt MikrotikSploit
cp "$ROOT/tool-linux/wifi_auto_gui.py" "$OUT/wifi_auto_gui_linux.py"
cp "$ROOT/tool-linux/mac_changer_pro.py" "$OUT/mac_changer_pro_linux.py"
cp "$ROOT/tool-linux/updater.py" "$OUT/updater.py"
cp "$ROOT/tool-linux/README.txt" "$OUT/README_LINUX.txt"

cp "$ROOT/version.json" "$ROOT/public/version.json"
echo "Synced Windows + Linux tool files -> public/ (ready for local build)"