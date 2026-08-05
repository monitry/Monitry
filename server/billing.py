"""Stripe integration — checkout session creation and webhook verification.

Requires a Stripe account. Set these env vars before running:
  STRIPE_SECRET_KEY    — from the Stripe dashboard (test or live)
  STRIPE_PRICE_ID      — the recurring Price object for the $19/mo plan
  STRIPE_WEBHOOK_SECRET — from the webhook endpoint's settings, after you register it
"""
import os

import stripe

stripe.api_key = os.environ.get("STRIPE_SECRET_KEY", "")
PRICE_ID = os.environ.get("STRIPE_PRICE_ID", "")
WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "")


def create_checkout_session(success_url: str, cancel_url: str) -> str:
    session = stripe.checkout.Session.create(
        mode="subscription",
        line_items=[{"price": PRICE_ID, "quantity": 1}],
        success_url=success_url,
        cancel_url=cancel_url,
    )
    return session.url


def verify_webhook(payload: bytes, sig_header: str) -> stripe.Event:
    return stripe.Webhook.construct_event(payload, sig_header, WEBHOOK_SECRET)
