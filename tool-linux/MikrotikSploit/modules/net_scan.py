#!/usr/bin/python3
# coding=utf-8
# LAN MikroTik discovery - finds ALL responding MikroTik devices with
# MAC, identity and RouterOS version (Winbox discovery protocol).

import os
import re
import socket
import subprocess
import threading
import time

from color import R, P, W, B, N, T, Y, WOW

if os.name == "nt":
    try:
        os.system("")
    except Exception:
        pass


def _subnet_broadcasts():
    """Per-interface subnet broadcasts (e.g. 192.168.1.255). Windows
    firewalls often ignore the 255.255.255.255 flood, so we also
    broadcast to every local subnet (/24 assumed)."""
    targets = []
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        if ip and not ip.startswith("127."):
            targets.append(".".join(ip.split(".")[:3]) + ".255")
    except OSError:
        pass
    try:
        for info in socket.getaddrinfo(socket.gethostname(), None):
            ip = info[4][0]
            if ip.count(".") == 3 and not ip.startswith("127."):
                targets.append(".".join(ip.split(".")[:3]) + ".255")
    except OSError:
        pass
    seen = []
    for t in targets:
        if t not in seen:
            seen.append(t)
    return seen


def discover_all(timeout=6):
    """Return list of dicts: mac, identity, version, ip (may be 0.0.0.0)."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.bind(("0.0.0.0", 5678))
        sock.settimeout(1)
    except OSError as e:
        print(f"{W}[{R} - {W}]{B} Bind error: {e}{N}")
        return []

    targets = ["255.255.255.255"] + _subnet_broadcasts()
    stop = False

    def _loop():
        while not stop:
            try:
                for t in targets:
                    sock.sendto(b"\x00\x00\x00\x00", (t, 5678))
            except OSError:
                return
            time.sleep(0.15)

    threading.Thread(target=_loop, daemon=True).start()
    found = {}
    deadline = time.time() + timeout
    try:
        while time.time() < deadline:
            data, addr = sock.recvfrom(2048)
            fields = {}
            i = data.find(b"\x00\x01\x00\x06")
            if i == -1:
                continue
            mac = ":".join("%02x" % b for b in data[i + 4:i + 10])
            if not mac:
                continue
            for m in re.finditer(rb"\x00([\x05\x07\x08])\x00(.)", data):
                ln = m.group(2)[0]
                if m.end() + ln <= len(data):
                    fields[m.group(1)[0]] = \
                        data[m.end():m.end() + ln].decode("utf-8", "replace")
            entry = found.setdefault(mac, {
                "mac": mac, "ip": addr[0], "identity": None,
                "version": "unknown"})
            if fields.get(5):
                entry["identity"] = fields.get(5)
            if fields.get(8) and not entry["identity"]:
                entry["identity"] = fields.get(8)
            if fields.get(7):
                entry["version"] = fields.get(7)
            if entry["ip"] in ("0.0.0.0", "") and addr[0] not in ("0.0.0.0", ""):
                entry["ip"] = addr[0]
    except socket.timeout:
        pass
    finally:
        stop = True
        sock.close()
    return list(found.values())


def _arp_table():
    """MAC -> IP table, cross-platform (/proc/net/arp on Linux,
    `arp -a` on Windows). Returns {} on failure."""
    table = {}
    try:
        if os.name == "nt":
            out = subprocess.run(["arp", "-a"], capture_output=True,
                                 text=True, timeout=10).stdout
            for line in out.splitlines():
                m = re.search(
                    r"([\d.]+)\s+([0-9a-fA-F-]{17})", line)
                if m:
                    ip, mac = m.group(1), m.group(2).replace("-", ":").lower()
                    if mac != "00:00:00:00:00:00":
                        table[mac] = ip
        else:
            with open("/proc/net/arp") as f:
                lines = f.readlines()[1:]
            for line in lines:
                parts = line.split()
                if len(parts) >= 4 and parts[3] != "00:00:00:00:00:00":
                    table[parts[3].lower()] = parts[0]
    except Exception:
        return {}
    return table


def arp_resolve(devices):
    """Try to fill unknown IPs (0.0.0.0) using the ARP/neighbor table."""
    table = _arp_table()
    for d in devices:
        if d["ip"] in ("0.0.0.0", ""):
            d["ip"] = table.get(d["mac"].lower(), d["ip"])
    return devices


def run_scan(timeout=6):
    print(f"{WOW}\n[ Network Scan - all MikroTik devices ]{N}")
    print(f"{W}[{P} * {W}]{B} Listening on UDP 5678 for {T}{timeout}{B}s ...{N}")
    devices = arp_resolve(discover_all(timeout))
    if not devices:
        print(f"{W}[{R} - {W}]{B} No MikroTik devices answered on this LAN.{N}")
        return []
    print(f"{W}{'-' * 72}{N}")
    print(f"{W}{'#':<3}{'IP':<16}{'MAC':<20}{'Version':<24}{'Identity'}{N}")
    print(f"{W}{'-' * 72}{N}")
    for i, d in enumerate(devices, 1):
        ip = d["ip"] if d["ip"] not in ("0.0.0.0", "") else "unknown"
        ver = d["version"] if d["version"] != "unknown" else "unknown"
        ident = d["identity"] or "-"
        print(f"{W}[{T}{i:>2}{W}]{B} {ip:<14}{W}{d['mac']:<20}"
              f"{T}{ver:<24}{N}{Y}{ident}{N}")
    print(f"{W}{'-' * 72}{N}")
    print(f"{W}[{P} * {W}]{B} Found {T}{len(devices)}{N}{B} device(s)."
          f"{N}")
    print(f"{W}   Use option {B}2{N}{W} and enter the target IP"
          f"{W} (press {B}n{W} when asked for IP/MAC).{N}")
    return devices


if __name__ == "__main__":
    run_scan()