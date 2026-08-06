"""Onitry managed-API proxy + accounts + licensing.

Three product editions share this server:
  - "byok"    ($30 one-time) — never calls /v1/analyze. Only ever hits
              /v1/license/verify, once (or occasionally), then runs fully
              offline against the user's own Anthropic key.
  - "managed" (free 1hr/day, or $19/mo for 10hr/day) — signs in with Google
              via /v1/auth/google, then every check goes through
              /v1/analyze, which is model-locked to Haiku and enforces the
              daily cap server-side (never trust the client for either).
  - "dev"     — unrestricted, doesn't touch this server at all unless the
              developer explicitly flips on managed mode for testing.

Run locally:
    uvicorn server.app:app --reload

Required env vars: ANTHROPIC_API_KEY, STRIPE_SECRET_KEY, STRIPE_BYOK_PRICE_ID,
STRIPE_MANAGED_PRICE_ID, STRIPE_WEBHOOK_SECRET, GOOGLE_CLIENT_ID — see
server/README.md for how to obtain each one.

NOTE: the system prompt and JSON-extraction logic here are intentionally
kept in sync with (but not imported from) ai/client.py — this module must
stay deployable without the desktop app's dependencies (tkinter, mss, cv2).
"""
import json
import os
import time

import anthropic
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel

from server import billing, db, google_auth

app = FastAPI(title="Onitry Managed API")

_client: anthropic.Anthropic | None = None

# $ per 1M tokens: (input, output) — keep in sync with ai/client.py's PRICING.
# Managed edition is ALWAYS Haiku — enforced here, not trusted from the client.
PRICING = {
    "claude-haiku-4-5-20251001": (1.00, 5.00),
    "claude-sonnet-4-6": (3.00, 15.00),
    "claude-opus-4-8": (5.00, 25.00),
}
MANAGED_MODEL = "claude-haiku-4-5-20251001"

# Daily wall-clock monitoring caps, in seconds, by plan.
PLAN_LIMITS = {
    db.PLAN_FREE: 60 * 60,       # 1 hour/day
    db.PLAN_PAID: 10 * 60 * 60,  # 10 hours/day
}

SYSTEM_PROMPT = """You are a productivity monitor. Given a screenshot of the user's screen,
an activity log, and the task they want to accomplish, determine if they are on task.

Respond ONLY with a JSON object (no markdown, no extra text):
{
  "onTask": true or false,
  "interrupt": true or false (whether you want the reminder to interrupt the tab or be a softer notification),
  "activity": "brief description of what they appear to be doing right now",
  "reminder": "if off-task, a short firm reminder of what they should be doing instead or a gentle notice if they are taking a while to do something",
  "notes": "you will be given notes from previous calls, modify it if necessary however keep it short and don't add if you don't need to"
}

Be realistic — browsing documentation, writing code, or reading relevant material counts as on-task.
Social media, YouTube, games, or unrelated browsing is off-task."""


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    return _client


def _parse_json_response(raw: str) -> dict:
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw)


class AnalyzeRequest(BaseModel):
    token: str
    task: str
    screenshot_b64: str
    context: str = ""
    notes: str = ""
    elapsed_seconds: float = 0.0  # wall-clock time since the last check — what the daily cap counts


class GoogleAuthRequest(BaseModel):
    id_token: str


class LicenseVerifyRequest(BaseModel):
    token: str


class CheckoutRequest(BaseModel):
    success_url: str
    cancel_url: str
    subscriber_token: str | None = None  # required for a managed-plan upgrade, unused for BYOK


@app.on_event("startup")
def _startup() -> None:
    db.init_db()


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


def _require_managed_subscriber(token: str) -> dict:
    subscriber = db.get_subscriber(token)
    if subscriber is None:
        raise HTTPException(status_code=401, detail="Unknown token")
    if subscriber["plan"] not in PLAN_LIMITS:
        raise HTTPException(status_code=403, detail="Token is not a managed-plan account")
    if not subscriber["active"]:
        raise HTTPException(status_code=402, detail="Account inactive")
    return subscriber


@app.get("/v1/whoami")
def whoami(token: str) -> dict:
    subscriber = _require_managed_subscriber(token)
    cap = PLAN_LIMITS[subscriber["plan"]]
    return {
        "email": subscriber["email"],
        "plan": subscriber["plan"],
        "active": bool(subscriber["active"]),
        "daily_cap_seconds": cap,
        "daily_remaining_seconds": db.remaining_daily_seconds(subscriber, cap),
    }


