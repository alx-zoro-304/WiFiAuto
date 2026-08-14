#!/bin/bash
exec pkexec env DISPLAY="$DISPLAY" XAUTHORITY="$XAUTHORITY" python3 "$(dirname "$0")/mac_changer_pro.py"