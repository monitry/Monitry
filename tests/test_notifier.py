import unittest
from unittest.mock import patch

from alerts import notifier


class TestEscaping(unittest.TestCase):
    def test_quotes_are_escaped(self):
        self.assertEqual(notifier._escape_applescript_string('say "hi"'), 'say \\"hi\\"')

    def test_backslash_is_escaped(self):
        self.assertEqual(notifier._escape_applescript_string("C:\\path"), "C:\\\\path")

    def test_trailing_backslash_before_quote_does_not_close_string_early(self):
        # Regression test for the AppleScript-injection bug: a message ending in a
        # literal backslash immediately followed by a quote used to collapse to an
        # escaped backslash + an UNESCAPED quote (\\\\" ), which closes the AppleScript
        # string early and lets anything after it run as live AppleScript. Escaping
        # backslash first means the quote stays escaped no matter what precedes it.
        malicious = 'foo\\" & (do shell script "touch /tmp/pwned") & "'
        escaped = notifier._escape_applescript_string(malicious)
        script = f'display notification "{escaped}" with title "t"'

        # The only unescaped quotes in the whole script must be the four that
        # legitimately open/close the notification and title string literals.
        unescaped_quote_count = 0
        i = 0
        while i < len(script):
            if script[i] == "\\":
                i += 2
                continue
            if script[i] == '"':
                unescaped_quote_count += 1
            i += 1
        self.assertEqual(unescaped_quote_count, 4)


class TestNotify(unittest.TestCase):
    @patch("alerts.notifier.subprocess.run")
    def test_builds_osascript_command_with_sound(self, mock_run):
        notifier.notify("Title", "Message", sound=True)
        args = mock_run.call_args.args[0]
        self.assertEqual(args[0], "osascript")
        self.assertIn('display notification "Message" with title "Title" sound name "Basso"', args[2])

    @patch("alerts.notifier.subprocess.run")
    def test_silent_banner_has_no_sound_clause(self, mock_run):
        notifier.notify("Title", "Message", sound=False)
        script = mock_run.call_args.args[0][2]
        self.assertNotIn("sound name", script)

    @patch("alerts.notifier.subprocess.run")
    def test_does_not_raise_on_nonzero_exit(self, mock_run):
        # check=False means a failing osascript call (e.g. no display attached)
        # degrades silently instead of raising CalledProcessError mid-monitoring-loop.
        notifier.notify("Title", "Message")
        self.assertEqual(mock_run.call_args.kwargs.get("check"), False)


class TestAlertOffTask(unittest.TestCase):
    @patch("alerts.notifier.speak")
    def test_interrupt_speaks_the_reminder(self, mock_speak):
        notifier.alert_off_task("write code", "Get back to it", interrupt=True)
        mock_speak.assert_called_once_with("Get back to it")

    @patch("alerts.notifier.speak")
    def test_interrupt_falls_back_to_task_when_no_reminder(self, mock_speak):
        notifier.alert_off_task("write code", "", interrupt=True)
        mock_speak.assert_called_once_with("Get back to: write code")

    @patch("alerts.notifier.notify")
    def test_soft_notification_is_silent(self, mock_notify):
        notifier.alert_off_task("write code", "Get back to it", interrupt=False)
        mock_notify.assert_called_once_with("Full Focus", "Get back to it", sound=False)


if __name__ == "__main__":
    unittest.main()
