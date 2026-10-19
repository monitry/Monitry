# Onitry Server

Backs two of Full Focus's three product editions (Full Focus is Onitry's
screenshot-monitoring product — see the root README):

- **`byok`** ($30 one-time) — the desktop app calls Anthropic directly with the
  user's own key. This server is only ever hit once (or occasionally) to verify
  the license they bought.
- **`managed`** (free 1hr/day, or $19/mo for 10hr/day) — the desktop app never
  touches Anthropic directly. It signs in with Google, then every check is
  proxied through `/v1/analyze`, which is Haiku-only and enforces the daily
  cap server-side (never trust the client for either).
- **`dev`** (unrestricted, for testing) doesn't need this server unless you
  flip on "managed proxy (dev testing)" in Settings.

This is a from-scratch MVP — no hosting, database, Stripe account, or Google
Cloud project existed before this. **Nothing here is deployed.**

## Stack

- **FastAPI** — the API
- **SQLite** (stdlib `sqlite3`, one file, one `subscribers` table) — swap for
  Postgres if this ever needs more than one server process (SQLite doesn't
  handle concurrent writers across processes well)
- **Stripe** — billing (one-time $30 Price + recurring $19/mo Price)
- **Google OAuth** — "Sign in with Google" for the managed edition, via a
  desktop-app loopback flow (RFC 8252)

## 1. Set up Stripe — two separate Prices

1. Create a Stripe account (or use an existing one) at stripe.com.
2. Create a **Product** "Onitry BYOK" with a **one-time** Price of $30.
   Copy the Price ID → `STRIPE_BYOK_PRICE_ID`.
3. Create a second **Product** "Onitry Pro" with a **recurring** Price of
   $19/month. Copy the Price ID → `STRIPE_MANAGED_PRICE_ID`.
4. Get your **Secret key** from the dashboard (start with the test key).
5. The **webhook** gets registered in step 4 below, once you know the server's URL.

## 2. Set up Google OAuth (for the managed edition's sign-in)

