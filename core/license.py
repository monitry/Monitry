"""LEGACY — NOT OFFERED. Onitry is free and the default edition never calls
this module; it only runs if ONITRY_ENABLE_LEGACY_EDITIONS=1 and
ONITRY_EDITION=byok. Kept so the paid design can be revived, or deleted with server/.

Paid-BYOK edition license check — verified once against server/, then cached locally.

After a $30 one-time Stripe purchase, the webhook mints a license token
(see server/app.py + server/db.py's PLAN_BYOK). The desktop app just needs
to confirm that token is valid once; after that it runs fully offline,
direct to Anthropic with the user's own key — this module is never touched
again until/unless the user re-verifies (e.g. after re-entering the key).
"""
import httpx


class LicenseCheckFailed(Exception):
    pass


def verify(api_url: str, token: str, timeout: float = 10.0) -> bool:
    """Returns True/False for a definitive answer from the server.

    Raises LicenseCheckFailed if the server couldn't be reached at all —
    callers should treat that differently from "invalid" (e.g. let the app
    keep running on a previously-cached verification rather than lock out
    a paying user just because they're offline).
    """
    if not token:
        return False
    try:
        resp = httpx.post(f"{api_url}/v1/license/verify", json={"token": token}, timeout=timeout)
        resp.raise_for_status()
    except httpx.HTTPError as exc:
        raise LicenseCheckFailed(str(exc)) from exc
    return bool(resp.json().get("valid"))
