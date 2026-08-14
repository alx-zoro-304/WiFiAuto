#!/usr/bin/env python3
"""
MAC Changer Pro - Advanced MAC address changer (Windows GUI).
Detects ALL network adapters (WiFi + Ethernet) with driver descriptions.
Fully self-contained: changes the MAC using only Windows built-ins passed
inline to PowerShell (disable adapter -> write NetworkAddress registry
value -> enable adapter). No external .exe tools, no .ps1 script files.

Run as Administrator.
"""

import ctypes
import os
import re
import subprocess
import sys
import threading
import time
import tkinter as tk
from tkinter import ttk, messagebox

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from updater import start_update_check

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
APP_TITLE = "MAC Changer Pro"
APP_VERSION = "2.4"


def is_admin():
    try:
        import ctypes
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False


def run(cmd, timeout=120):
    try:
        kwargs = dict(capture_output=True, text=True, errors="replace",
                      timeout=timeout)
        kwargs["creationflags"] = (
            getattr(subprocess, "CREATE_NO_WINDOW", 0) | 0x08000000)
        p = subprocess.run(cmd, **kwargs)
        return p.returncode, p.stdout, p.stderr
    except (subprocess.TimeoutExpired, OSError) as e:
        return -1, "", str(e)


def normalize_mac(value):
    s = value.strip().lower().replace("-", "").replace(":", "").replace(".", "")
    if len(s) != 12 or not re.fullmatch(r"[0-9a-f]{12}", s):
        return None
    return s


def pretty_mac(plain):
    return ":".join(plain[i:i + 2] for i in range(0, 12, 2))


def get_adapters():
    adapters = []
    rc, out, _ = run(["powershell", "-Command",
                      "Get-NetAdapter | ForEach-Object { "
                      "Write-Output ($_.Name + '|' + $_.MacAddress + '|' + "
                      "$_.InterfaceDescription + '|' + $_.Status) }"])
    if rc == 0 and out.strip():
        for line in out.splitlines():
            parts = line.split("|")
            if len(parts) >= 3:
                adapters.append({
                    "name": parts[0].strip(),
                    "mac": parts[1].strip().replace("-", ":"),
                    "desc": parts[2].strip(),
                    "status": parts[3].strip() if len(parts) > 3 else "",
                })
    return adapters


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
                        "Bypass", "-Command", ps], timeout=60)
    for line in (out + err).splitlines():
        if line.strip():
            log(line.strip())
    return rc == 0 and "OK" in out and "REVERTED" not in out


