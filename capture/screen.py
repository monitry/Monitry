import base64

import cv2
import mss
import numpy as np


def grab_screenshot(max_width: int = 1280, quality: int = 75) -> str:
    """Capture the primary screen and return as base64-encoded JPEG string."""
    with mss.mss() as sct:
        monitor = sct.monitors[1]  # primary monitor
        raw = sct.grab(monitor)
        img = np.array(raw)  # BGRA

    img_bgr = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

    h, w = img_bgr.shape[:2]
    if w > max_width:
        scale = max_width / w
        img_bgr = cv2.resize(img_bgr, (max_width, int(h * scale)), interpolation=cv2.INTER_AREA)

    _, buf = cv2.imencode(".jpg", img_bgr, [cv2.IMWRITE_JPEG_QUALITY, quality])
    return base64.b64encode(buf.tobytes()).decode("utf-8")
