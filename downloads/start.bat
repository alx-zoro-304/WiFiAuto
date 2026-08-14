@echo off
title WiFi Auto - Launcher
cd /d "%~dp0"

net session >nul 2>&1
if %errorlevel% neq 0 (
    echo Requesting administrator rights...
    powershell -NoProfile -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
    exit /b
)

where pythonw >nul 2>&1
if %errorlevel% equ 0 (
    start "" pythonw "%~dp0wifi_auto_gui.py"
) else (
    where python >nul 2>&1
    if %errorlevel% equ 0 (
        start "" python "%~dp0wifi_auto_gui.py"
    ) else (
        echo Python is not installed. Install it from https://python.org
        pause
    )
)