1. Go to [Google Cloud Console](https://console.cloud.google.com/) → create/select a project.
2. **APIs & Services → OAuth consent screen** — External, testing mode is fine to start.
   Scopes needed: `openid`, `email` (both default/non-sensitive).
3. **APIs & Services → Credentials → Create Credentials → OAuth client ID**
   → Application type: **Desktop app**.
4. Copy the **Client ID** → `GOOGLE_CLIENT_ID`, and the **Client Secret** →
   `GOOGLE_CLIENT_SECRET`. Desktop clients are "public clients" per Google's
   own docs (the secret isn't treated as confidential the way a web server's
   is), but a real value is still required for the token exchange.
5. No redirect URI needs registering — the desktop app uses a loopback
   address (`http://localhost:<random-port>`), which Google always allows for
   this client type without pre-registration.

## 3. Configure environment

```
cp server/.env.example server/.env
```

Fill in `ANTHROPIC_API_KEY`, `STRIPE_SECRET_KEY`, `STRIPE_BYOK_PRICE_ID`,
`STRIPE_MANAGED_PRICE_ID`, `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`. Leave
`STRIPE_WEBHOOK_SECRET` for step 5. This app reads env vars directly (no
`python-dotenv` dependency) — export them before running:

```
export $(grep -v '^#' server/.env | xargs)
```

The desktop app needs `GOOGLE_CLIENT_ID`/`GOOGLE_CLIENT_SECRET` too (same
values) — set them wherever you launch the `managed`-edition build.

## 4. Run locally

```
pip install -r server/requirements.txt
uvicorn server.app:app --reload
```

Visit `http://localhost:8000/health` — should return `{"status": "ok"}`.

## 5. Wire up the Stripe webhook

For local testing, use the [Stripe CLI](https://stripe.com/docs/stripe-cli):

```
stripe listen --forward-to localhost:8000/webhooks/stripe
```

This prints a webhook signing secret (`whsec_...`) — put that in
`STRIPE_WEBHOOK_SECRET`. In production, register the webhook endpoint
(`https://your-domain/webhooks/stripe`) in the Stripe dashboard instead, for:
`checkout.session.completed`, `customer.subscription.updated`,
`customer.subscription.deleted`.

## 6. Test the flows end-to-end

**BYOK purchase** (one-time payment):
```
stripe trigger checkout.session.completed --add checkout_session:mode=payment
```
Check the logs for `[stripe] new BYOK license issued: ...`, then:
```
python -m server.admin lookup <token>
curl -X POST localhost:8000/v1/license/verify -d '{"token":"<token>"}' -H 'content-type: application/json'
```

**Managed sign-up + upgrade**: sign in with Google from the desktop app (or
call `POST /v1/auth/google` directly with a real ID token) to create a
`managed_free` account, then use `/v1/checkout/upgrade` with that account's
token as `subscriber_token` to test the upgrade path.

## What's NOT done yet

- **Email delivery.** BYOK licenses are logged server-side (see the `TODO` in
  `app.py`) but not emailed to the buyer. Wire up SMTP/SendGrid/Postmark in
  the webhook handler before this goes live. Until then, use
  `python -m server.admin lookup/issue` for support requests.
- **Deployment.** Not deployed anywhere. Runs anywhere Python does — Fly.io,
  Railway, Render, a plain VPS all work fine for a single-file SQLite app
  like this. Pick one when ready; `/health` is there for whatever platform's
  health check needs it.
- ~~Rate limiting / abuse protection.~~ **Done** — `/v1/analyze` now enforces a
  per-token minimum interval (`MIN_ANALYZE_INTERVAL_SECONDS`, currently 3s)
  using a server-observed timestamp (`db.check_rate_limit`), independent of
  the daily-cap's client-reported `elapsed_seconds`. This specifically closes
  the gap where a client could under-report `elapsed_seconds` to dodge the
  daily cap while still hammering the endpoint for real, billable Anthropic
  calls — see `db.check_rate_limit`'s docstring. Still single-process/SQLite
  scoped like the rest of this module; revisit alongside the Postgres move if
  this ever runs as multiple worker processes.
- **Google OAuth consent screen verification.** Testing-mode consent screens
  cap at 100 test users and show an "unverified app" warning. Submit for
  Google's verification before a real public launch.
- **Checkout wiring on the website.** The marketing site's "Get Full Focus"
  button still just shows an `alert()` — wire it to call
  `/v1/checkout/byok` (no account needed) and redirect.
- **Timezone.** Daily usage resets on the UTC calendar date, not the
  subscriber's local time — simplest to reason about, but means the reset
  moment isn't midnight for most users.

## API

- `GET /health` — liveness check
- `GET /v1/whoami?token=...` — managed accounts only → `{email, plan, active, daily_cap_seconds, daily_remaining_seconds}`
- `POST /v1/auth/google` — `{id_token}` → verifies with Google, creates/logs in a `managed_free` account → `{token, plan, email, daily_cap_seconds}`
- `POST /v1/license/verify` — `{token}` → `{valid}` (BYOK only)
- `POST /v1/analyze` — managed accounts only. `{token, task, screenshot_b64, context, notes, elapsed_seconds}` → same JSON shape as `ai/client.py`'s `analyze()`, plus `cost` and `daily_remaining_seconds`. Model is always Haiku — never accepted from the client.
- `POST /v1/checkout/byok` — `{success_url, cancel_url}` → `{url}` (one-time $30 Stripe Checkout, no account needed first)
- `POST /v1/checkout/upgrade` — `{success_url, cancel_url, subscriber_token}` → `{url}` ($19/mo Checkout that upgrades the given account on completion)
- `POST /webhooks/stripe` — Stripe webhook receiver (branches on `mode`: `"payment"` → new BYOK license, `"subscription"` → upgrade the account named by `client_reference_id`)

## Admin CLI

```
python -m server.admin lookup <token>
python -m server.admin issue <email> [--plan byok|managed_free|managed_paid] [--inactive]
python -m server.admin activate <token>
python -m server.admin deactivate <token>
```
