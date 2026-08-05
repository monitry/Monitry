# Onitry Managed API

Lets subscribers use Onitry without their own Anthropic key. The desktop app sends
a subscriber token; this server validates it, calls Claude with its own key, and
tracks per-subscriber usage/cost. Stripe handles billing and tells this server
(via webhook) when to activate/deactivate a subscriber.

This is a from-scratch MVP — no hosting, database, or Stripe account existed
before this. Nothing here is deployed yet.

## Stack

- **FastAPI** — the proxy API
- **SQLite** (stdlib `sqlite3`, one file) — subscriber records + usage. Swap for
  Postgres later if this ever needs to run on more than one instance (SQLite
  doesn't handle concurrent writers across multiple processes well).
- **Stripe** — checkout + subscription billing

## 1. Set up Stripe

1. Create a Stripe account (or use an existing one) at stripe.com.
2. Create a **Product** called "Onitry Pro" with a **recurring Price** of $19/month.
   Copy the Price ID (`price_...`).
3. Get your **Secret key** from the Stripe dashboard (start with the test key
   while developing).
4. You'll register the **webhook** in step 4 below, once you know your server's URL.

## 2. Configure environment

```
cp server/.env.example server/.env
```

Fill in `ANTHROPIC_API_KEY`, `STRIPE_SECRET_KEY`, `STRIPE_PRICE_ID`. Leave
`STRIPE_WEBHOOK_SECRET` for step 4. This app reads env vars directly (no
`python-dotenv` dependency) — export them before running, e.g.:

```
export $(grep -v '^#' server/.env | xargs)
```

## 3. Run locally

```
pip install -r server/requirements.txt
uvicorn server.app:app --reload
```

Visit `http://localhost:8000/health` — should return `{"status": "ok"}`.

## 4. Wire up the Stripe webhook

For local testing, use the [Stripe CLI](https://stripe.com/docs/stripe-cli):

```
stripe listen --forward-to localhost:8000/webhooks/stripe
```

This prints a webhook signing secret (`whsec_...`) — put that in
`STRIPE_WEBHOOK_SECRET`. In production, register the webhook endpoint
(`https://your-domain/webhooks/stripe`) in the Stripe dashboard instead, for
these events: `checkout.session.completed`, `customer.subscription.updated`,
`customer.subscription.deleted`.

## 5. Test the flow end-to-end

```
stripe trigger checkout.session.completed
```

Then check the server logs for `[stripe] new subscriber token issued: ...`,
and confirm it in the DB:

```
python -m server.admin lookup <token>
```

Use that token as `token` in a `POST /v1/analyze` request to confirm the proxy works.

## What's NOT done yet

- **Email delivery.** When a subscriber checks out, a token is generated and
  logged server-side (see the `TODO` in `app.py`) but not emailed to them.
  Wire up SMTP or a provider like SendGrid/Postmark in the
  `checkout.session.completed` handler in `app.py` before this goes live.
  Until then, use `python -m server.admin lookup/issue` for support requests.
- **Deployment.** Not deployed anywhere. This runs anywhere Python does —
  Fly.io, Railway, Render, a plain VPS all work fine for a single-file SQLite
  app like this. Pick one when you're ready to go live; the `/health` endpoint
  is there for whatever platform's health check needs it.
- **Rate limiting / abuse protection.** A malicious or buggy client could hit
  `/v1/analyze` in a tight loop and run up API costs on a subscriber's flat
  $19/mo. Add a per-subscriber rate limit before opening this up publicly.
- **Checkout success page.** `/v1/checkout` returns a Stripe-hosted checkout
  URL; the website's "Get Onitry" button still just shows an alert() — wire
  it to call this endpoint and redirect once you're ready to launch billing.

## API

- `GET /health` — liveness check
- `GET /v1/whoami?token=...` — validate a token, returns `{email, active}`
- `POST /v1/analyze` — `{token, task, screenshot_b64, context, notes, model}` →
  same JSON shape as `ai/client.py`'s `analyze()`, plus a `cost` field
- `POST /v1/checkout` — `{success_url, cancel_url}` → `{url}` (Stripe Checkout link)
- `POST /webhooks/stripe` — Stripe webhook receiver

## Admin CLI

```
python -m server.admin lookup <token>
python -m server.admin issue <email> [--inactive]
python -m server.admin activate <token>
python -m server.admin deactivate <token>
```
