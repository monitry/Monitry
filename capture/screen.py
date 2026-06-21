import base64
import io
import mss
import cv2
import numpy as np
from PIL import Image


def grab_screenshot() -> str:
    """Capture the primary screen and return as base64-encoded JPEG string."""
    with mss.mss() as sct:
        monitor = sct.monitors[1]  # primary monitor
        raw = sct.grab(monitor)
        img = np.array(raw)  # BGRA

    img_bgr = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

    # Resize to max width 1280 to keep API payload small
    h, w = img_bgr.shape[:2]
    if w > 1280:
        scale = 1280 / w
        img_bgr = cv2.resize(img_bgr, (1280, int(h * scale)), interpolation=cv2.INTER_AREA)

    _, buf = cv2.imencode(".jpg", img_bgr, [cv2.IMWRITE_JPEG_QUALITY, 75])
    return base64.b64encode(buf.tobytes()).decode("utf-8")
