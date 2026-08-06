import datetime
import os
import shutil
import tempfile
import unittest

from server import db


class TestServerDB(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self._orig_path = db.DB_PATH
        db.DB_PATH = os.path.join(self.tmpdir, "test.db")
        db.init_db()

    def tearDown(self):
        db.DB_PATH = self._orig_path
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_unknown_token_returns_none(self):
        self.assertIsNone(db.get_subscriber("nope"))

    # ── Google sign-in / free-tier signup ──────────────────────────────────

    def test_new_google_user_gets_free_plan(self):
        subscriber = db.get_or_create_by_google("google-sub-1", "a@b.com")
        self.assertEqual(subscriber["plan"], db.PLAN_FREE)
        self.assertEqual(subscriber["email"], "a@b.com")
        self.assertEqual(subscriber["active"], 1)

    def test_same_google_sub_returns_same_account(self):
        first = db.get_or_create_by_google("google-sub-1", "a@b.com")
        second = db.get_or_create_by_google("google-sub-1", "a@b.com")
        self.assertEqual(first["token"], second["token"])

    def test_google_login_updates_changed_email(self):
        first = db.get_or_create_by_google("google-sub-1", "old@b.com")
        second = db.get_or_create_by_google("google-sub-1", "new@b.com")
        self.assertEqual(first["token"], second["token"])
        self.assertEqual(db.get_subscriber(first["token"])["email"], "new@b.com")

    def test_different_google_subs_get_different_accounts(self):
        a = db.get_or_create_by_google("sub-a", "a@b.com")
        b = db.get_or_create_by_google("sub-b", "b@b.com")
        self.assertNotEqual(a["token"], b["token"])

    # ── BYOK licensing ──────────────────────────────────────────────────────

    def test_byok_license_verifies(self):
        token = db.create_byok_license("a@b.com", "cus_1")
        self.assertTrue(db.verify_byok_license(token))

    def test_unknown_token_does_not_verify_as_byok(self):
        self.assertFalse(db.verify_byok_license("nope"))

    def test_managed_token_does_not_verify_as_byok(self):
        subscriber = db.get_or_create_by_google("sub-a", "a@b.com")
        self.assertFalse(db.verify_byok_license(subscriber["token"]))

    def test_deactivated_byok_license_fails_verification(self):
        token = db.create_byok_license("a@b.com", "cus_1")
        db.set_active_by_token(token, False)
        self.assertFalse(db.verify_byok_license(token))

    # ── Plan upgrades/downgrades ─────────────────────────────────────────────

    def test_upgrade_to_paid(self):
        subscriber = db.get_or_create_by_google("sub-a", "a@b.com")
        found = db.upgrade_to_paid(subscriber["token"], "cus_1", "sub_1")
        self.assertTrue(found)
        self.assertEqual(db.get_subscriber(subscriber["token"])["plan"], db.PLAN_PAID)

    def test_upgrade_unknown_token_returns_false(self):
        self.assertFalse(db.upgrade_to_paid("nope", "cus_1", "sub_1"))

    def test_downgrade_to_free_by_subscription(self):
        subscriber = db.get_or_create_by_google("sub-a", "a@b.com")
        db.upgrade_to_paid(subscriber["token"], "cus_1", "sub_1")
        db.downgrade_to_free_by_subscription("sub_1")
        self.assertEqual(db.get_subscriber(subscriber["token"])["plan"], db.PLAN_FREE)

    def test_downgrade_does_not_touch_byok_plans(self):
        # A BYOK row's stripe_subscription_id is always None, so this should never match/affect it.
        byok_token = db.create_byok_license("a@b.com", "cus_1")
        db.downgrade_to_free_by_subscription("sub_1")
        self.assertEqual(db.get_subscriber(byok_token)["plan"], db.PLAN_BYOK)

    # ── Manual admin issuance ────────────────────────────────────────────────

    def test_create_manual_token(self):
        token = db.create_manual("a@b.com", db.PLAN_BYOK, active=True)
        subscriber = db.get_subscriber(token)
        self.assertEqual(subscriber["plan"], db.PLAN_BYOK)
        self.assertEqual(subscriber["active"], 1)

    def test_set_active_by_token(self):
        token = db.create_manual("a@b.com", db.PLAN_FREE, active=True)
        found = db.set_active_by_token(token, False)
        self.assertTrue(found)
        self.assertEqual(db.get_subscriber(token)["active"], 0)

    def test_set_active_by_token_unknown_returns_false(self):
        self.assertFalse(db.set_active_by_token("nonexistent", True))

    # ── Usage accounting ─────────────────────────────────────────────────────

    def test_record_usage_accumulates(self):
        token = db.create_manual("a@b.com", db.PLAN_FREE)
        db.record_usage(token, 1000, 500, 0.01)
        db.record_usage(token, 2000, 1000, 0.02)
        subscriber = db.get_subscriber(token)
        self.assertEqual(subscriber["total_input_tokens"], 3000)
        self.assertEqual(subscriber["total_output_tokens"], 1500)
        self.assertAlmostEqual(subscriber["total_cost"], 0.03, places=6)

    def test_tokens_are_unique(self):
        tokens = {db.create_manual(f"{i}@b.com", db.PLAN_FREE) for i in range(20)}
        self.assertEqual(len(tokens), 20)

    # ── Daily usage cap enforcement ──────────────────────────────────────────

    def test_usage_allowed_within_cap(self):
        token = db.create_manual("a@b.com", db.PLAN_FREE)
        result = db.check_and_consume_daily_usage(token, 100, cap_seconds=3600)
        self.assertTrue(result["allowed"])
        self.assertAlmostEqual(result["remaining"], 3500, places=3)

    def test_usage_consumes_across_multiple_calls(self):
        token = db.create_manual("a@b.com", db.PLAN_FREE)
        db.check_and_consume_daily_usage(token, 1000, cap_seconds=3600)
        result = db.check_and_consume_daily_usage(token, 1000, cap_seconds=3600)
        self.assertTrue(result["allowed"])
        self.assertAlmostEqual(result["remaining"], 1600, places=3)

    def test_usage_rejected_once_cap_exceeded(self):
        token = db.create_manual("a@b.com", db.PLAN_FREE)
        db.check_and_consume_daily_usage(token, 3600, cap_seconds=3600)  # use it all up
        result = db.check_and_consume_daily_usage(token, 1, cap_seconds=3600)
        self.assertFalse(result["allowed"])
        self.assertEqual(result["remaining"], 0.0)

    def test_usage_unknown_token_rejected(self):
        result = db.check_and_consume_daily_usage("nope", 1, cap_seconds=3600)
        self.assertFalse(result["allowed"])

    def test_usage_resets_on_new_day(self):
        token = db.create_manual("a@b.com", db.PLAN_FREE)
        db.check_and_consume_daily_usage(token, 3600, cap_seconds=3600)  # maxed out "today"

        # Simulate yesterday's date already stored, then a fresh check should treat it as a new day.
        yesterday = (datetime.datetime.now(datetime.UTC).date() - datetime.timedelta(days=1)).isoformat()
        with db._connect() as conn:
            conn.execute("UPDATE subscribers SET daily_usage_date = ? WHERE token = ?", (yesterday, token))

        result = db.check_and_consume_daily_usage(token, 100, cap_seconds=3600)
        self.assertTrue(result["allowed"])
        self.assertAlmostEqual(result["remaining"], 3500, places=3)

    def test_remaining_daily_seconds_read_only(self):
        token = db.create_manual("a@b.com", db.PLAN_FREE)
        db.check_and_consume_daily_usage(token, 1000, cap_seconds=3600)
        subscriber = db.get_subscriber(token)
        # Calling this twice must not double-consume anything.
        self.assertAlmostEqual(db.remaining_daily_seconds(subscriber, 3600), 2600, places=3)
        self.assertAlmostEqual(db.remaining_daily_seconds(subscriber, 3600), 2600, places=3)


if __name__ == "__main__":
    unittest.main()
