"""Verifies Google ID tokens from the desktop app's "Sign in with Google" flow.

Setup (Google Cloud Console):
  1. Create/select a project → APIs & Services → OAuth consent screen (External, testing mode is fine to start).
  2. Credentials → Create Credentials → OAuth client ID → Application type: "Desktop app".
  3. Copy the Client ID (and secret) into GOOGLE_CLIENT_ID / GOOGLE_CLIENT_SECRET env vars.

Desktop-app OAuth clients are "public clients" per Google's own docs — the
secret isn't treated as confidential the way a web server's would be, but
it's still required as a literal parameter in the token exchange.
"""
import os

from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token

GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "")

_request = google_requests.Request()


class InvalidGoogleToken(Exception):
    pass


def verify(id_token_str: str) -> dict:
    """Returns {"sub": ..., "email": ...} for a valid token, raises InvalidGoogleToken otherwise."""
    if not GOOGLE_CLIENT_ID:
        raise InvalidGoogleToken("Server has no GOOGLE_CLIENT_ID configured")
    try:
        claims = google_id_token.verify_oauth2_token(id_token_str, _request, GOOGLE_CLIENT_ID)
    except ValueError as exc:
        raise InvalidGoogleToken(str(exc)) from exc

    if claims.get("aud") != GOOGLE_CLIENT_ID:
        raise InvalidGoogleToken("Token audience mismatch")

    return {"sub": claims["sub"], "email": claims.get("email")}
