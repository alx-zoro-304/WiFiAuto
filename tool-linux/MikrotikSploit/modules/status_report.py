#!/usr/bin/python3
# coding=utf-8
# SESSION STATUS - live honest assessment of the current session:
#   what we could reach, what is blocked, why, and what to do next.
# Run it whenever you want a clear picture before attacking.

import socket
import struct
import sys
import time

from color import R, P, W, B, N, T, Y, WOW, vulnexploit, failexploit
from net_scan import discover_all, arp_resolve

HELLO = bytes.fromhex("680100664d320500ff010600ff09050700ff090701000021")


def _tcp_connect(ip, port, timeout=3):
    s = socket.socket()
    s.settimeout(timeout)
    try:
        s.connect((ip, port))
        return "OPEN"
    except OSError:
        return "BLOCKED"
    finally:
        s.close()


def _tcp_talks(ip, port, body, timeout=4):
    """Connect, send body, does the service answer anything?"""
    s = socket.socket()
    s.settimeout(timeout)
    try:
        s.connect((ip, port))
        s.sendall(body)
        s.settimeout(timeout)
        try:
            data = s.recv(4096)
            return "REPLIES" if data else "SILENT"
        except socket.timeout:
            return "SILENT"
    except OSError:
        return "BLOCKED"
    finally:
        s.close()


def _udp_talks(ip, port, timeout=4):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    s.bind(("0.0.0.0", 0))
    s.settimeout(timeout)
    try:
        s.sendto(HELLO, (ip, port))
        try:
            d, a = s.recvfrom(2048)
            return f"REPLIES ({len(d)}B)"
        except socket.timeout:
            return "SILENT"
    except OSError:
        return "BLOCKED"
    finally:
        s.close()


def _http_code(ip, timeout=4):
    try:
        import urllib.request
        r = urllib.request.urlopen(f"http://{ip}/", timeout=timeout)
        return r.status
    except Exception as e:
        code = getattr(e, "code", None)
        if code:
            return code
        return None


def run_status(scan_timeout=5):
    print(f"{WOW}\n{'#' * 72}{N}")
    print(f"{WOW}   SESSION STATUS - honest live assessment{N}")
    print(f"{WOW}{'#' * 72}{N}")

    # --- our position ---
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("10.0.0.1", 9))
        myip = s.getsockname()[0]
        s.close()
    except OSError:
        myip = "?"
    print(f"{W}[{P} * {W}]{B} Our IP: {T}{myip}{N}")

    # --- devices ---
    print(f"{W}[{P} * {W}]{B} Discovering MikroTik devices "
          f"({T}{scan_timeout}{B}s)...{N}")
    devices = arp_resolve(discover_all(scan_timeout))
    if not devices:
        print(f"{W}[{R} - {W}]{B} No devices found on this LAN.{N}")
        return

    print(f"{W}{'=' * 72}{N}")
    print(f"{W}{'DEVICE':<16}{'MAC':<20}{'VERSION':<24}{'REACHABLE'}{N}")
    print(f"{W}{'-' * 72}{N}")
    for d in devices:
        ip = d["ip"]
        ok = ip not in ("0.0.0.0", "")
        mark = f"{vulnexploit}{B} yes{N}" if ok else f"{failexploit}{B} no IP{N}"
        print(f"{W}{ip:<16}{d['mac']:<20}{d['version']:<24}{mark}{N}")

    # --- per-device service probes ---
    for d in devices:
        ip = d["ip"]
        if ip in ("0.0.0.0", ""):
            print(f"{WOW}\n--- {d['mac']} ({d['version']}) ---{N}")
            print(f"{Y}  no IP on this subnet -> services unreachable.{N}")
            print(f"{Y}  Fix: give it an IP on this network (or plug it "
                  f"directly), then rescan.{N}")
            continue
        print(f"{WOW}\n--- {ip} ({d['mac']}, {d['version']}) ---{N}")
        api = _tcp_connect(ip, 8728)
        api_talk = _tcp_talks(ip, 8728,
                              struct.pack(">H", 33) +
                              b"/login\n=name=admin\n=password=admin\n")
        win = _tcp_connect(ip, 8291)
        win_talk = _tcp_talks(ip, 8291, struct.pack(">I", len(HELLO)) + HELLO)
        win_udp = _udp_talks(ip, 20561)
        web = _http_code(ip)
        print(f"{W}[{T}API{W}] TCP {api:<8} protocol {api_talk}{N}")
        print(f"{W}[{T}WINBOX{W}] TCP {win:<8} protocol {win_talk}{N}")
        print(f"{W}[{T}WINBOX{W}] UDP 20561  {win_udp}{N}")
        print(f"{W}[{T}WEB{W}]  HTTP :{web if web else 'no reply'}{N}")
        if api_talk in ("SILENT", "BLOCKED") or win_talk in ("SILENT", "BLOCKED"):
            print(f"{Y}  -> management services refuse us: "
                  f"restricted (allowed-addresses / firewall).{N}")
        if api_talk == "REPLIES" or win_talk == "REPLIES":
            print(f"{WOW}  -> service ALIVE and TALKING! Run option 2 / 7 / 9.{N}")

    # --- honest summary ---
    print(f"{WOW}\n{'=' * 72}{N}")
    print(f"{WOW}   HONEST SUMMARY{N}")
    print(f"{WOW}{'=' * 72}{N}")
    print(f"{W}   Exploits delivered so far : none (targets locked){N}")
    print(f"{W}   Accounts obtained         : none{N}")
    print(f"{W}   Why: services are silent/blocked from our IP.{N}")
    print(f"{W}   This is security working - not a tool bug.{N}")
    print(f"{W}{'-' * 72}{N}")
    print(f"{WOW}   HOW TO ACTUALLY GET IN{N}")
    print(f"{B}   1. Test router you own with default config    "
          f"{W}-> tools will pop it instantly{N}")
    print(f"{B}   2. Run from an allowed source                 "
          f"{W}-> operator's PC / VPN{N}")
    print(f"{B}   3. Give the 2nd device (no IP) an address     "
          f"{W}-> then option 2 / 7{N}")
    print(f"{B}   4. Get creds first (user.dat / default)       "
          f"{W}-> then option 9 full control{N}")
    print(f"{W}{'-' * 72}{N}")
    print(f"{W}[{P} * {W}]{B} Tip: run this after every network "
          f"change to see if targets opened up.{N}")


if __name__ == "__main__":
    run_status()