#!/usr/bin/python3
# coding=utf-8
# Mock RouterOS API server - emulates a real MikroTik RouterOS API (8728)
# for testing api_shell.py without a real device.
#   - plain /login (old-style, e.g. admin/mock123)
#   - challenge /login (6.43+, e.g. secure/s12345)
#   - /user/print, /system/identity/print, /system/resource/print, /user/add
# Usage: python3 mock_api_server.py [port]

import hashlib
import socket
import struct
import sys
import threading
import time

USERS = {
    "admin":  ("mock123", "plain"),
    "secure": ("s12345", "challenge"),
}
CHALLENGE = b"\x13\x37\x00\x99\xab\xcd\xef\x01\x02\x03\x04\x05\x06\x07\x08\x09"


def recvn(s, n):
    out = b""
    while len(out) < n:
        c = s.recv(n - len(out))
        if not c:
            raise ConnectionError
        out += c
    return out


def handle(conn, addr):
    print(f"[mock] connection from {addr}")
    try:
        while True:
            head = recvn(conn, 2)
            ln = struct.unpack(">H", head)[0]
            body = recvn(conn, ln).decode("utf-8", "replace")
            lines = body.split("\n")
            cmd = lines[0]
            fields = {}
            for line in lines[1:]:
                if line.startswith("="):
                    k, _, v = line[1:].partition("=")
                    fields[k] = v
            print(f"[mock] <- {cmd} {fields}")

            if cmd == "/login":
                name = fields.get("name", "")
                if fields.get("response"):
                    ok = hashlib.md5(b"\x00" + USERS.get(
                        name, ("", "plain"))[0].encode()
                        + CHALLENGE).hexdigest() == fields["response"]
                    reply = b"!done" if ok else b"!trap\n=message=invalid user name or password"
                elif name not in USERS:
                    reply = b"!trap\n=message=invalid user name or password"
                else:
                    pwd = fields.get("password", "")
                    mode = USERS[name][1]
                    if mode == "challenge":
                        reply = b"!done\n=ret=" + CHALLENGE.hex().encode()
                    elif USERS[name][0] == pwd:
                        reply = b"!done"
                    else:
                        reply = b"!trap\n=message=invalid user name or password"
            elif cmd == "/user/print":
                rows = [
                    b"!re\n=name=admin\n=group=full\n=address=0.0.0.0/0",
                    b"!re\n=name=secure\n=group=full\n=address=10.0.0.78/32",
                    b"!re\n=name=guest\n=group=read\n=address=0.0.0.0/0",
                    b"!done",
                ]
                for r in rows:
                    conn.sendall(struct.pack(">H", len(r)) + r)
                continue
            elif cmd == "/system/identity/print":
                reply = b"!re\n=identity=MockRouterABDO\n!done"
            elif cmd == "/system/resource/print":
                reply = (b"!re\n=uptime=1w2d13:04:05\n=version=6.47.9 "
                         b"(long-term)\n=board-name=x86\n!done")
            elif cmd == "/user/add":
                print(f"[mock] !!! BACKDOOR ADDED: "
                      f"{fields.get('name')} / {fields.get('password')} "
                      f"group={fields.get('group')}")
                reply = b"!done"
            else:
                reply = b"!trap\n=message=no such command prefix"
            conn.sendall(struct.pack(">H", len(reply)) + reply)
    except ConnectionError:
        pass
    except Exception as e:
        print(f"[mock] error: {e}")
    finally:
        conn.close()
        print(f"[mock] closed {addr}")


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8728
    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(("127.0.0.1", port))
    s.listen(5)
    print(f"[mock] RouterOS API mock listening on 127.0.0.1:{port}")
    print(f"[mock] users: admin/mock123 (plain), secure/s12345 (challenge)")
    while True:
        conn, addr = s.accept()
        threading.Thread(target=handle, args=(conn, addr), daemon=True).start()


if __name__ == "__main__":
    main()