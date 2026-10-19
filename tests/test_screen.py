import base64
import unittest
from unittest.mock import MagicMock, patch

import numpy as np

from capture import screen


def _fake_mss(width, height):
    mock_sct = MagicMock()
    mock_sct.monitors = [None, {"left": 0, "top": 0, "width": width, "height": height}]
    mock_sct.grab.return_value = np.zeros((height, width, 4), dtype=np.uint8)
    mock_cm = MagicMock()
    mock_cm.__enter__.return_value = mock_sct
    mock_cm.__exit__.return_value = False
    return mock_cm


class TestGrabScreenshot(unittest.TestCase):
    @patch("capture.screen.mss.mss")
    def test_returns_valid_base64_jpeg(self, mock_mss):
        mock_mss.return_value = _fake_mss(200, 100)
        result = screen.grab_screenshot()
        # A real JPEG file starts with the 0xFFD8 magic bytes.
        decoded = base64.b64decode(result)
        self.assertEqual(decoded[:2], b"\xff\xd8")

    @patch("capture.screen.mss.mss")
    def test_captures_the_primary_monitor_not_the_virtual_bounding_box(self, mock_mss):
        # sct.monitors[0] is the union of every display; [1] is the actual primary
        # monitor — grabbing [0] on a multi-monitor setup would capture everything.
        mock_cm = _fake_mss(200, 100)
        mock_mss.return_value = mock_cm
        screen.grab_screenshot()
        called_monitor = mock_cm.__enter__.return_value.grab.call_args.args[0]
        self.assertEqual(called_monitor, {"left": 0, "top": 0, "width": 200, "height": 100})

    @patch("capture.screen.mss.mss")
    def test_downscales_when_wider_than_max_width(self, mock_mss):
        mock_mss.return_value = _fake_mss(2560, 1440)
        result = screen.grab_screenshot(max_width=800, quality=75)
        decoded = base64.b64decode(result)
        arr = np.frombuffer(decoded, dtype=np.uint8)
        import cv2
        img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        self.assertEqual(img.shape[1], 800)
        self.assertEqual(img.shape[0], round(1440 * 800 / 2560))

    @patch("capture.screen.mss.mss")
    def test_no_downscale_when_narrower_than_max_width(self, mock_mss):
        mock_mss.return_value = _fake_mss(200, 100)
        result = screen.grab_screenshot(max_width=1280, quality=75)
        decoded = base64.b64decode(result)
        arr = np.frombuffer(decoded, dtype=np.uint8)
        import cv2
        img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        self.assertEqual(img.shape[1], 200)
        self.assertEqual(img.shape[0], 100)

    @patch("capture.screen.cv2.imencode")
    @patch("capture.screen.mss.mss")
    def test_raises_if_jpeg_encoding_fails(self, mock_mss, mock_imencode):
        mock_mss.return_value = _fake_mss(200, 100)
        mock_imencode.return_value = (False, None)
        with self.assertRaises(ValueError):
            screen.grab_screenshot()


if __name__ == "__main__":
    unittest.main()
