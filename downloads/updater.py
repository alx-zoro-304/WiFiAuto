#!/usr/bin/env python3
"""
updater.py — WiFi Auto official updater (by ALX-ZORO).

Checks the official site (version.json) for new releases. If a newer
version exists the user is ASKED before anything is downloaded. On
approval the new package is downloaded and installed next to this
script; every replaced file is first backed up as <name>.bak.

100% standard library — cross-platform (Windows & Linux).
"""

import json
import os
import shutil
import ssl
import sys
import tarfile
import tempfile
import threading
import urllib.request
import zipfile

UPDATE_URL = "https://alx-zoro-304.github.io/WiFiAuto/version.json"
DOWNLOAD_BASE = "https://alx-zoro-304.github.io/WiFiAuto/"
USER_AGENT = "WiFiAuto-Updater/2.0"

IS_WINDOWS = sys.platform.startswith("win")


def _safe_print(msg):
    try:
        print(msg)
    except Exception:
        pass


def fetch_version_info(timeout=8):
    """Fetch + parse version.json from the official site.
    Returns a dict or None on any failure (offline / site down)."""
    try:
        req = urllib.request.Request(UPDATE_URL,
                                     headers={"User-Agent": USER_AGENT})
        ctx = ssl.create_default_context()
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception:
        return None


def version_tuple(v):
    """'v2.0.1' / '2.0' -> (2, 0, 1)."""
    parts = []
    for p in str(v).strip().lstrip("v").split("."):
        try:
            parts.append(int(p))
        except ValueError:
            parts.append(0)
    while len(parts) < 3:
        parts.append(0)
    return tuple(parts)


def is_newer(remote, local):
    return version_tuple(remote) > version_tuple(local)


def _http_get(url, timeout=30):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    ctx = ssl.create_default_context()
    with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
        return r.read()


def install_update(script_dir, info, log=_safe_print):
    """Download the new package (ZIP on Windows, TAR.GZ on Linux) and
    install it next to the running script. Existing files are backed up
    as <name>.bak. Returns True on success."""
    downloads = info.get("downloads", {})
    if IS_WINDOWS:
        pkg = downloads.get("zip", "downloads/WiFiAuto_v2.zip")
        archive_type = "zip"
    else:
        pkg = downloads.get("linux_tar",
                            "downloads/WiFiAuto_v2-linux.tar.gz")
        archive_type = "tar"
    pkg_url = DOWNLOAD_BASE + pkg
    log(f"[updater] Downloading {pkg_url} ...")
    data = _http_get(pkg_url)
    tmp = None
    try:
        fd, tmp = tempfile.mkstemp(suffix=".pkg")
        os.close(fd)
        with open(tmp, "wb") as f:
            f.write(data)

        def extract(name, dest):
            if archive_type == "zip":
                with zipfile.ZipFile(tmp) as z:
                    with z.open(name) as src, open(dest, "wb") as out:
                        shutil.copyfileobj(src, out)
            else:
                with tarfile.open(tmp, "r:gz") as t:
                    member = t.getmember(name)
                    if member.isdir():
                        return
                    src = t.extractfile(member)
                    with open(dest, "wb") as out:
                        shutil.copyfileobj(src, out)

        names = []
        if archive_type == "zip":
            with zipfile.ZipFile(tmp) as z:
                names = z.namelist()
        else:
            with tarfile.open(tmp, "r:gz") as t:
                names = t.getnames()

        for name in names:
            if (name.endswith("/") or "__pycache__" in name
                    or name.endswith(".pyc") or ".." in name.split("/")):
                continue
            base = os.path.basename(name)
            if not base:
                continue
            dest = os.path.join(script_dir, name)
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            if os.path.exists(dest):
                bak = dest + ".bak"
                try:
                    if os.path.exists(bak):
                        os.remove(bak)
                    shutil.copy2(dest, bak)
                    log(f"[updater] Backup: {name} -> {name}.bak")
                except OSError:
                    pass
            extract(name, dest)
            log(f"[updater] Installed: {name}")
        return True
    finally:
        if tmp:
            try:
                os.remove(tmp)
            except OSError:
                pass


def start_update_check(root, script_dir, current_version, app_title="WiFi Auto",
                       version_field="current_version", log=None):
    """Non-blocking update check for tkinter apps. Called once at startup.

    - Fetches version.json in a background thread (silent on failure).
    - If a newer version exists, asks the user on the main thread.
    - On approval, downloads + installs in a background thread and shows
      a "restart required" dialog.

    log: optional callback (called from background threads).
    """
    log = log or _safe_print

    def worker():
        try:
            info = fetch_version_info()
        except Exception:
            return
        if not info:
            log("[updater] Could not reach the update server (offline?).")
            return
        remote = info.get(version_field) or info.get("current_version", "")
        if not is_newer(remote, current_version):
            log(f"[updater] Already on the latest version "
                f"({current_version}).")
            return

        def ask():
            notes = []
            if info.get("changelog"):
                notes = info["changelog"][0].get("notes_en") or []
            preview = "\n".join(f"  • {n}" for n in notes[:6]) or "  (see the site for details)"
            try:
                import tkinter.messagebox as mbox
                want = mbox.askyesno(
                    f"{app_title} - Update available",
                    "A new version is available!\n\n"
                    f"Current : v{current_version}\n"
                    f"New     : v{remote}\n\n"
                    f"What's new:\n{preview}\n\n"
                    "Download and install it now?")
            except Exception:
                return
            if not want:
                log(f"[updater] User declined update to v{remote}.")
                return

            def install_now():
                try:
                    ok = install_update(script_dir, info, log)
                except Exception as e:
                    ok = False
                    log(f"[updater] Update failed: {e}")
                if ok:
                    def done():
                        try:
                            import tkinter.messagebox as mbox
                            mbox.showinfo(
                                f"{app_title} - Update complete",
                                "The update was installed successfully.\n\n"
                                "Please restart the app to use the new "
                                "version.")
                        except Exception:
                            pass
                    root.after(0, done)

            threading.Thread(target=install_now, daemon=True).start()

        root.after(300, ask)

    threading.Thread(target=worker, daemon=True).start()