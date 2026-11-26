import unittest
from types import SimpleNamespace
from unittest.mock import patch

import anthropic

from ai import client


def _fake_message(text, input_tokens=100, output_tokens=100):
    return SimpleNamespace(
        content=[SimpleNamespace(text=text)],
        usage=SimpleNamespace(input_tokens=input_tokens, output_tokens=output_tokens),
    )


class TestResponseParsing(unittest.TestCase):
    def setUp(self):
        client.reset_session()

    def tearDown(self):
        client.reset_session()

    @patch("ai.client._create_with_retry")
    def test_plain_json_no_fence(self, mock_create):
        mock_create.return_value = _fake_message(
            '{"onTask": true, "activity": "coding", "reminder": "", "notes": ""}'
        )
        result = client.analyze("task", "b64", "")
        self.assertTrue(result["onTask"])
        self.assertEqual(result["activity"], "coding")

    @patch("ai.client._create_with_retry")
    def test_json_fence_with_language_tag(self, mock_create):
        mock_create.return_value = _fake_message(
            '```json\n{"onTask": false, "activity": "browsing", "reminder": "focus", "notes": ""}\n```'
        )
        result = client.analyze("task", "b64", "")
        self.assertFalse(result["onTask"])
        self.assertEqual(result["reminder"], "focus")

    @patch("ai.client._create_with_retry")
    def test_bare_fence_without_language_tag(self, mock_create):
        mock_create.return_value = _fake_message(
            '```\n{"onTask": true, "activity": "reading", "reminder": "", "notes": ""}\n```'
        )
        result = client.analyze("task", "b64", "")
        self.assertTrue(result["onTask"])
        self.assertEqual(result["activity"], "reading")

    @patch("ai.client._create_with_retry")
    def test_embedded_triple_backtick_in_content_survives(self, mock_create):
        # Regression test: activity descriptions can legitimately quote code containing
        # ``` (e.g. describing a markdown file on screen). A naive `.split("```")[1]`
        # would truncate the JSON at that inner occurrence instead of the real fence.
        payload = (
            '```json\n'
            '{"onTask": true, "activity": "editing a README with a ```python code block```", '
            '"reminder": "", "notes": ""}\n'
            '```'
        )
        mock_create.return_value = _fake_message(payload)
        result = client.analyze("task", "b64", "")
        self.assertTrue(result["onTask"])
        self.assertIn("```python code block```", result["activity"])

    @patch("ai.client._create_with_retry")
    def test_notes_carry_across_calls(self, mock_create):
        mock_create.side_effect = [
            _fake_message('{"onTask": true, "activity": "a", "reminder": "", "notes": "first note"}'),
            _fake_message('{"onTask": true, "activity": "b", "reminder": "", "notes": "second note"}'),
        ]
        client.analyze("task", "b64", "")
        second_call_kwargs = None

        def capture(*args, **kwargs):
            nonlocal second_call_kwargs
            second_call_kwargs = kwargs
            return _fake_message('{"onTask": true, "activity": "b", "reminder": "", "notes": "second note"}')

        mock_create.side_effect = None
        mock_create.side_effect = capture
        client.analyze("task", "b64", "")

        sent_text = second_call_kwargs["messages"][0]["content"][1]["text"]
        self.assertIn("first note", sent_text)


class TestRetry(unittest.TestCase):
    def setUp(self):
        client.reset_session()

    def tearDown(self):
        client.reset_session()

    @patch("ai.client._get_client")
    @patch("ai.client.time.sleep")
    def test_retries_on_retryable_error_then_succeeds(self, mock_sleep, mock_get_client):
        mock_messages = mock_get_client.return_value.messages
        mock_messages.create.side_effect = [
            anthropic.APITimeoutError(request=SimpleNamespace()),
            _fake_message('{"onTask": true, "activity": "a", "reminder": "", "notes": ""}'),
        ]
        result = client.analyze("task", "b64", "")
        self.assertTrue(result["onTask"])
        self.assertEqual(mock_messages.create.call_count, 2)
        mock_sleep.assert_called_once()

    @patch("ai.client._get_client")
    @patch("ai.client.time.sleep")
    def test_raises_after_exhausting_retries(self, mock_sleep, mock_get_client):
        mock_messages = mock_get_client.return_value.messages
        mock_messages.create.side_effect = anthropic.APITimeoutError(request=SimpleNamespace())
        with self.assertRaises(anthropic.APITimeoutError):
            client.analyze("task", "b64", "")
        self.assertEqual(mock_messages.create.call_count, 3)  # initial + 2 retries

    @patch("ai.client._get_client")
    def test_non_retryable_error_raises_immediately(self, mock_get_client):
        mock_messages = mock_get_client.return_value.messages
        mock_messages.create.side_effect = ValueError("not a retryable error")
        with self.assertRaises(ValueError):
            client.analyze("task", "b64", "")
        self.assertEqual(mock_messages.create.call_count, 1)


if __name__ == "__main__":
    unittest.main()
