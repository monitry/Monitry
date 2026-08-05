"""Onitry managed-API proxy.

Lets subscribers use Onitry without their own Anthropic API key — the app
sends a subscriber token instead of a key, this server calls Claude with
its own key, and bills the API cost into the subscription price.

Run locally:
    uvicorn server.app:app --reload

Required env vars: ANTHROPIC_API_KEY, STRIPE_SECRET_KEY, STRIPE_PRICE_ID,
STRIPE_WEBHOOK_SECRET (see server/README.md).

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

from server import billing, db

app = FastAPI(title="Onitry Managed API")

_client: anthropic.Anthropic | None = None

# $ per 1M tokens: (input, output) — keep in sync with ai/client.py's PRICING
PRICING = {
    "claude-haiku-4-5-20251001": (1.00, 5.00),
    "claude-sonnet-4-6": (3.00, 15.00),
    "claude-opus-4-8": (5.00, 25.00),
}
DEFAULT_MODEL = "claude-haiku-4-5-20251001"

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
    model: str = DEFAULT_MODEL


class CheckoutRequest(BaseModel):
    success_url: str
    cancel_url: str


@app.on_event("startup")
def _startup() -> None:
    db.init_db()


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


def _require_active_subscriber(token: str) -> dict:
    subscriber = db.get_subscriber(token)
    if subscriber is None:
        raise HTTPException(status_code=401, detail="Unknown token")
    if not subscriber["active"]:
        raise HTTPException(status_code=402, detail="Subscription inactive")
    return subscriber


@app.get("/v1/whoami")
def whoami(token: str) -> dict:
    subscriber = _require_active_subscriber(token)
    return {"email": subscriber["email"], "active": bool(subscriber["active"])}


@app.post("/v1/analyze")
def analyze(req: AnalyzeRequest) -> dict:
    _require_active_subscriber(req.token)
    model = req.model if req.model in PRICING else DEFAULT_MODEL

    user_text = f"""Task the user wants to complete: {req.task}

    Activity log so far:
    {req.context or "(empty — just started)"}

    notes:
    {req.notes or "no notes have been given so far"}

Analyze the screenshot and determine if the user is on task."""

    message = _get_client().messages.create(
        model=model,
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

    in_price, out_price = PRICING[model]
    cost = (message.usage.input_tokens / 1_000_000) * in_price
    cost += (message.usage.output_tokens / 1_000_000) * out_price
    db.record_usage(req.token, message.usage.input_tokens, message.usage.output_tokens, cost)

    parsed = _parse_json_response(message.content[0].text)
    parsed["cost"] = cost
    return parsed


@app.post("/v1/checkout")
def create_checkout(req: CheckoutRequest) -> dict:
    url = billing.create_checkout_session(req.success_url, req.cancel_url)
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
        token = db.create_subscriber(
            email=(obj.get("customer_details") or {}).get("email"),
            stripe_customer_id=obj.get("customer"),
            stripe_subscription_id=obj.get("subscription"),
            active=True,
        )
        # TODO: email `token` to the subscriber (SMTP/SendGrid — no credentials configured yet).
        # Until that's wired up, look tokens up manually via server/admin.py for support requests.
        print(f"[stripe] new subscriber token issued: {token} ({time.time()})")

    elif event_type in ("customer.subscription.updated", "customer.subscription.deleted"):
        active = obj.get("status") == "active"
        db.set_active_by_subscription(obj["id"], active)

    return {"received": True}
