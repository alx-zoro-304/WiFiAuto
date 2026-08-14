@echo off
title MAC Changer Pro - Launcher
cd /d "%~dp0"

net session >nul 2>&1
if %errorlevel% neq 0 (
    echo Requesting administrator rights...
    powershell -NoProfile -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
    exit /b
)

where pythonw >nul 2>&1
if %errorlevel% equ 0 (
    start "" pythonw "%~dp0mac_changer_pro.py"
) else (
    where python >nul 2>&1
    if %errorlevel% equ 0 (
        start "" python "%~dp0mac_changer_pro.py"
    ) else (
        echo Python is not installed. Install it from https://python.org
        pause
    )
)