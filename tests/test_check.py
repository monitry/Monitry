import unittest
from unittest.mock import patch

from core import check


class TestRunCheck(unittest.TestCase):
    @patch("core.check.ai_client.analyze")
    @patch("core.check.screen.grab_screenshot")
    def test_captures_screenshot_and_forwards_to_analyze(self, mock_grab, mock_analyze):
        mock_grab.return_value = "fakebase64"
        mock_analyze.return_value = {"onTask": True}

        result = check.run_check("write code", "recent activity", max_width=800, quality=60, elapsed_seconds=12.5)

        mock_grab.assert_called_once_with(800, 60)
        mock_analyze.assert_called_once_with("write code", "fakebase64", "recent activity", 12.5)
        self.assertEqual(result, {"onTask": True})

    @patch("core.check.ai_client.analyze")
    @patch("core.check.screen.grab_screenshot")
    def test_defaults_match_documented_values(self, mock_grab, mock_analyze):
        mock_grab.return_value = "b64"
        mock_analyze.return_value = {}

        check.run_check("task", "context")

        mock_grab.assert_called_once_with(1280, 75)


class TestSessionHelpers(unittest.TestCase):
    @patch("core.check.ai_client.reset_session")
    def test_reset_session_delegates(self, mock_reset):
        check.reset_session()
        mock_reset.assert_called_once_with()

    @patch("core.check.ai_client.session_cost")
    def test_session_cost_delegates(self, mock_cost):
        mock_cost.return_value = 3.14
        self.assertEqual(check.session_cost(), 3.14)


if __name__ == "__main__":
    unittest.main()
