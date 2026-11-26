import json
import os
import shutil
import tempfile
import time
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from fastapi.testclient import TestClient

from server import app as server_app
from server import db


def _fake_message(input_tokens, output_tokens, payload):
    return SimpleNamespace(
        content=[SimpleNamespace(text=json.dumps(payload))],
        usage=SimpleNamespace(input_tokens=input_tokens, output_tokens=output_tokens),
    )


class TestServerApp(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self._orig_path = db.DB_PATH
        db.DB_PATH = os.path.join(self.tmpdir, "test.db")
        db.init_db()
        self.client = TestClient(server_app.app)

    def tearDown(self):
        db.DB_PATH = self._orig_path
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_health(self):
        resp = self.client.get("/health")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), {"status": "ok"})

    # ── whoami ────────────────────────────────────────────────────────────

    def test_whoami_unknown_token(self):
        resp = self.client.get("/v1/whoami", params={"token": "nope"})
        self.assertEqual(resp.status_code, 401)

    def test_whoami_byok_token_rejected(self):
        # BYOK tokens aren't managed-plan accounts — whoami is a managed-only endpoint.
        token = db.create_byok_license("a@b.com", None)
        resp = self.client.get("/v1/whoami", params={"token": token})
        self.assertEqual(resp.status_code, 403)

    def test_whoami_free_account(self):
        subscriber = db.get_or_create_by_google("sub-a", "a@b.com")
        resp = self.client.get("/v1/whoami", params={"token": subscriber["token"]})
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertEqual(body["plan"], db.PLAN_FREE)
        self.assertEqual(body["daily_cap_seconds"], 3600)
        self.assertEqual(body["daily_remaining_seconds"], 3600)

    # ── Google auth ───────────────────────────────────────────────────────

    @patch("server.app.google_auth.verify")
    def test_auth_google_creates_free_account(self, mock_verify):
        mock_verify.return_value = {"sub": "google-sub-1", "email": "a@b.com"}
        resp = self.client.post("/v1/auth/google", json={"id_token": "fake"})
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertEqual(body["plan"], db.PLAN_FREE)
        self.assertEqual(body["email"], "a@b.com")
        self.assertIn("token", body)

    @patch("server.app.google_auth.verify")
    def test_auth_google_invalid_token_rejected(self, mock_verify):
        from server.google_auth import InvalidGoogleToken
        mock_verify.side_effect = InvalidGoogleToken("bad token")
        resp = self.client.post("/v1/auth/google", json={"id_token": "fake"})
        self.assertEqual(resp.status_code, 401)

    @patch("server.app.google_auth.verify")
    def test_auth_google_same_user_returns_same_token(self, mock_verify):
        mock_verify.return_value = {"sub": "google-sub-1", "email": "a@b.com"}
        first = self.client.post("/v1/auth/google", json={"id_token": "fake"}).json()
        second = self.client.post("/v1/auth/google", json={"id_token": "fake"}).json()
        self.assertEqual(first["token"], second["token"])

    # ── BYOK license verification ─────────────────────────────────────────

    def test_license_verify_valid(self):
        token = db.create_byok_license("a@b.com", None)
        resp = self.client.post("/v1/license/verify", json={"token": token})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), {"valid": True})

    def test_license_verify_unknown_token(self):
        resp = self.client.post("/v1/license/verify", json={"token": "nope"})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), {"valid": False})

    def test_license_verify_rejects_managed_token(self):
        subscriber = db.get_or_create_by_google("sub-a", "a@b.com")
        resp = self.client.post("/v1/license/verify", json={"token": subscriber["token"]})
        self.assertEqual(resp.json(), {"valid": False})

    # ── /v1/analyze ───────────────────────────────────────────────────────

    def test_analyze_rejects_unknown_token(self):
        resp = self.client.post("/v1/analyze", json={
            "token": "nope", "task": "work", "screenshot_b64": "abc",
        })
        self.assertEqual(resp.status_code, 401)

    def test_analyze_rejects_byok_token(self):
        # BYOK never calls /v1/analyze — it runs direct-to-Anthropic client-side.
        token = db.create_byok_license("a@b.com", None)
        resp = self.client.post("/v1/analyze", json={
            "token": token, "task": "work", "screenshot_b64": "abc",
        })
        self.assertEqual(resp.status_code, 403)

    def test_analyze_rejects_inactive_subscriber(self):
        subscriber = db.get_or_create_by_google("sub-a", "a@b.com")
        db.set_active_by_token(subscriber["token"], False)
        resp = self.client.post("/v1/analyze", json={
            "token": subscriber["token"], "task": "work", "screenshot_b64": "abc",
        })
        self.assertEqual(resp.status_code, 402)

    @patch("server.app._get_client")
    def test_analyze_returns_parsed_result_and_records_usage(self, mock_get_client):
        subscriber = db.get_or_create_by_google("sub-a", "a@b.com")
        payload = {"onTask": True, "interrupt": False, "activity": "coding", "reminder": "", "notes": ""}
        mock_get_client.return_value.messages.create.return_value = _fake_message(
            1_000_000, 1_000_000, payload
        )

        resp = self.client.post("/v1/analyze", json={
            "token": subscriber["token"], "task": "write code", "screenshot_b64": "abc",
            "elapsed_seconds": 10,
        })

        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertEqual(body["activity"], "coding")
        self.assertAlmostEqual(body["cost"], 6.00, places=6)  # 1M in @$1 + 1M out @$5
        self.assertAlmostEqual(body["daily_remaining_seconds"], 3590, places=3)

        called_model = mock_get_client.return_value.messages.create.call_args.kwargs["model"]
        self.assertEqual(called_model, server_app.MANAGED_MODEL)

    @patch("server.app._get_client")
    def test_analyze_ignores_client_supplied_model(self, mock_get_client):
        # There's no `model` field on AnalyzeRequest anymore, but even a raw extra key must not
        # change what's actually sent to Anthropic — managed edition is Haiku-only, server-enforced.
        subscriber = db.get_or_create_by_google("sub-a", "a@b.com")
        payload = {"onTask": True, "activity": "x", "reminder": "", "notes": ""}
        mock_get_client.return_value.messages.create.return_value = _fake_message(0, 0, payload)

        resp = self.client.post("/v1/analyze", json={
            "token": subscriber["token"], "task": "work", "screenshot_b64": "abc",
            "model": "claude-opus-4-8",
        })
        self.assertEqual(resp.status_code, 200)
        called_model = mock_get_client.return_value.messages.create.call_args.kwargs["model"]
        self.assertEqual(called_model, server_app.MANAGED_MODEL)

    @patch("server.app._get_client")
    def test_analyze_rejects_once_daily_cap_exhausted(self, mock_get_client):
        subscriber = db.get_or_create_by_google("sub-a", "a@b.com")
        payload = {"onTask": True, "activity": "x", "reminder": "", "notes": ""}
        mock_get_client.return_value.messages.create.return_value = _fake_message(0, 0, payload)

        resp = self.client.post("/v1/analyze", json={
            "token": subscriber["token"], "task": "work", "screenshot_b64": "abc",
            "elapsed_seconds": 3600,  # the entire free-tier daily cap in one go
        })
        self.assertEqual(resp.status_code, 200)

        # Back-date last_request_at so this second call clears the (separate)
        # per-token rate limiter and actually exercises the daily-cap rejection
        # path being tested here, rather than incidentally tripping the rate
        # limiter instead — see test_analyze_rate_limited_on_rapid_repeat_calls
        # for that path specifically.
        with db._connect() as conn:
            conn.execute(
                "UPDATE subscribers SET last_request_at = ? WHERE token = ?",
                (time.time() - server_app.MIN_ANALYZE_INTERVAL_SECONDS - 1, subscriber["token"]),
            )

        resp2 = self.client.post("/v1/analyze", json={
            "token": subscriber["token"], "task": "work", "screenshot_b64": "abc",
            "elapsed_seconds": 1,
        })
        self.assertEqual(resp2.status_code, 429)
        self.assertIn("Daily limit", resp2.json()["detail"])
        # Anthropic must not have been called for the rejected request.
        self.assertEqual(mock_get_client.return_value.messages.create.call_count, 1)

    @patch("server.app._get_client")
    def test_analyze_rate_limited_on_rapid_repeat_calls(self, mock_get_client):
        subscriber = db.get_or_create_by_google("sub-a", "a@b.com")
        payload = {"onTask": True, "activity": "x", "reminder": "", "notes": ""}
        mock_get_client.return_value.messages.create.return_value = _fake_message(0, 0, payload)

        resp = self.client.post("/v1/analyze", json={
            "token": subscriber["token"], "task": "work", "screenshot_b64": "abc",
            "elapsed_seconds": 0,
        })
        self.assertEqual(resp.status_code, 200)

        # Immediate repeat, well within MIN_ANALYZE_INTERVAL_SECONDS and still
        # claiming elapsed_seconds=0 — this is exactly the tight-loop-while-
        # under-reporting-usage abuse pattern the rate limiter exists to catch,
        # since the daily cap alone can't see it (see db.check_rate_limit).
        resp2 = self.client.post("/v1/analyze", json={
            "token": subscriber["token"], "task": "work", "screenshot_b64": "abc",
            "elapsed_seconds": 0,
        })
        self.assertEqual(resp2.status_code, 429)
        self.assertIn("Too many requests", resp2.json()["detail"])
        self.assertEqual(mock_get_client.return_value.messages.create.call_count, 1)

    @patch("server.app._get_client")
    def test_paid_plan_gets_larger_cap(self, mock_get_client):
        subscriber = db.get_or_create_by_google("sub-a", "a@b.com")
        db.upgrade_to_paid(subscriber["token"], "cus_1", "sub_1")
        payload = {"onTask": True, "activity": "x", "reminder": "", "notes": ""}
        mock_get_client.return_value.messages.create.return_value = _fake_message(0, 0, payload)

        resp = self.client.post("/v1/analyze", json={
            "token": subscriber["token"], "task": "work", "screenshot_b64": "abc",
            "elapsed_seconds": 3600,  # would exhaust a free-tier cap but not a paid one
        })
        self.assertEqual(resp.status_code, 200)
        self.assertAlmostEqual(resp.json()["daily_remaining_seconds"], 36000 - 3600, places=3)

    # ── Checkout ──────────────────────────────────────────────────────────

    @patch("server.app.billing.create_byok_checkout_session")
    def test_checkout_byok(self, mock_create):
        mock_create.return_value = "https://checkout.stripe.com/session/abc"
        resp = self.client.post("/v1/checkout/byok", json={
            "success_url": "https://onitry.app/ok", "cancel_url": "https://onitry.app/cancel",
        })
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["url"], "https://checkout.stripe.com/session/abc")

    @patch("server.app.billing.create_managed_upgrade_session")
    def test_checkout_upgrade_requires_subscriber_token(self, mock_create):
        resp = self.client.post("/v1/checkout/upgrade", json={
            "success_url": "https://onitry.app/ok", "cancel_url": "https://onitry.app/cancel",
        })
        self.assertEqual(resp.status_code, 400)
        mock_create.assert_not_called()

    @patch("server.app.billing.create_managed_upgrade_session")
    def test_checkout_upgrade_passes_subscriber_token(self, mock_create):
        mock_create.return_value = "https://checkout.stripe.com/session/xyz"
        resp = self.client.post("/v1/checkout/upgrade", json={
            "success_url": "https://onitry.app/ok", "cancel_url": "https://onitry.app/cancel",
            "subscriber_token": "onitry_abc",
        })
        self.assertEqual(resp.status_code, 200)
        mock_create.assert_called_once_with(
            "https://onitry.app/ok", "https://onitry.app/cancel", "onitry_abc"
        )

    # ── Stripe webhook ────────────────────────────────────────────────────

    @patch("server.app.billing.verify_webhook")
    def test_webhook_byok_payment_issues_license(self, mock_verify):
        mock_verify.return_value = {
            "type": "checkout.session.completed",
            "data": {"object": {
                "mode": "payment",
                "customer": "cus_1",
                "customer_details": {"email": "buyer@b.com"},
            }},
        }
        resp = self.client.post(
            "/webhooks/stripe", content=b"{}", headers={"stripe-signature": "sig"}
        )
        self.assertEqual(resp.status_code, 200)

    @patch("server.app.billing.verify_webhook")
    def test_webhook_subscription_upgrades_existing_account(self, mock_verify):
        subscriber = db.get_or_create_by_google("sub-a", "a@b.com")
        mock_verify.return_value = {
            "type": "checkout.session.completed",
            "data": {"object": {
                "mode": "subscription",
                "customer": "cus_1",
                "subscription": "sub_1",
                "client_reference_id": subscriber["token"],
            }},
        }
        resp = self.client.post(
            "/webhooks/stripe", content=b"{}", headers={"stripe-signature": "sig"}
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(db.get_subscriber(subscriber["token"])["plan"], db.PLAN_PAID)

    @patch("server.app.billing.verify_webhook")
    def test_webhook_subscription_deleted_downgrades(self, mock_verify):
        subscriber = db.get_or_create_by_google("sub-a", "a@b.com")
        db.upgrade_to_paid(subscriber["token"], "cus_1", "sub_1")

        mock_verify.return_value = {
            "type": "customer.subscription.deleted",
            "data": {"object": {"id": "sub_1"}},
        }
        resp = self.client.post(
            "/webhooks/stripe", content=b"{}", headers={"stripe-signature": "sig"}
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(db.get_subscriber(subscriber["token"])["plan"], db.PLAN_FREE)

    @patch("server.app.billing.verify_webhook")
    def test_webhook_bad_signature_rejected(self, mock_verify):
        mock_verify.side_effect = ValueError("bad signature")
        resp = self.client.post(
            "/webhooks/stripe", content=b"{}", headers={"stripe-signature": "bad"}
        )
        self.assertEqual(resp.status_code, 400)


if __name__ == "__main__":
    unittest.main()
