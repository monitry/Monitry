import unittest
from unittest.mock import MagicMock, patch

import httpx

import config
from ai import client


class _DirectPathCalled(Exception):
    """Sentinel raised by the mocked direct-call path to prove it (not httpx) ran."""


class TestManagedMode(unittest.TestCase):
    """LEGACY managed proxy (not offered). Only reachable with the legacy flag on."""

    def setUp(self):
        self._orig_legacy = config.LEGACY_EDITIONS_ENABLED
        config.LEGACY_EDITIONS_ENABLED = True
        self._orig_managed_mode = config.MANAGED_MODE
        self._orig_managed_token = config.MANAGED_TOKEN
        self._orig_managed_url = config.MANAGED_API_URL
        client.reset_session()

    def tearDown(self):
        config.LEGACY_EDITIONS_ENABLED = self._orig_legacy
        config.MANAGED_MODE = self._orig_managed_mode
        config.MANAGED_TOKEN = self._orig_managed_token
        config.MANAGED_API_URL = self._orig_managed_url
        client.reset_session()

    @patch("ai.client.httpx.post")
    @patch("ai.client._create_with_retry")
    def test_direct_mode_used_when_managed_disabled(self, mock_direct, mock_post):
        config.MANAGED_MODE = False
        config.MANAGED_TOKEN = "onitry_sometoken"

        mock_direct.side_effect = _DirectPathCalled()
        mock_post.side_effect = AssertionError("httpx.post should not be called in direct mode")

        with self.assertRaises(_DirectPathCalled):
            client.analyze("task", "b64", "")
        mock_post.assert_not_called()

    @patch("ai.client.httpx.post")
    def test_managed_mode_calls_proxy_and_updates_cost(self, mock_post):
        config.MANAGED_MODE = True
        config.MANAGED_TOKEN = "onitry_sometoken"
        config.MANAGED_API_URL = "https://api.example.test"

        fake_response = MagicMock()
        fake_response.json.return_value = {
            "onTask": True, "activity": "coding", "reminder": "", "notes": "",
            "cost": 0.0042,
        }
        mock_post.return_value = fake_response

        result = client.analyze("task", "b64", "")

        self.assertEqual(result["activity"], "coding")
        self.assertAlmostEqual(client.session_cost(), 0.0042, places=6)

        call_kwargs = mock_post.call_args.kwargs
        self.assertEqual(call_kwargs["json"]["token"], "onitry_sometoken")
        self.assertEqual(mock_post.call_args.args[0], "https://api.example.test/v1/analyze")

    @patch("ai.client.httpx.post")
    def test_managed_mode_not_used_without_token(self, mock_post):
        config.MANAGED_MODE = True
        config.MANAGED_TOKEN = ""  # no token saved yet

        with patch("ai.client._create_with_retry") as mock_direct:
            mock_direct.side_effect = RuntimeError("direct path reached, as expected")
            with self.assertRaises(RuntimeError):
                client.analyze("task", "b64", "")

        mock_post.assert_not_called()

    @patch("ai.client.httpx.post")
    def test_managed_mode_accumulates_cost_across_calls(self, mock_post):
        config.MANAGED_MODE = True
        config.MANAGED_TOKEN = "onitry_sometoken"

        fake_response = MagicMock()
        fake_response.json.return_value = {
            "onTask": True, "activity": "x", "reminder": "", "notes": "", "cost": 0.01,
        }
        mock_post.return_value = fake_response

        client.analyze("task", "b64", "")
        client.analyze("task", "b64", "")

        self.assertAlmostEqual(client.session_cost(), 0.02, places=6)

    @patch("ai.client.httpx.post")
    def test_managed_mode_reports_elapsed_seconds_never_model(self, mock_post):
        config.MANAGED_MODE = True
        config.MANAGED_TOKEN = "onitry_sometoken"

        fake_response = MagicMock()
        fake_response.json.return_value = {"onTask": True, "activity": "x", "reminder": "", "notes": ""}
        mock_post.return_value = fake_response

        client.analyze("task", "b64", "", elapsed_seconds=12.5)

        sent = mock_post.call_args.kwargs["json"]
        self.assertEqual(sent["elapsed_seconds"], 12.5)
        self.assertNotIn("model", sent)  # server always uses Haiku for managed requests

    @patch("ai.client.httpx.post")
    def test_managed_mode_raises_on_daily_limit(self, mock_post):
        config.MANAGED_MODE = True
        config.MANAGED_TOKEN = "onitry_sometoken"

        fake_response = MagicMock()
        fake_response.status_code = 429
        fake_response.json.return_value = {"detail": "Daily limit reached. 0s remaining today."}
        mock_post.return_value = fake_response

        with self.assertRaises(client.DailyLimitReached):
            client.analyze("task", "b64", "")

    @patch("ai.client.httpx.post")
    @patch("ai.client.time.sleep")
    def test_managed_mode_retries_on_connection_error_then_succeeds(self, mock_sleep, mock_post):
        config.MANAGED_MODE = True
        config.MANAGED_TOKEN = "onitry_sometoken"

        fake_response = MagicMock()
        fake_response.status_code = 200
        fake_response.json.return_value = {"onTask": True, "activity": "x", "reminder": "", "notes": ""}
        mock_post.side_effect = [httpx.ConnectError("connection refused"), fake_response]

        result = client.analyze("task", "b64", "")

        self.assertTrue(result["onTask"])
        self.assertEqual(mock_post.call_count, 2)
        mock_sleep.assert_called_once()

    @patch("ai.client.httpx.post")
    @patch("ai.client.time.sleep")
    def test_managed_mode_raises_after_exhausting_retries(self, mock_sleep, mock_post):
        config.MANAGED_MODE = True
        config.MANAGED_TOKEN = "onitry_sometoken"
        mock_post.side_effect = httpx.ConnectTimeout("timed out")

        with self.assertRaises(httpx.ConnectTimeout):
            client.analyze("task", "b64", "")
        self.assertEqual(mock_post.call_count, 3)  # initial + 2 retries

    @patch("ai.client.httpx.post")
    def test_managed_mode_daily_limit_is_not_retried(self, mock_post):
        # A 429 from our own server (daily cap) is a definitive answer, not a
        # transient failure — retrying it in a loop would be pointless and,
        # combined with the server's own rate limiter, would just get 429'd
        # again immediately. httpx.post returning a 429 response (not raising)
        # never even reaches the retry wrapper's except clause.
        config.MANAGED_MODE = True
        config.MANAGED_TOKEN = "onitry_sometoken"

        fake_response = MagicMock()
        fake_response.status_code = 429
        fake_response.json.return_value = {"detail": "Daily limit reached."}
        mock_post.return_value = fake_response

        with self.assertRaises(client.DailyLimitReached):
            client.analyze("task", "b64", "")
        self.assertEqual(mock_post.call_count, 1)

    @patch("ai.client.httpx.post")
    def test_managed_mode_updates_remaining_seconds_in_config(self, mock_post):
        config.MANAGED_MODE = True
        config.MANAGED_TOKEN = "onitry_sometoken"

        fake_response = MagicMock()
        fake_response.status_code = 200
        fake_response.json.return_value = {
            "onTask": True, "activity": "x", "reminder": "", "notes": "",
            "daily_remaining_seconds": 42.0,
        }
        mock_post.return_value = fake_response

        client.analyze("task", "b64", "")
        self.assertEqual(config.MANAGED_DAILY_REMAINING_SECONDS, 42.0)


class TestManagedProxyUnreachableByDefault(unittest.TestCase):
    """With the legacy flag off (the default), analyze() never talks to an Onitry server,
    even if stale managed state is present."""

    def setUp(self):
        self._orig = (config.LEGACY_EDITIONS_ENABLED, config.MANAGED_MODE, config.MANAGED_TOKEN)
        client.reset_session()

    def tearDown(self):
        config.LEGACY_EDITIONS_ENABLED, config.MANAGED_MODE, config.MANAGED_TOKEN = self._orig
        client.reset_session()

    @patch("ai.client.httpx.post")
    @patch("ai.client._create_with_retry")
    def test_stale_managed_state_still_goes_direct(self, mock_direct, mock_post):
        config.LEGACY_EDITIONS_ENABLED = False
        config.MANAGED_MODE = True
        config.MANAGED_TOKEN = "onitry_sometoken"
        mock_direct.side_effect = _DirectPathCalled()
        mock_post.side_effect = AssertionError("must not call any Onitry server")

        with self.assertRaises(_DirectPathCalled):
            client.analyze("task", "b64", "")
        mock_post.assert_not_called()


if __name__ == "__main__":
    unittest.main()
