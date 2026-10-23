"""Local bridge between Onitry and the Timecheck browser extension.

The extension plans your day; Onitry watches your screen. The bridge lets them
talk so starting a focus block in the browser starts Onitry monitoring on that
exact task, and Onitry's on/off-task verdicts show up back in the browser.

Security model (it's a localhost server, so any web page could try to reach it):
  * binds to 127.0.0.1 only
  * every endpoint except /v1/ping needs the pairing code in an
    ``X-Onitry-Token`` header — a custom header, so a web page can't send it
    without a CORS preflight, and preflights are only answered for
    ``chrome-extension://`` origins
  * requests with a non-extension ``Origin`` are rejected outright
  * the Host header must be 127.0.0.1/localhost (blocks DNS-rebinding)

Stdlib only, so it adds no dependencies. The GUI owns a controller object that
implements ``status()``, ``start_task(task, details)``, ``stop()`` and
``pause(minutes)``, ``resume()`` and ``review(stats)`` (the weekly AI review, which uses Onitry's own API key so the
extension never holds one).
"""
from __future__ import annotations

import hmac
import json
import os
import secrets
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Protocol

DEFAULT_PORT = 47323
API_VERSION = 1
MAX_BODY_BYTES = 16 * 1024
MAX_REVIEW_BODY_BYTES = 64 * 1024  # weekly stats + journal excerpts
_CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"  # no 0/O/1/I to keep it typeable


class BridgeController(Protocol):
    def status(self) -> dict: ...
    def start_task(self, task: str, details: str = "") -> dict: ...
    def stop(self) -> dict: ...
    def pause(self, minutes: float) -> dict: ...
    def resume(self) -> dict: ...
    def review(self, stats: dict) -> dict: ...


def generate_code() -> str:
    raw = "".join(secrets.choice(_CODE_ALPHABET) for _ in range(8))
    return f"{raw[:4]}-{raw[4:]}"


def load_or_create_token(path: str) -> str:
    """The pairing code lives in data/ so it survives restarts but never hits git."""
    try:
        with open(path) as f:
            code = f.read().strip()
        if code:
            return code
    except OSError:
        pass
    code = generate_code()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(code)
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass
    return code


def _normalize(code: str) -> str:
    return code.strip().upper().replace(" ", "")