class MACChangerApp:
    def __init__(self, root):
        self.root = root
        self.root.title(f"MAC Changer Pro v{APP_VERSION}")
        self.root.geometry("680x520")
        self.root.minsize(600, 420)

        self.adapters = get_adapters()
        self.busy = False

        pad = 6

        frm = ttk.LabelFrame(self.root, text="Network Adapter", padding=pad)
        frm.pack(fill=tk.X, padx=pad, pady=pad)

        self.adapter_var = tk.StringVar()
        self.combo = ttk.Combobox(frm, textvariable=self.adapter_var,
                                  state="readonly", width=50)
        self.combo.pack(fill=tk.X, padx=4, pady=2)
        self.combo.bind("<<ComboboxSelected>>", self._on_select)

        self.details_var = tk.StringVar(value="Select an adapter...")
        ttk.Label(frm, textvariable=self.details_var,
                  foreground="#555").pack(anchor=tk.W, padx=4)

        self.mac_var = tk.StringVar()
        frm2 = ttk.LabelFrame(self.root, text="New MAC Address",
                              padding=pad)
        frm2.pack(fill=tk.X, padx=pad, pady=pad)

        entry = ttk.Entry(frm2, textvariable=self.mac_var, width=30,
                          font=("Consolas", 12))
        entry.pack(side=tk.LEFT, padx=4)
        ttk.Button(frm2, text="Apply MAC", command=self.apply).pack(
            side=tk.LEFT, padx=4)
        ttk.Button(frm2, text="Restore Original",
                   command=self.restore).pack(side=tk.LEFT, padx=4)
        ttk.Button(frm2, text="Refresh", command=self.refresh).pack(
            side=tk.LEFT, padx=4)
        entry.bind("<Return>", lambda e: self.apply())

        self.status_var = tk.StringVar()
        ttk.Label(self.root, textvariable=self.status_var,
                  anchor=tk.W).pack(fill=tk.X, padx=8)

        self.ver_lbl = ttk.Label(self.root, text=f"{APP_TITLE} v{APP_VERSION}",
                                 anchor=tk.E, foreground="#555555")
        self.ver_lbl.pack(fill=tk.X, padx=8)

        logfrm = ttk.LabelFrame(self.root, text="Log", padding=pad)
        logfrm.pack(fill=tk.BOTH, expand=True, padx=pad, pady=pad)
        self.log_text = tk.Text(logfrm, height=12, state=tk.DISABLED)
        sb = ttk.Scrollbar(logfrm, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=sb.set)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)

        self._fill_combo()
        if not is_admin():
            self.log("[WARNING] Not running as Administrator! "
                     "Right-click and select 'Run as administrator'.")
        self.root.after(2500, self._check_for_updates)

    def _check_for_updates(self):
        """Ask the official site if a newer version exists (non-blocking)."""
        start_update_check(
            self.root, SCRIPT_DIR, APP_VERSION, APP_TITLE,
            version_field="mac_changer_version",
            log=self.log,
            on_version=self._apply_remote_version)

    def _apply_remote_version(self, ver):
        """Version comes from the site — sync every place that shows it."""
        global APP_VERSION
        APP_VERSION = str(ver)
        try:
            self.root.title(f"{APP_TITLE} v{APP_VERSION}")
            if getattr(self, "ver_lbl", None) is not None:
                self.ver_lbl.config(text=f"{APP_TITLE} v{APP_VERSION}")
        except Exception:
            pass

    def _fill_combo(self):
        names = [f"{a['name']}  [{a['desc']}]" for a in self.adapters]
        self.combo["values"] = names
        wifi = [i for i, a in enumerate(self.adapters)
                if "wi-fi" in a["desc"].lower() or "wireless" in a["desc"].lower()]
        if wifi:
            idx = wifi[0]
        elif self.adapters:
            idx = 0
        else:
            self.log("[WARNING] No adapters found via Get-NetAdapter.")
            return
        self.combo.current(idx)
        self._on_select()

    def _on_select(self, _event=None):
        idx = self.combo.current()
        if idx < 0:
            return
        a = self.adapters[idx]
        self.details_var.set(f"MAC: {a['mac']} | Status: {a['status']}")

    def _selected(self):
        idx = self.combo.current()
        return self.adapters[idx] if 0 <= idx < len(self.adapters) else None

    def log(self, text):
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.insert(tk.END, text + "\n")
        self.log_text.see(tk.END)
        self.log_text.configure(state=tk.DISABLED)

    def _log_worker(self, text):
        self.root.after(0, self.log, text)

    def apply(self):
        if self.busy:
            return
        a = self._selected()
        if not a:
            return
        mac = normalize_mac(self.mac_var.get())
        if not mac:
            messagebox.showwarning("MAC Changer",
                                   "Enter a valid MAC (AA:BB:CC:DD:EE:FF "
                                   "or AABBCCDDEEFF).")
            return
        self.busy = True
        self.status_var.set(f"Changing MAC of {a['name']} ...")
        threading.Thread(target=self._do_change,
                         args=(a["name"], pretty_mac(mac), None),
                         daemon=True).start()

    def restore(self):
        if self.busy:
            return
        a = self._selected()
        if not a or not a["mac"]:
            return
        self.busy = True
        self.status_var.set(f"Restoring original MAC of {a['name']} ...")
        threading.Thread(target=self._do_change,
                         args=(a["name"], a["mac"], "restore"),
                         daemon=True).start()

    def refresh(self):
        self.log("Refreshing adapter list...")
        self.adapters = get_adapters()
        self._fill_combo()
        self.log(f"Found {len(self.adapters)} adapter(s).")

    def _do_change(self, adapter_name, mac, mode):
        def log(m):
            self._log_worker(m)
        ok = False
        for attempt in (1, 2):
            ok = change_mac_native(adapter_name, mac.replace(":", ""), log)
            if ok:
                break
            log(f"[ERROR] Attempt {attempt} failed - the driver reverted "
                f"the MAC change.")
            time.sleep(2)
        self.root.after(0, self._finished, ok, adapter_name, mac, mode)

    def _finished(self, ok, adapter_name, mac, mode):
        self.busy = False
        self.adapters = get_adapters()
        self._fill_combo()
        if ok:
            self.status_var.set(f"DONE: {adapter_name} MAC is now {mac}")
            messagebox.showinfo("MAC Changer",
                                f"MAC of {adapter_name} changed to:\n{mac}")
        else:
            self.status_var.set(f"FAILED: {adapter_name} driver reverted "
                                "the MAC change.")
            messagebox.showerror(
                "MAC Changer - Failed",
                f"The driver of {adapter_name} reverted the MAC.\n\n"
                "The adapter was disabled, the NetworkAddress registry "
                "value written, and re-enabled, but the driver reset it. "
                "This adapter's driver may block MAC spoofing.\n\n"
                "Options:\n"
                "1. Try an older Realtek driver that exposes the "
                "'Network Address' property.\n"
                "2. Use another adapter (Ethernet or USB Wi-Fi).\n"
                "3. Reboot Windows - the MAC may stick after a full "
                "restart (the registry value is still written).")

    def _on_close(self):
        self.root.destroy()


def main():
    root = tk.Tk()
    try:
        style = ttk.Style()
        if "clam" in style.theme_names():
            style.theme_use("clam")
    except tk.TclError:
        pass
    MACChangerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()