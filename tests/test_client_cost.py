import json
import unittest
from types import SimpleNamespace
from unittest.mock import patch

import config
from ai import client


def _fake_message(input_tokens, output_tokens, payload):
    return SimpleNamespace(
        content=[SimpleNamespace(text=json.dumps(payload))],
        usage=SimpleNamespace(input_tokens=input_tokens, output_tokens=output_tokens),
    )


class TestSessionCost(unittest.TestCase):
    def setUp(self):
        self._orig_model = config.MODEL
        config.MODEL = "claude-haiku-4-5-20251001"  # $1.00 in / $5.00 out per 1M tokens
        client.reset_session()

    def tearDown(self):
        config.MODEL = self._orig_model
        client.reset_session()

    def test_reset_session_zeroes_cost(self):
        self.assertEqual(client.session_cost(), 0.0)

    @patch("ai.client._create_with_retry")
    def test_analyze_accumulates_cost_from_usage(self, mock_create):
        payload = {"onTask": True, "activity": "coding", "reminder": "", "notes": ""}
        mock_create.return_value = _fake_message(1_000_000, 1_000_000, payload)

        client.analyze("write code", "fakebase64", "")

        # 1M input tokens @ $1.00/M + 1M output tokens @ $5.00/M = $6.00
        self.assertAlmostEqual(client.session_cost(), 6.00, places=6)

    @patch("ai.client._create_with_retry")
    def test_cost_accumulates_across_multiple_calls(self, mock_create):
        payload = {"onTask": True, "activity": "coding", "reminder": "", "notes": ""}
        mock_create.return_value = _fake_message(500_000, 100_000, payload)

        client.analyze("task", "b64", "")
        client.analyze("task", "b64", "")

        # Each call: 0.5M * $1.00 + 0.1M * $5.00 = $0.50 + $0.50 = $1.00; twice = $2.00
        self.assertAlmostEqual(client.session_cost(), 2.00, places=6)

    @patch("ai.client._create_with_retry")
    def test_unknown_model_costs_nothing(self, mock_create):
        config.MODEL = "some-future-model-not-in-pricing-table"
        payload = {"onTask": True, "activity": "coding", "reminder": "", "notes": ""}
        mock_create.return_value = _fake_message(1_000_000, 1_000_000, payload)

        client.analyze("task", "b64", "")

        self.assertEqual(client.session_cost(), 0.0)


if __name__ == "__main__":
    unittest.main()
