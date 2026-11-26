"""LEGACY — NOT OFFERED. Onitry is free and has no accounts; nothing in the default
edition ever calls this module. Only reachable with ONITRY_ENABLE_LEGACY_EDITIONS=1
and ONITRY_EDITION=managed. Kept so the paid design can be revived, or deleted with server/.

"Sign in with Google" for a desktop app — the loopback-redirect flow from RFC 8252.

Blocking by design (waits on the user's browser + a local HTTP callback) — the
GUI is expected to run login_with_google() on a background thread, not the
tkinter main thread.

Setup: create a Google Cloud OAuth client (type: "Desktop app") and set
GOOGLE_CLIENT_ID / GOOGLE_CLIENT_SECRET — see server/README.md.
"""
import http.server
import secrets
import urllib.parse
import webbrowser

import httpx

AUTH_ENDPOINT = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"


class GoogleLoginError(Exception):
    pass


class _CallbackHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):  # noqa: N802 (http.server's naming convention, not ours)
        params = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        self.server.auth_code = params.get("code", [None])[0]
        self.server.auth_state = params.get("state", [None])[0]
        self.server.auth_error = params.get("error", [None])[0]

        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        message = "Signed in — you can close this tab." if self.server.auth_code else "Sign-in failed — you can close this tab."
        self.wfile.write(f"<html><body><p>{message}</p></body></html>".encode())

    def log_message(self, *args):
        pass  # silence the default request logging to stdout


def login_with_google(client_id: str, client_secret: str, timeout: float = 120.0) -> str:
    """Runs the full flow and returns a verified Google ID token (a JWT)."""
    if not client_id:
        raise GoogleLoginError("No GOOGLE_CLIENT_ID configured for this build")

    state = secrets.token_urlsafe(16)

    # Reserve the callback port before building the auth URL, since redirect_uri must match exactly.
    server = http.server.HTTPServer(("localhost", 0), _CallbackHandler)
    port = server.server_address[1]
    redirect_uri = f"http://localhost:{port}"

    auth_url = AUTH_ENDPOINT + "?" + urllib.parse.urlencode({
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "openid email",
        "state": state,
        "prompt": "select_account",
    })
    webbrowser.open(auth_url)

    server.timeout = timeout
    server.auth_code = None
    server.auth_state = None
    server.auth_error = None
    server.handle_request()
    server.server_close()

    if server.auth_error:
        raise GoogleLoginError(server.auth_error)
    if server.auth_code is None:
        raise GoogleLoginError("Timed out waiting for Google sign-in")
    if server.auth_state != state:
        raise GoogleLoginError("state mismatch — possible CSRF, aborting")

    token_resp = httpx.post(TOKEN_ENDPOINT, data={
        "code": server.auth_code,
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code",
    }, timeout=30.0)
    token_resp.raise_for_status()
    id_token = token_resp.json().get("id_token")
    if not id_token:
        raise GoogleLoginError("Google didn't return an id_token")
    return id_token