@app.post("/v1/auth/google")
def auth_google(req: GoogleAuthRequest) -> dict:
    try:
        claims = google_auth.verify(req.id_token)
    except google_auth.InvalidGoogleToken as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc

    subscriber = db.get_or_create_by_google(claims["sub"], claims.get("email"))
    cap = PLAN_LIMITS[subscriber["plan"]]
    return {
        "token": subscriber["token"],
        "plan": subscriber["plan"],
        "email": subscriber["email"],
        "daily_cap_seconds": cap,
    }


@app.post("/v1/license/verify")
def verify_license(req: LicenseVerifyRequest) -> dict:
    return {"valid": db.verify_byok_license(req.token)}


@app.post("/v1/analyze")
def analyze(req: AnalyzeRequest) -> dict:
    subscriber = _require_managed_subscriber(req.token)
    cap = PLAN_LIMITS[subscriber["plan"]]

    usage = db.check_and_consume_daily_usage(req.token, max(0.0, req.elapsed_seconds), cap)
    if not usage["allowed"]:
        raise HTTPException(
            status_code=429,
            detail=f"Daily limit reached. {usage['remaining']:.0f}s remaining today.",
        )

    user_text = f"""Task the user wants to complete: {req.task}

    Activity log so far:
    {req.context or "(empty — just started)"}

    notes:
    {req.notes or "no notes have been given so far"}

Analyze the screenshot and determine if the user is on task."""

    message = _get_client().messages.create(
        model=MANAGED_MODEL,
        max_tokens=512,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/jpeg",
                            "data": req.screenshot_b64,
                        },
                    },
                    {"type": "text", "text": user_text},
                ],
            }
        ],
    )

    in_price, out_price = PRICING[MANAGED_MODEL]
    cost = (message.usage.input_tokens / 1_000_000) * in_price
    cost += (message.usage.output_tokens / 1_000_000) * out_price
    db.record_usage(req.token, message.usage.input_tokens, message.usage.output_tokens, cost)

    parsed = _parse_json_response(message.content[0].text)
    parsed["cost"] = cost
    parsed["daily_remaining_seconds"] = usage["remaining"]
    return parsed


@app.post("/v1/checkout/byok")
def checkout_byok(req: CheckoutRequest) -> dict:
    url = billing.create_byok_checkout_session(req.success_url, req.cancel_url)
    return {"url": url}


@app.post("/v1/checkout/upgrade")
def checkout_upgrade(req: CheckoutRequest) -> dict:
    if not req.subscriber_token:
        raise HTTPException(status_code=400, detail="subscriber_token is required to upgrade")
    url = billing.create_managed_upgrade_session(req.success_url, req.cancel_url, req.subscriber_token)
    return {"url": url}


@app.post("/webhooks/stripe")
async def stripe_webhook(request: Request) -> dict:
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")
    try:
        event = billing.verify_webhook(payload, sig_header)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    event_type = event["type"]
    obj = event["data"]["object"]

    if event_type == "checkout.session.completed":
        if obj.get("mode") == "payment":
            # BYOK $30 one-time purchase — mint a fresh license, no prior account needed.
            token = db.create_byok_license(
                email=(obj.get("customer_details") or {}).get("email"),
                stripe_customer_id=obj.get("customer"),
            )
            # TODO: email `token` to the buyer (SMTP/SendGrid — no credentials configured yet).
            # Until that's wired up, use `python -m server.admin lookup` for support requests.
            print(f"[stripe] new BYOK license issued: {token} ({time.time()})")

        elif obj.get("mode") == "subscription":
            # Managed plan upgrade — client_reference_id is the existing Google-linked token.
            subscriber_token = obj.get("client_reference_id")
            if subscriber_token:
                db.upgrade_to_paid(
                    subscriber_token,
                    stripe_customer_id=obj.get("customer"),
                    stripe_subscription_id=obj.get("subscription"),
                )

    elif event_type in ("customer.subscription.deleted",):
        db.downgrade_to_free_by_subscription(obj["id"])

    elif event_type == "customer.subscription.updated":
        if obj.get("status") != "active":
            db.downgrade_to_free_by_subscription(obj["id"])

    return {"received": True}
