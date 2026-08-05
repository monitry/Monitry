import unittest
from unittest.mock import MagicMock, patch

import config
from ai import client


class _DirectPathCalled(Exception):
    """Sentinel raised by the mocked direct-call path to prove it (not httpx) ran."""


class TestManagedMode(unittest.TestCase):
    def setUp(self):
        self._orig_managed_mode = config.MANAGED_MODE
        self._orig_managed_token = config.MANAGED_TOKEN
        self._orig_managed_url = config.MANAGED_API_URL
        client.reset_session()

    def tearDown(self):
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


if __name__ == "__main__":
    unittest.main()
