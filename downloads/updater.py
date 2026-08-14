#!/usr/bin/env python3
"""
updater.py — WiFi Auto official updater (by ALX-ZORO).

Checks the official site (version.json) for new releases. The version
number shown by the tools comes from the site, not from inside the
scripts. If a newer version exists the user is ASKED before anything is
downloaded — and only once per version. On approval the new package is
downloaded and installed in place: every replaced file is backed up as
a single <name>.bak, and files from the previous package that no longer
exist in the new one are deleted (clean replace, no leftovers).

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
USER_AGENT = "WiFiAuto-Updater/2.3"

IS_WINDOWS = sys.platform.startswith("win")

STATE_FILE = ".updater_state.json"


def _safe_print(msg):
    try:
        print(msg)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Persistent state — keeps the tool in sync with the site's version.
# ---------------------------------------------------------------------------
def _state_path(script_dir):
    return os.path.join(script_dir, STATE_FILE)


def load_state(script_dir):
    try:
        with open(_state_path(script_dir), "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_state(script_dir, **fields):
    try:
        state = load_state(script_dir)
        state.update(fields)
        with open(_state_path(script_dir), "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
    except OSError:
        pass


# ---------------------------------------------------------------------------
# Networking
# ---------------------------------------------------------------------------
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


# ---------------------------------------------------------------------------
# Install — clean in-place replace
# ---------------------------------------------------------------------------
def install_update(script_dir, info, log=_safe_print):
    """Download the new package (ZIP on Windows, TAR.GZ on Linux) and
    install it next to the running script. Every replaced file gets a
    single <name>.bak; files from the previous package that are not in
    the new package are deleted. Returns True on success."""
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

        keep = set()
        for name in names:
            if (name.endswith("/") or "__pycache__" in name
                    or name.endswith(".pyc") or ".." in name.split("/")):
                continue
            if not os.path.basename(name):
                continue
            keep.add(name)

        # The packages now ship with a top-level folder
        # (WiFiAuto_v2/ or WiFiAuto_v2-linux/) so users extract a neat
        # folder. When installing we strip that prefix so files land
        # next to the running script, exactly like before.
        strip_prefix = ""
        if names:
            first = next((n for n in names if n and not n.endswith("/")), "")
            if "/" in first:
                top = first.split("/", 1)[0]
                if all(not n or n.split("/", 1)[0] == top for n in names):
                    strip_prefix = top + "/"

        def rel_path(name):
            return name[len(strip_prefix):] if strip_prefix else name

        # Clean replace: remove files installed by the previous package
        # that are no longer part of the new package (no leftovers).
        state = load_state(script_dir)
        for old in state.get("installed_files", []):
            if old in {rel_path(k) for k in keep}:
                continue
            if "__pycache__" in old or old.endswith(".pyc"):
                continue
            stale = os.path.join(script_dir, old)
            if os.path.isfile(stale):
                try:
                    os.remove(stale)
                    log(f"[updater] Removed obsolete: {old}")
                except OSError:
                    pass

        installed = []
        for name in keep:
            rel = rel_path(name)
            dest = os.path.join(script_dir, rel)
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            if os.path.exists(dest):
                bak = dest + ".bak"
                try:
                    if os.path.exists(bak):
                        os.remove(bak)
                    shutil.copy2(dest, bak)
                    log(f"[updater] Backup: {rel} -> {rel}.bak")
                except OSError:
                    pass
            extract(name, dest)
            log(f"[updater] Installed: {rel}")
            installed.append(rel)

        save_state(script_dir, installed_files=sorted(installed))
        return True
    finally:
        if tmp:
            try:
                os.remove(tmp)
            except OSError:
                pass


# ---------------------------------------------------------------------------
# Entry point — non-blocking check for tkinter apps
# ---------------------------------------------------------------------------
def start_update_check(root, script_dir, current_version, app_title="WiFi Auto",
                       version_field="current_version", log=None,
                       on_version=None):
    """Non-blocking update check for tkinter apps. Called once at startup.

    - Fetches version.json in a background thread (silent on failure).
    - The version number comes FROM THE SITE: after a successful check the
      tool adopts the site's version (via on_version callback) even if no
      update is needed — so the number inside the tool always matches
      the site.
    - Asks the user only when the site version is newer than the version
      recorded locally — and only ONCE per version (declined versions are
      remembered and never asked again unless a newer one appears).
    - On approval, downloads + installs in a background thread and shows
      a "restart required" dialog.

    on_version: optional callback(remote_version) called on the main
                thread after a successful check — update the UI there.
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

        # Version comes from the site — adopt it (main thread, UI update).
        if remote:
            def sync_ui():
                if on_version:
                    try:
                        on_version(str(remote))
                    except Exception:
                        pass
            root.after(0, sync_ui)

        state = load_state(script_dir)
        installed = state.get("installed_version") or str(current_version)
        declined = state.get("declined_version") or ""

        if not is_newer(remote, installed):
            log(f"[updater] Already on the latest version "
                f"({installed}).")
            return
        if declined and not is_newer(remote, declined):
            log(f"[updater] v{remote} was declined before — skipping.")
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
                    f"Current : v{installed}\n"
                    f"New     : v{remote}\n\n"
                    f"What's new:\n{preview}\n\n"
                    "Download and install it now?")
            except Exception:
                return
            if not want:
                log(f"[updater] User declined update to v{remote}.")
                save_state(script_dir, declined_version=str(remote))
                return

            def install_now():
                try:
                    ok = install_update(script_dir, info, log)
                except Exception as e:
                    ok = False
                    log(f"[updater] Update failed: {e}")
                if ok:
                    save_state(script_dir,
                               installed_version=str(remote),
                               declined_version="")
                    # Keep the UI in sync with the newly installed version.
                    def sync_after():
                        if on_version:
                            try:
                                on_version(str(remote))
                            except Exception:
                                pass

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
                    root.after(0, sync_after)

            threading.Thread(target=install_now, daemon=True).start()

        root.after(300, ask)

    threading.Thread(target=worker, daemon=True).start()