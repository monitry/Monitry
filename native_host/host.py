"""Chrome native-messaging host for the Timecheck extension.

Chrome starts this script when the extension calls
``chrome.runtime.sendNativeMessage("com.onitry.host", {...})``. It answers one
message and exits. Commands:

  {"cmd": "ping"}    -> {"ok": true, "bridge": <is Onitry's bridge listening?>}
  {"cmd": "launch"}  -> starts the Onitry GUI (detached) unless it's already running

Register it with ``python native_host/install.py``.
"""

from __future__ import annotations

import json
import os
import socket
import struct
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import config  # noqa: E402 — needs ROOT on sys.path

MAX_MESSAGE_BYTES = 64 * 1024


def read_message() -> dict | None:
    header = sys.stdin.buffer.read(4)
    if len(header) < 4:
        return None
    (length,) = struct.unpack("<I", header)
    if length > MAX_MESSAGE_BYTES:
        return None
    try:
        data = json.loads(sys.stdin.buffer.read(length))
    except ValueError:
        return None
    return data if isinstance(data, dict) else None


def send_message(payload: dict) -> None:
    body = json.dumps(payload).encode()
    sys.stdout.buffer.write(struct.pack("<I", len(body)) + body)
    sys.stdout.buffer.flush()


def bridge_listening(port: int = config.BRIDGE_PORT) -> bool:
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=0.5):
            return True
    except OSError:
        return False


def launch_gui() -> dict:
    if bridge_listening():
        return {"ok": True, "launched": False, "already_running": True}
    os.makedirs(os.path.join(ROOT, "data"), exist_ok=True)
    log = open(os.path.join(ROOT, "data", "native_launch.log"), "ab")
    # Never inherit stdout: it's Chrome's message pipe. New session so closing
    # the pipe (or Chrome) doesn't take Onitry down with it.
    subprocess.Popen(
        [sys.executable, os.path.join(ROOT, "gui.py")],
        cwd=ROOT,
        stdin=subprocess.DEVNULL,
        stdout=log,
        stderr=log,
        start_new_session=True,
    )
    return {"ok": True, "launched": True}


def handle(message: dict | None) -> dict:
    cmd = (message or {}).get("cmd")
    if cmd == "ping":
        return {"ok": True, "bridge": bridge_listening()}
    if cmd == "launch":
        return launch_gui()
    return {"ok": False, "error": "unknown command"}


def main() -> None:
    try:
        send_message(handle(read_message()))
    except Exception as exc:  # report, don't crash silently on Chrome's side
        send_message({"ok": False, "error": str(exc)})


if __name__ == "__main__":
    main()