def make_handler(controller: BridgeController, token: str, port: int):
    allowed_hosts = {f"127.0.0.1:{port}", f"localhost:{port}"}

    class Handler(BaseHTTPRequestHandler):
        server_version = "OnitryBridge/1"

        # ── helpers ──────────────────────────────────────────────────────────
        def _origin(self) -> str | None:
            return self.headers.get("Origin")

        def _origin_ok(self) -> bool:
            origin = self._origin()
            return origin is None or origin.startswith("chrome-extension://")

        def _host_ok(self) -> bool:
            return self.headers.get("Host", "") in allowed_hosts

        def _authed(self) -> bool:
            given = _normalize(self.headers.get("X-Onitry-Token", ""))
            return bool(given) and hmac.compare_digest(given, _normalize(token))

        def _send(self, code: int, payload: dict | None = None) -> None:
            body = json.dumps(payload or {}).encode()
            self.send_response(code)
            origin = self._origin()
            if origin and origin.startswith("chrome-extension://"):
                self.send_header("Access-Control-Allow-Origin", origin)
                self.send_header("Vary", "Origin")
            self.send_header("Content-Type", "application/json")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _guard(self, need_auth: bool = True) -> bool:
            if not self._host_ok() or not self._origin_ok():
                self._send(403, {"error": "forbidden"})
                return False
            if need_auth and not self._authed():
                self._send(401, {"error": "bad or missing pairing code"})
                return False
            return True

        def _json_body(self, limit: int = MAX_BODY_BYTES) -> dict | None:
            length = int(self.headers.get("Content-Length") or 0)
            if length > limit:
                self._send(413, {"error": "body too large"})
                return None
            raw = self.rfile.read(length) if length else b"{}"
            try:
                data = json.loads(raw or b"{}")
            except json.JSONDecodeError:
                self._send(400, {"error": "invalid JSON"})
                return None
            if not isinstance(data, dict):
                self._send(400, {"error": "expected a JSON object"})
                return None
            return data

        # ── verbs ────────────────────────────────────────────────────────────
        def do_OPTIONS(self):  # noqa: N802 — http.server naming
            if not self._host_ok() or not self._origin_ok() or not self._origin():
                self.send_response(403)
                self.end_headers()
                return
            self.send_response(204)
            self.send_header("Access-Control-Allow-Origin", self._origin())
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type, X-Onitry-Token")
            self.send_header("Access-Control-Max-Age", "600")
            self.send_header("Vary", "Origin")
            self.end_headers()

        def do_GET(self):  # noqa: N802
            path = self.path.split("?", 1)[0]
            if path == "/v1/ping":
                if self._guard(need_auth=False):
                    self._send(200, {"ok": True, "app": "onitry", "api": API_VERSION, "paired": self._authed()})
                return
            if path == "/v1/status":
                if self._guard():
                    self._send(200, {"ok": True, **controller.status()})
                return
            if self._guard(need_auth=False):
                self._send(404, {"error": "not found"})

        def do_POST(self):  # noqa: N802
            path = self.path.split("?", 1)[0]
            if not self._guard():
                return
            data = self._json_body(MAX_REVIEW_BODY_BYTES if path == "/v1/review" else MAX_BODY_BYTES)
            if data is None:
                return
            if path == "/v1/task":
                task = str(data.get("task", "")).strip()[:300]
                details = str(data.get("details", "")).strip()[:1500]
                if not task:
                    self._send(400, {"error": "task is required"})
                    return
                self._send(200, {"ok": True, **controller.start_task(task, details)})
            elif path == "/v1/stop":
                self._send(200, {"ok": True, **controller.stop()})
            elif path == "/v1/pause":
                try:
                    minutes = float(data.get("minutes", 10))
                except (TypeError, ValueError):
                    minutes = -1
                if not 0 < minutes <= 240:
                    self._send(400, {"error": "minutes must be between 0 and 240"})
                    return
                self._send(200, {"ok": True, **controller.pause(minutes)})
            elif path == "/v1/resume":
                self._send(200, {"ok": True, **controller.resume()})
            elif path == "/v1/review":
                stats = data.get("stats")
                if not isinstance(stats, dict):
                    self._send(400, {"error": "stats object is required"})
                    return
                result = controller.review(stats)
                if result.get("error"):
                    self._send(503, {"error": result["error"]})
                else:
                    self._send(200, {"ok": True, **result})
            else:
                self._send(404, {"error": "not found"})

        def log_message(self, *args):
            pass  # keep the GUI's stdout quiet

    return Handler


class BridgeServer:
    """Runs the bridge on a daemon thread. ``port=0`` picks a free port (tests)."""

    def __init__(self, controller: BridgeController, token: str, host: str = "127.0.0.1", port: int = DEFAULT_PORT):
        self.controller = controller
        self.token = token
        self.host = host
        self._requested_port = port
        self._httpd: ThreadingHTTPServer | None = None
        self._thread: threading.Thread | None = None

    @property
    def port(self) -> int:
        return self._httpd.server_address[1] if self._httpd else self._requested_port

    def start(self) -> None:
        # Bind first with a placeholder handler so port=0 resolves, then install the real one.
        self._httpd = ThreadingHTTPServer((self.host, self._requested_port), BaseHTTPRequestHandler)
        self._httpd.daemon_threads = True
        self._httpd.RequestHandlerClass = make_handler(self.controller, self.token, self.port)
        self._thread = threading.Thread(target=self._httpd.serve_forever, name="onitry-bridge", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        if self._httpd:
            self._httpd.shutdown()
            self._httpd.server_close()
            self._httpd = None
