"""Stripe integration — checkout session creation and webhook verification.

Two separate Stripe Price objects, two separate products:
  - STRIPE_BYOK_PRICE_ID    — one-time ($30) Price, for the bring-your-own-key app
  - STRIPE_MANAGED_PRICE_ID — recurring ($19/mo) Price, for upgrading a managed_free
                              account to managed_paid

Set these env vars before running:
  STRIPE_SECRET_KEY      — from the Stripe dashboard (test or live)
  STRIPE_BYOK_PRICE_ID    — the one-time Price for the $30 BYOK app
  STRIPE_MANAGED_PRICE_ID — the recurring Price for the $19/mo managed plan
  STRIPE_WEBHOOK_SECRET   — from the webhook endpoint's settings, after you register it
"""
import os

import stripe

stripe.api_key = os.environ.get("STRIPE_SECRET_KEY", "")
BYOK_PRICE_ID = os.environ.get("STRIPE_BYOK_PRICE_ID", "")
MANAGED_PRICE_ID = os.environ.get("STRIPE_MANAGED_PRICE_ID", "")
WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "")


def create_byok_checkout_session(success_url: str, cancel_url: str) -> str:
    """One-time $30 purchase — no existing account needed, the webhook mints a fresh license."""
    session = stripe.checkout.Session.create(
        mode="payment",
        line_items=[{"price": BYOK_PRICE_ID, "quantity": 1}],
        success_url=success_url,
        cancel_url=cancel_url,
    )
    return session.url


def create_managed_upgrade_session(success_url: str, cancel_url: str, subscriber_token: str) -> str:
    """Subscription checkout for an *existing* managed_free account (Google sign-in already
    happened) — `client_reference_id` lets the webhook find the right row to upgrade instead
    of blindly minting a new one."""
    session = stripe.checkout.Session.create(
        mode="subscription",
        line_items=[{"price": MANAGED_PRICE_ID, "quantity": 1}],
        success_url=success_url,
        cancel_url=cancel_url,
        client_reference_id=subscriber_token,
    )
    return session.url


def verify_webhook(payload: bytes, sig_header: str) -> stripe.Event:
    return stripe.Webhook.construct_event(payload, sig_header, WEBHOOK_SECRET)
