import unittest
from types import SimpleNamespace
from unittest import mock

import config
from ai import review


def _response(text="**Solid week.**", stop_reason="end_turn"):
    return SimpleNamespace(
        stop_reason=stop_reason,
        model="claude-opus-5-5",
        content=[SimpleNamespace(type="thinking", thinking=""), SimpleNamespace(type="text", text=text)],
    )


class TestWeeklyReview(unittest.TestCase):
    def setUp(self):
        self._patches = [
            mock.patch.object(config, "ANTHROPIC_API_KEY", "sk-test"),
            mock.patch.object(config, "MANAGED_MODE", False),
        ]
        for p in self._patches:
            p.start()

    def tearDown(self):
        for p in self._patches:
            p.stop()

    def test_returns_text_blocks_only(self):
        client = mock.Mock()
        client.beta.messages.create.return_value = _response()
        with mock.patch.object(review, "_client", return_value=client):
            out = review.weekly_review({"done": 3})
        self.assertEqual(out["text"], "**Solid week.**")
        kwargs = client.beta.messages.create.call_args.kwargs
        self.assertEqual(kwargs["model"], config.REVIEW_MODEL)
        self.assertEqual(kwargs["fallbacks"], "default")
        self.assertIn('"done": 3', kwargs["messages"][0]["content"])

    def test_refusal_is_unavailable(self):
        client = mock.Mock()
        client.beta.messages.create.return_value = _response(text="", stop_reason="refusal")
        with mock.patch.object(review, "_client", return_value=client):
            with self.assertRaises(review.ReviewUnavailable):
                review.weekly_review({})

    def test_needs_api_key(self):
        with mock.patch.object(config, "ANTHROPIC_API_KEY", ""):
            with self.assertRaises(review.ReviewUnavailable):
                review.weekly_review({})

    def test_managed_mode_is_unavailable(self):
        with mock.patch.object(config, "MANAGED_MODE", True):
            with self.assertRaises(review.ReviewUnavailable):
                review.weekly_review({})


if __name__ == "__main__":
    unittest.main()
