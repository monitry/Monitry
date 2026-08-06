import unittest
from unittest.mock import MagicMock, patch

import httpx

from core import license as license_check


class TestLicense(unittest.TestCase):
    def test_empty_token_is_never_valid(self):
        self.assertFalse(license_check.verify("https://api.example.test", ""))

    @patch("core.license.httpx.post")
    def test_valid_token(self, mock_post):
        mock_post.return_value = MagicMock(json=lambda: {"valid": True})
        self.assertTrue(license_check.verify("https://api.example.test", "onitry_abc"))

    @patch("core.license.httpx.post")
    def test_invalid_token(self, mock_post):
        mock_post.return_value = MagicMock(json=lambda: {"valid": False})
        self.assertFalse(license_check.verify("https://api.example.test", "onitry_abc"))

    @patch("core.license.httpx.post")
    def test_network_failure_raises_distinct_error(self, mock_post):
        mock_post.side_effect = httpx.ConnectError("connection refused")
        with self.assertRaises(license_check.LicenseCheckFailed):
            license_check.verify("https://api.example.test", "onitry_abc")

    @patch("core.license.httpx.post")
    def test_sends_token_to_correct_endpoint(self, mock_post):
        mock_post.return_value = MagicMock(json=lambda: {"valid": True})
        license_check.verify("https://api.example.test", "onitry_abc")
        mock_post.assert_called_once()
        self.assertEqual(mock_post.call_args.args[0], "https://api.example.test/v1/license/verify")
        self.assertEqual(mock_post.call_args.kwargs["json"], {"token": "onitry_abc"})


if __name__ == "__main__":
    unittest.main()
