import subprocess
import unittest
from unittest.mock import MagicMock, patch

from core import idle

_SAMPLE_IOREG_OUTPUT = b"""\
+-o IOHIDSystem  <class IOHIDSystem, id 0x100000275, registered, matched, active, busy 0 (0 ms), retain 6>
    {
      "IOSharedMemory" = "<...>"
      "IOHIDIdleNotify" = 0
      "HIDIdleTime" = 102169396916
      "IOHIDSystem986Notification" = 0
    }
"""


class TestGetIdleSeconds(unittest.TestCase):
    @patch("core.idle.subprocess.run")
    def test_parses_nanoseconds_to_seconds(self, mock_run):
        mock_run.return_value = MagicMock(stdout=_SAMPLE_IOREG_OUTPUT)
        self.assertAlmostEqual(idle.get_idle_seconds(), 102.169396916, places=6)

    @patch("core.idle.subprocess.run")
    def test_zero_idle_time(self, mock_run):
        mock_run.return_value = MagicMock(stdout=b'"HIDIdleTime" = 0')
        self.assertEqual(idle.get_idle_seconds(), 0.0)

    @patch("core.idle.subprocess.run")
    def test_unparseable_output_returns_zero(self, mock_run):
        mock_run.return_value = MagicMock(stdout=b"nothing useful here")
        self.assertEqual(idle.get_idle_seconds(), 0.0)

    @patch("core.idle.subprocess.run")
    def test_ioreg_missing_fails_open(self, mock_run):
        mock_run.side_effect = FileNotFoundError("ioreg not found")
        self.assertEqual(idle.get_idle_seconds(), 0.0)

    @patch("core.idle.subprocess.run")
    def test_ioreg_timeout_fails_open(self, mock_run):
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="ioreg", timeout=5)
        self.assertEqual(idle.get_idle_seconds(), 0.0)

    @patch("core.idle.subprocess.run")
    def test_ioreg_nonzero_exit_fails_open(self, mock_run):
        mock_run.side_effect = subprocess.CalledProcessError(returncode=1, cmd="ioreg")
        self.assertEqual(idle.get_idle_seconds(), 0.0)


if __name__ == "__main__":
    unittest.main()
