import json
import unittest
from types import SimpleNamespace
from unittest.mock import patch

import config
from room import analyzer


def _fake_message(input_tokens, output_tokens, payload):
    return SimpleNamespace(
        content=[SimpleNamespace(text=json.dumps(payload))],
        usage=SimpleNamespace(input_tokens=input_tokens, output_tokens=output_tokens),
    )


class TestRoomAnalyzer(unittest.TestCase):
    def setUp(self):
        self._orig_model = config.HAIKU_MODEL
        analyzer.reset_session()

    def tearDown(self):
        config.HAIKU_MODEL = self._orig_model
        analyzer.reset_session()

    def test_reset_session_zeroes_cost_and_notes(self):
        analyzer._notes["screen-1"] = "leftover"
        analyzer._session_cost = 5.0
        analyzer.reset_session()
        self.assertEqual(analyzer.session_cost(), 0.0)
        self.assertEqual(analyzer._notes, {})

    @patch("room.analyzer._create_with_retry")
    def test_analyze_screen_returns_parsed_result_and_tracks_cost(self, mock_create):
        payload = {"activity": "reading a PDF", "onTask": True, "notes": "steady"}
        mock_create.return_value = _fake_message(1_000_000, 1_000_000, payload)

        result = analyzer.analyze_screen("screen-1", "fakeb64", context="", task="reading")

        self.assertEqual(result["activity"], "reading a PDF")
        self.assertTrue(result["onTask"])
        # 1M input @ $1.00/M + 1M output @ $5.00/M = $6.00
        self.assertAlmostEqual(analyzer.session_cost(), 6.00, places=6)

    @patch("room.analyzer._create_with_retry")
    def test_notes_persist_per_screen_independently(self, mock_create):
        mock_create.return_value = _fake_message(
            0, 0, {"activity": "x", "onTask": None, "notes": "screen-1 notes"}
        )
        analyzer.analyze_screen("screen-1", "b64", context="", task="")

        mock_create.return_value = _fake_message(
            0, 0, {"activity": "y", "onTask": None, "notes": "screen-2 notes"}
        )
        analyzer.analyze_screen("screen-2", "b64", context="", task="")

        self.assertEqual(analyzer._notes["screen-1"], "screen-1 notes")
        self.assertEqual(analyzer._notes["screen-2"], "screen-2 notes")

    @patch("room.analyzer._create_with_retry")
    def test_forget_screen_removes_only_that_screens_notes(self, mock_create):
        mock_create.return_value = _fake_message(0, 0, {"activity": "x", "onTask": None, "notes": "n1"})
        analyzer.analyze_screen("screen-1", "b64", context="", task="")
        mock_create.return_value = _fake_message(0, 0, {"activity": "y", "onTask": None, "notes": "n2"})
        analyzer.analyze_screen("screen-2", "b64", context="", task="")

        analyzer.forget_screen("screen-1")

        self.assertNotIn("screen-1", analyzer._notes)
        self.assertIn("screen-2", analyzer._notes)

    @patch("room.analyzer._create_with_retry")
    def test_empty_task_reflected_in_prompt(self, mock_create):
        mock_create.return_value = _fake_message(0, 0, {"activity": "x", "onTask": None, "notes": ""})
        analyzer.analyze_screen("screen-1", "b64", context="", task="")

        sent_text = mock_create.call_args.kwargs["messages"][0]["content"][1]["text"]
        self.assertIn("none specified", sent_text)

    @patch("room.analyzer._create_with_retry")
    def test_given_task_is_included_in_prompt(self, mock_create):
        mock_create.return_value = _fake_message(0, 0, {"activity": "x", "onTask": True, "notes": ""})
        analyzer.analyze_screen("screen-1", "b64", context="", task="finish the essay")

        sent_text = mock_create.call_args.kwargs["messages"][0]["content"][1]["text"]
        self.assertIn("finish the essay", sent_text)

    @patch("room.analyzer._create_with_retry")
    def test_json_fenced_response_with_embedded_backticks_survives(self, mock_create):
        # Regression test, mirrors ai/client.py's equivalent fix: a naive
        # `.split("```")[1]` truncates if the JSON payload itself contains a
        # ``` sequence (e.g. describing a code block visible on the screen).
        raw_text = (
            '```json\n'
            '{"activity": "viewing a README with a ```bash snippet```", '
            '"onTask": true, "notes": ""}\n'
            '```'
        )
        mock_create.return_value = SimpleNamespace(
            content=[SimpleNamespace(text=raw_text)],
            usage=SimpleNamespace(input_tokens=0, output_tokens=0),
        )
        result = analyzer.analyze_screen("screen-1", "b64", context="", task="")
        self.assertIn("```bash snippet```", result["activity"])

    @patch("room.analyzer._create_with_retry")
    def test_cost_accumulates_across_multiple_screens(self, mock_create):
        mock_create.return_value = _fake_message(500_000, 100_000, {"activity": "x", "onTask": None, "notes": ""})
        analyzer.analyze_screen("screen-1", "b64", context="", task="")
        analyzer.analyze_screen("screen-2", "b64", context="", task="")

        # Each call: 0.5M*$1 + 0.1M*$5 = $0.50 + $0.50 = $1.00; twice = $2.00
        self.assertAlmostEqual(analyzer.session_cost(), 2.00, places=6)


if __name__ == "__main__":
    unittest.main()
