#!/bin/bash
exec pkexec env DISPLAY="$DISPLAY" XAUTHORITY="$XAUTHORITY" python3 "$(dirname "$0")/wifi_auto_gui.py"