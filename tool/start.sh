#!/usr/bin/env bash
# WiFi Auto — Linux launcher (requests sudo automatically)
cd "$(dirname "$0")"

if [ "$(id -u)" -ne 0 ]; then
    echo "WiFi Auto needs root for MAC change + deep scan — elevating with sudo ..."
    exec sudo python3 "$(pwd)/wifi_auto_gui.py" "$@"
else
    exec python3 "$(pwd)/wifi_auto_gui.py" "$@"
fi