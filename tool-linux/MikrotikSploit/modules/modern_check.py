#!/usr/bin/python3
# coding=utf-8
# Modern MikroTik vulnerability checker - non-destructive probes only.
# Checks: CVE-2026-16347, CVE-2026-7668, CVE-2026-39042, CVE-2026-14227,
#         CVE-2025-61481, CVE-2025-10948, CVE-2025-42611, CVE-2025-6563,
#         CVE-2024-27686
# Timeout (pause) between every check so results are clearly visible.

import re
import socket
import struct
import threading
import time

import requests

try:
    requests.packages.urllib3.disable_warnings()
except Exception:
    pass

from color import (R, P, W, B, N, T, Y, WOW, F2, vulnexploit,
                   failexploit, portopen, portclose)


class ModernChecker(object):
    def __init__(self, ip, timeout=4):
        self.ip = ip
        self.timeout = timeout
        self.version = None
        self.version_raw = "unknown"
        self.identity = None
        self.mac = None
        self.results = []
        self.detect_version()

    # ------------------------------------------------------------------
    def _port_open(self, p):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(self.timeout)
        try:
            s.connect((self.ip, p))
            return True
        except OSError:
            return False
        finally:
            s.close()

    def _http(self, path, method="GET", data=None, headers=None):
        try:
            kw = dict(timeout=self.timeout, verify=False,
                      allow_redirects=True)
            if headers:
                kw["headers"] = headers
            if method == "POST":
                return requests.post(f"http://{self.ip}{path}",
                                     data=data, **kw)
            return requests.get(f"http://{self.ip}{path}", **kw)
        except OSError:
            return None

    def _is_below(self, major, minor, patch):
        if not self.version:
            return None
        target = (major, minor, patch)
        mine = (self.version + (0, 0, 0))[:3]
        return mine < target

    def _cmp(self, v):
        """-1 if self.version < v, 0 equal, 1 greater (v is 3-tuple)."""
        mine = (self.version + (0, 0, 0))[:3]
        other = (tuple(v) + (0, 0, 0))[:3]
        return (mine > other) - (mine < other)

    def _in_range(self, lo, hi):
        return self._cmp(lo) >= 0 and self._cmp(hi) <= 0

    def _is_6x(self):
        return self.version is not None and self.version[0] == 6

    # ------------------------------------------------------------------
    def detect_version(self):
        # 1) Winbox discovery protocol - version is inside the reply (field 0x07)
        if self._discover():
            return
        # 2) Fallback: HTTP WebFig pages
        for path in ("/webfig/", "/webfig", "/login", "/"):
            r = self._http(path)
            if r is None:
                continue
            m = re.search(r"RouterOS[^0-9]{0,8}([0-9]+(?:\.[0-9]+){1,3})",
                          r.text, re.I)
            if m:
                parts = [int(x) for x in m.group(1).split(".")]
                self.version = tuple(parts)
                self.version_raw = m.group(1)
                return

    def _discover(self, timeout=3):
        """UDP broadcast (5678) - Winbox discovery.
        Reply format: field bytes \x00<id>\x00<len><data>,
        0x06=MAC (no length byte), 0x05=platform, 0x07=version, 0x08=identity."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.bind(("0.0.0.0", 5678))
            sock.settimeout(1)
        except OSError:
            return False
        stop = False

        def _loop():
            while not stop:
                try:
                    sock.sendto(b"\x00\x00\x00\x00",
                                ("255.255.255.255", 5678))
                except OSError:
                    return
                time.sleep(0.2)

        threading.Thread(target=_loop, daemon=True).start()
        deadline = time.time() + timeout
        try:
            while time.time() < deadline:
                data, _ = sock.recvfrom(2048)
                fields = {}
                for m in re.finditer(rb"\x00([\x05\x07\x08])\x00(.)", data):
                    ln = m.group(2)[0]
                    if m.end() + ln <= len(data):
                        fields[m.group(1)[0]] = \
                            data[m.end():m.end() + ln].decode("utf-8", "replace")
                ver = fields.get(7)
                if ver and re.search(r"[0-9]+(?:\.[0-9]+){1,3}", ver):
                    self.version_raw = ver
                    self.version = tuple(
                        int(x) for x in re.search(
                            r"[0-9]+(?:\.[0-9]+){1,3}", ver).group(0).split("."))
                    self.identity = fields.get(8) or fields.get(5)
                    i = data.find(b"\x00\x01\x00\x06")
                    if i != -1:
                        self.mac = ":".join("%02x" % b
                                            for b in data[i + 4:i + 10])
                    return True
        except socket.timeout:
            pass
        finally:
            stop = True
            sock.close()
        return False

    # ------------------------------------------------------------------
    # CVE-2026-16347: API authentication without rate limiting (all versions)
    def check_16347(self):
        if not self._port_open(8728):
            return False, "API (TCP 8728) closed - not exposed"
        times = []
        body = b"/login\n=name=admin\n=password=guess123\n"
        try:
            s = socket.create_connection((self.ip, 8728), self.timeout)
            for i in range(4):
                t0 = time.time()
                s.sendall(struct.pack(">H", len(body)) + body)
                s.settimeout(5)
                try:
                    s.recv(1024)
                except socket.timeout:
                    pass
                times.append(time.time() - t0)
                time.sleep(0.5)
            s.close()
        except OSError as e:
            return False, f"API probe failed: {e}"
        avg = sum(times) / len(times)
        if avg < 2.0:
            return True, f"API answers failed logins fast (avg {avg:.1f}s) - no rate limiting detected"
        return False, f"API delayed replies (avg {avg:.1f}s) - lockout/rate limiting in place"

    # ------------------------------------------------------------------
    # CVE-2026-7668: SCEP endpoint OOB read (RouterOS 6.49.8)
    def check_7668(self):
        if not self._port_open(80):
            return False, "no HTTP service"
        r = self._http("/scep")
        if r is None:
            return False, "SCEP endpoint did not respond"
        if self.version and self.version[:2] == (6, 49):
            return True, f"SCEP answered ({r.status_code}) on RouterOS {self.version_raw} - OOB read applies"
        return False, f"SCEP reachable ({r.status_code}) but version {self.version_raw} not confirmed affected"

    # ------------------------------------------------------------------
    # CVE-2026-39042: DoS via libumsg.so unflatten() (7.21.x < 7.21.4, 7.22.x < 7.22.2)
    def check_39042(self):
        if self.version is None:
            return None, "version unknown - cannot assess"
        if self.version[:2] == (7, 21) and self._is_below(7, 21, 4):
            return True, f"RouterOS {self.version_raw} < 7.21.4 - unflatten() DoS applies"
        if self.version[:2] == (7, 22) and self._is_below(7, 22, 2):
            return True, f"RouterOS {self.version_raw} < 7.22.2 - unflatten() DoS applies"
        return False, f"RouterOS {self.version_raw} is patched"

    # ------------------------------------------------------------------
    # CVE-2026-14227: API session-management (stale permissions)
    def check_14227(self):
        if not self._port_open(8728):
            return False, "API (TCP 8728) closed - not exposed"
        return True, "API enabled - session-permission retention flaw applies"

    # ------------------------------------------------------------------
    # CVE-2025-61481: WebFig over cleartext HTTP (7.14.2 / SwOS 2.18 pattern)
    def check_61481(self):
        r = self._http("/webfig/")
        if r is None:
            return False, "no WebFig over HTTP"
        if r.status_code == 200 and "WebFig" in r.text:
            return True, "WebFig served over cleartext HTTP - credential interception possible"
        return False, "WebFig not exposed over plain HTTP"

    # ------------------------------------------------------------------
    # CVE-2025-10948: libjson.so parse_json_element BOF (RouterOS 7)
    def check_10948(self):
        if self.version is None or self.version[0] != 7:
            return None, "needs RouterOS 7 fingerprint"
        if self._port_open(8291) or self._port_open(80):
            return True, f"RouterOS 7.x ({self.version_raw}) with remote mgmt exposed - BOF surface applies"
        return False, "no remote management surface found"

    # ------------------------------------------------------------------
    # CVE-2025-42611: shared trust store cert bypass (<= 6.47)
    def check_42611(self):
        if self.version is None:
            return None, "version unknown - cannot assess"
        if self.version[:2] == (6, 47) or self._is_below(6, 48, 0):
            return True, f"RouterOS {self.version_raw} <= 6.47 - CAPsMAN/OpenVPN/Dot1x auth bypass applies"
        return False, f"RouterOS {self.version_raw} patched"

    # ------------------------------------------------------------------
    # CVE-2025-6563: Hotspot XSS (version < 7.19.2)
    def check_6563(self):
        r = self._http("/hotspotlogin")
        if r is None:
            return False, "no hotspot page"
        if self.version is None:
            return None, f"hotspot reachable ({r.status_code}) but version unknown"
        if self._is_below(7, 19, 2):
            return True, f"Hotspot reachable on {self.version_raw} < 7.19.2 - XSS applies"
        return False, "hotspot present but version patched"

    # ------------------------------------------------------------------
    # CVE-2024-27686: SMB DoS (x86 6.40.5 - 6.49.10)
    def check_27686(self):
        if not self._port_open(445):
            return False, "SMB (TCP 445) closed"
        if self.version and self.version[0] == 6 and \
                (6, 40, 5) <= (self.version + (0, 0, 0))[:3] <= (6, 49, 10):
            return True, f"SMB open on RouterOS {self.version_raw} - DoS applies (x86 only)"
        return False, f"SMB open but version {self.version_raw} outside 6.40.5-6.49.10"

    # ------------------------------------------------------------------
    def _pre_check(self, pause):
        """Probe common ports + ping; warn loudly if target is unreachable."""
        services = [
            (80,   "HTTP (WebFig)"),
            (443,  "HTTPS (WebFig SSL)"),
            (8291, "Winbox (UDP/TCP)"),
            (8728, "API"),
            (445,  "SMB"),
            (22,   "SSH"),
            (23,   "Telnet"),
        ]
        print(f"{W}[{P} * {W}]{B} Connectivity pre-check ...{N}")
        open_ports = []
        for port, name in services:
            ok = self._port_open(port)
            state = f"{P}{portopen}{N}" if ok else f"{portclose}"
            print(f"{W}    {name:<18} {W}[{state}{W}] {T}{self.ip}:{port}{N}")
            if ok:
                open_ports.append(port)
        time.sleep(pause)

        if not open_ports:
            print(f"{W}{'-' * 72}{N}")
            print(f"{R}{WOW} WARNING{N}{R}: no services answered on {self.ip}.{N}")
            print(f"{T}  Possible causes:{N}")
            print(f"{W}    1. Wrong IP (is this the MikroTik router?){N}")
            print(f"{W}    2. Router firewall blocking probes from your device{N}")
            print(f"{W}    3. Router powered off / disconnected{N}")
            print(f"{W}    4. You scanned your own PC IP instead of the router{N}")
            print(f"{W}{'-' * 72}{N}")
        else:
            print(f"{W}    -> {T}{len(open_ports)}{N}{B} service(s) reachable: "
                  f"{W}{', '.join(str(p) for p in open_ports)}{N}")
            time.sleep(pause)

    # ==================================================================
    # LEGACY (old) MikroTik vulnerabilities - version / service based
    # ==================================================================

    # CVE-2018-14847: Winbox directory traversal - unauth file read / write
    def check_14847(self):
        if self.version is None:
            return None, "version unknown"
        if self.version[0] == 5 or self._cmp((6, 42, 0)) <= 0:
            return True, f"RouterOS {self.version_raw} - Winbox traversal (file read/write) applies"
        return False, f"patched (fixed in 6.42.1)"

    # CVE-2019-3924: unauth login bypass via internal API
    def check_3924(self):
        if self.version is None:
            return None, "version unknown"
        if self._in_range((6, 42, 9), (6, 42, 13)) or \
                self._in_range((6, 43, 4), (6, 43, 7)):
            return True, f"RouterOS {self.version_raw} - internal API login bypass applies"
        return False, "not in affected range (6.42.9-6.42.13 / 6.43.4-6.43.7)"

    # CVE-2019-3978: unauth RCE via simple certificate
    def check_3978(self):
        if self.version is None:
            return None, "version unknown"
        if self._in_range((6, 42, 1), (6, 44, 4)):
            return True, f"RouterOS {self.version_raw} - simple cert RCE applies"
        return False, "not in affected range (6.42.1-6.44.4)"

    # CVE-2019-3979: unauth file read via simple certificate
    def check_3979(self):
        if self.version is None:
            return None, "version unknown"
        if self._in_range((6, 42, 1), (6, 44, 4)):
            return True, f"RouterOS {self.version_raw} - simple cert file read applies"
        return False, "not in affected range (6.42.1-6.44.4)"

    # CVE-2020-24571: Winbox buffer overflow (remote crash)
    def check_24571(self):
        if self.version is None:
            return None, "version unknown"
        if self._in_range((6, 44, 0), (6, 47, 9)):
            return True, f"RouterOS {self.version_raw} - Winbox BOF / crash applies"
        return False, "not in affected range (6.44.0-6.47.9)"

    # CVE-2017-10922: SMB RCE (versions 6.29.3 - 6.38.4)
    def check_10922(self):
        if self.version is None:
            return None, "version unknown"
        if self._in_range((6, 29, 3), (6, 38, 4)) and self._port_open(445):
            return True, f"SMB open on RouterOS {self.version_raw} - SMB RCE applies"
        if self._in_range((6, 29, 3), (6, 38, 4)):
            return None, f"affected version {self.version_raw} but SMB (445) closed"
        return False, "not in affected range (6.29.3-6.38.4)"

    # CVE-2017-10923: SMB privilege escalation (<= 6.38.4)
    def check_10923(self):
        if self.version is None:
            return None, "version unknown"
        if self._cmp((6, 38, 4)) <= 0 and self._is_6x():
            if self._port_open(445):
                return True, f"SMB open on RouterOS {self.version_raw} - SMB priv-esc applies"
            return None, f"affected version {self.version_raw} but SMB (445) closed"
        return False, "not in affected range (<= 6.38.4)"

    # CVE-2016-9322 / CVE-2016-9323: remote DoS (< 6.38.4)
    def check_9322(self):
        if self.version is None:
            return None, "version unknown"
        if self._is_6x() and self._cmp((6, 38, 4)) < 0:
            return True, f"RouterOS {self.version_raw} < 6.38.4 - remote DoS applies"
        return False, "patched (fixed in 6.38.4)"

    # CVE-2018-19299: DNS cache poisoning (< 6.43.5)
    def check_19299(self):
        if self.version is None:
            return None, "version unknown"
        if self._is_6x() and self._cmp((6, 43, 5)) < 0:
            return True, f"RouterOS {self.version_raw} < 6.43.5 - DNS cache poisoning applies"
        return False, "patched (fixed in 6.43.5)"

    # CVE-2023-30799: unauth RCE via WinBox / PoE (6.x < 6.49.10, 7.x < 7.9.1)
    def check_30799(self):
        if self.version is None:
            return None, "version unknown"
        vuln = (self._is_6x() and self._cmp((6, 49, 10)) < 0) or \
               (self.version[0] == 7 and self._cmp((7, 9, 1)) < 0)
        if vuln:
            if self._port_open(8291):
                return True, f"Winbox open on RouterOS {self.version_raw} - Winbox/PoE RCE applies"
            return None, f"affected version {self.version_raw} but Winbox (8291) closed"
        return False, "patched (fixed in 6.49.10 / 7.9.1)"

    # ------------------------------------------------------------------
    def run_all(self, pause=3):
        checks = [
            # --- modern ---
            ("CVE-2026-16347", "API brute-force / no rate limit", self.check_16347),
            ("CVE-2026-7668",  "SCEP endpoint OOB read",        self.check_7668),
            ("CVE-2026-39042", "libumsg unflatten() DoS",        self.check_39042),
            ("CVE-2026-14227", "API session-permission flaw",    self.check_14227),
            ("CVE-2025-61481", "WebFig cleartext HTTP",          self.check_61481),
            ("CVE-2025-10948", "libjson parse BOF",              self.check_10948),
            ("CVE-2025-42611", "cert trust store bypass",        self.check_42611),
            ("CVE-2025-6563",  "Hotspot XSS",                    self.check_6563),
            ("CVE-2024-27686", "SMB DoS",                        self.check_27686),
            # --- legacy ---
            ("CVE-2023-30799", "Winbox/PoE unauth RCE",          self.check_30799),
            ("CVE-2020-24571", "Winbox buffer overflow",         self.check_24571),
            ("CVE-2019-3978",  "simple cert RCE",                self.check_3978),
            ("CVE-2019-3979",  "simple cert file read",          self.check_3979),
            ("CVE-2019-3924",  "internal API login bypass",      self.check_3924),
            ("CVE-2018-14847", "Winbox dir traversal",           self.check_14847),
            ("CVE-2018-19299", "DNS cache poisoning",            self.check_19299),
            ("CVE-2017-10922", "SMB RCE",                        self.check_10922),
            ("CVE-2017-10923", "SMB priv-esc",                   self.check_10923),
            ("CVE-2016-9322",  "remote DoS (<6.38.4)",           self.check_9322),
        ]
        print(f"{WOW}\n{MikroTikHeader()}{N}")
        print(f"{W}[{P} * {W}]{B} Target      : {W}{self.ip}{N}")
        print(f"{W}[{P} * {W}]{B} Version     : {W}{self.version_raw}{N}"
              f"{B} (auto-detect){N}")
        if self.identity:
            print(f"{W}[{P} * {W}]{B} Identity    : {W}{self.identity}{N}")
        if self.mac:
            print(f"{W}[{P} * {W}]{B} MAC         : {W}{self.mac}{N}")
        print(f"{W}[{P} * {W}]{B} Timeout     : {W}{pause}s between checks{N}")
        print(f"{W}{'-' * 72}{N}")

        # ---- Connectivity / open-ports pre-check ----
        self._pre_check(pause)

        for cve, name, fn in checks:
            try:
                ok, detail = fn()
            except Exception as e:
                ok, detail = None, f"error: {e}"
            self.results.append(ok is True)
            if ok is True:
                mark = f"{vulnexploit}"
            elif ok is False:
                mark = f"{failexploit}"
            else:
                mark = f"{Y}INFO {N}"
            print(f"{W}[{P} {cve} {W}]{B} {name:<34} {W}| {mark} {W}{detail}{N}")
            time.sleep(pause)
        print(f"{W}{'-' * 72}{N}")
        vulnerable = sum(1 for r in self.results if r)
        print(f"{W}[{P} * {W}]{B} Done. Found {T}{vulnerable}{N}{B} vulnerable surface(s).{N}")


def MikroTikHeader():
    return f"""
    {B}6B 53 70 6C 6F 69 74 {N} {F2}CVE Scanner{N}
        {T}modern + legacy {W}|{N} {T}RouterOS 5.x / 6.x / 7.x{N}
    """
