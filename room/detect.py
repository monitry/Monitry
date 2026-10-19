"""Screen detection + flattening for camera-based room monitoring.

Ported from ../Emerging Tech/laptop-screen-flatten (YOLOv8 -> SAM -> perspective
warp) with two changes for this use case:
  - detects both laptops AND external monitors/TVs (COCO's "laptop" and "tv"
    classes), not just laptops — a room can have desktop monitors too.
  - never silently drops a screen just because segmentation/corner-finding
    failed. Low-quality camera input (the expected case here) makes SAM
    unreliable; a screen we can still see falls back to a plain axis-aligned
    crop of its YOLO box rather than disappearing from tracking/reporting.

Heavy ML deps (ultralytics/torch) are only imported inside the model loaders,
so importing this module and unit-testing the pure geometry functions
(order_corners, mask_to_corners, flatten_quad) never requires them installed.
"""
from __future__ import annotations

import cv2
import numpy as np

SCREEN_CLASS_NAMES = {"laptop", "tv"}

_yolo = None
_sam = None


def get_yolo(model_path: str = "yolov8n.pt"):
    global _yolo
    if _yolo is None:
        from ultralytics import YOLO
        _yolo = YOLO(model_path)
    return _yolo


def get_sam(model_path: str = "mobile_sam.pt"):
    global _sam
    if _sam is None:
        from ultralytics import SAM
        _sam = SAM(model_path)
    return _sam


def order_corners(pts: np.ndarray) -> np.ndarray:
    """Order 4 points as top-left, top-right, bottom-right, bottom-left."""
    pts = pts.reshape(-1, 2).astype("float32")
    s = pts.sum(axis=1)
    diff = np.diff(pts, axis=1).reshape(-1)
    tl = pts[np.argmin(s)]
    br = pts[np.argmax(s)]
    tr = pts[np.argmin(diff)]
    bl = pts[np.argmax(diff)]
    return np.array([tl, tr, br, bl], dtype="float32")


def mask_to_corners(mask: np.ndarray) -> np.ndarray | None:
    """Reduce a binary mask's outline to 4 ordered corner keypoints."""
    mask_u8 = (mask * 255).astype("uint8")
    contours, _ = cv2.findContours(mask_u8, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None
    contour = max(contours, key=cv2.contourArea)
    if cv2.contourArea(contour) < 200:
        return None

    perimeter = cv2.arcLength(contour, True)
    for eps_frac in (0.02, 0.03, 0.015, 0.04, 0.05, 0.07):
        approx = cv2.approxPolyDP(contour, eps_frac * perimeter, True)
        if len(approx) == 4:
            return order_corners(approx)

    rect = cv2.minAreaRect(contour)
    box = cv2.boxPoints(rect)
    return order_corners(box)


def flatten_quad(image: np.ndarray, corners: np.ndarray) -> np.ndarray:
    """Warp the quadrilateral defined by 4 corners into an upright rectangle."""
    tl, tr, br, bl = corners
    width = int(max(np.linalg.norm(br - bl), np.linalg.norm(tr - tl), 10))
    height = int(max(np.linalg.norm(tr - br), np.linalg.norm(tl - bl), 10))

    dst = np.array(
        [[0, 0], [width - 1, 0], [width - 1, height - 1], [0, height - 1]],
        dtype="float32",
    )
    matrix = cv2.getPerspectiveTransform(corners, dst)
    return cv2.warpPerspective(image, matrix, (width, height))


def raw_crop(image: np.ndarray, box: np.ndarray) -> np.ndarray:
    """Fallback when segmentation fails: a plain axis-aligned crop of the YOLO box."""
    h, w = image.shape[:2]
    x1, y1, x2, y2 = box.astype(int)
    x1, y1 = max(0, x1), max(0, y1)
    x2, y2 = min(w, x2), min(h, y2)
    return image[y1:y2, x1:x2].copy()


def segment_screen(sam, image: np.ndarray, box: np.ndarray) -> np.ndarray | None:
    """Run SAM with a point prompt on the screen portion of a box, then clip
    the resulting mask to the box so stray segmentation can't bleed out."""
    x1, y1, x2, y2 = box.astype(int)
    point_x = int((x1 + x2) / 2)
    point_y = int(y1 + (y2 - y1) * 0.35)  # upper-middle: usually the screen

    result = sam.predict(image, points=[[point_x, point_y]], labels=[1], verbose=False)[0]
    if result.masks is None or len(result.masks.data) == 0:
        return None

    mask = result.masks.data[0].cpu().numpy()
    mask = cv2.resize(mask.astype("uint8"), (image.shape[1], image.shape[0]))

    clipped = np.zeros_like(mask)
    clipped[y1:y2, x1:x2] = mask[y1:y2, x1:x2]
    return clipped


def detect_screens(
    frame: np.ndarray,
    yolo=None,
    sam=None,
    conf: float = 0.25,
) -> list[dict]:
    """Detect every screen (laptop or monitor/TV) in a frame and return a flattened
    (or, on segmentation failure, raw-cropped) image for each, in YOLO's detection
    order. Never returns fewer screens than YOLO found — a detected screen is
    always included, degraded gracefully rather than dropped.

    Each result: {"box": (x1,y1,x2,y2) ndarray, "corners": ndarray|None,
                  "image": ndarray, "method": "warped"|"raw_crop", "class_name": str}
    """
    yolo = yolo or get_yolo()
    sam = sam or get_sam()

    detections = yolo.predict(frame, conf=conf, verbose=False)[0]
    screens = []

    for box_obj in detections.boxes:
        class_name = detections.names[int(box_obj.cls[0])]
        if class_name not in SCREEN_CLASS_NAMES:
            continue
        box = box_obj.xyxy[0].cpu().numpy()

        corners = None
        image = None
        method = "raw_crop"

        mask = segment_screen(sam, frame, box)
        if mask is not None:
            corners = mask_to_corners(mask)
            if corners is not None:
                image = flatten_quad(frame, corners)
                method = "warped"

        if image is None:
            image = raw_crop(frame, box)

        if image.size == 0:
            continue  # degenerate box, nothing usable even as a raw crop

        screens.append({
            "box": box,
            "corners": corners,
            "image": image,
            "method": method,
            "class_name": class_name,
        })

    return screens
