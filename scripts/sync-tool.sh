#!/usr/bin/env bash
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$ROOT/public/downloads"
mkdir -p "$OUT"

# --- Windows package (tool/) ---
rm -f "$OUT/WiFiAuto_v2.zip"
python3 - "$ROOT/tool" "$OUT/WiFiAuto_v2.zip" <<'EOF'
import zipfile, os, sys
src, dst = sys.argv[1], sys.argv[2]
skip = ("__pycache__", ".pyc", ".bak")
with zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as z:
    for root, dirs, files in os.walk(src):
        dirs[:] = [d for d in dirs if d not in skip]
        for f in files:
            if f.endswith(skip[1]) or f.endswith(skip[2]):
                continue
            full = os.path.join(root, f)
            rel = os.path.relpath(full, src)
            z.write(full, rel.replace(os.sep, "/"))
print("ZIP rebuilt:", dst)
EOF
cp "$ROOT"/tool/*.bat "$ROOT"/tool/*.exe "$OUT/"
cp "$ROOT/tool/start.sh" "$OUT/"

# --- Linux package (tool-linux/) ---
rm -f "$OUT/WiFiAuto_v2-linux.tar.gz"
tar -czf "$OUT/WiFiAuto_v2-linux.tar.gz" \
    --exclude="__pycache__" --exclude="*.pyc" --exclude="*.bak" \
    -C "$ROOT/tool-linux" wifi_auto_gui.py mac_changer_pro.py updater.py \
    start_wifi_auto.sh start_changer.sh "WiFi Auto.desktop" \
    "MAC Changer.desktop" README.txt MikrotikSploit
cp "$ROOT/tool-linux/wifi_auto_gui.py" "$OUT/wifi_auto_gui_linux.py"
cp "$ROOT/tool-linux/mac_changer_pro.py" "$OUT/mac_changer_pro_linux.py"
cp "$ROOT/tool-linux/updater.py" "$OUT/updater.py"
cp "$ROOT/tool-linux/README.txt" "$OUT/README_LINUX.txt"

cp "$ROOT/version.json" "$ROOT/public/version.json"
echo "Synced Windows + Linux tool files -> public/ (ready for local build)"