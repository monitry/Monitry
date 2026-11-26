"""Orchestrates one room-monitoring capture cycle: detect screens in a camera
frame, track their identity across cycles, analyze each with Claude, and log
the result — both to this session's RoomReport and to a per-screen context
file on disk (reusing core/context.py, so history survives a restart)."""
from __future__ import annotations

import base64
import os

import cv2

from core import context as context_log
from core import paths
from room.analyzer import analyze_screen, forget_screen, reset_session
from room.detect import detect_screens
from room.report import RoomReport
from room.tracker import ScreenTracker

ROOM_DATA_DIR = os.path.join(paths.data_dir(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "room")
MAX_WIDTH = 800    # per-screen image sent to Claude — cost control, matches capture/screen.py
JPEG_QUALITY = 75


def _encode_jpeg(image, max_width: int = MAX_WIDTH, quality: int = JPEG_QUALITY) -> str:
    h, w = image.shape[:2]
    if w > max_width:
        scale = max_width / w
        image = cv2.resize(image, (max_width, max(1, int(h * scale))), interpolation=cv2.INTER_AREA)
    ok, buf = cv2.imencode(".jpg", image, [cv2.IMWRITE_JPEG_QUALITY, quality])
    if not ok:
        raise ValueError("Failed to JPEG-encode screen crop")
    return base64.b64encode(buf.tobytes()).decode("utf-8")


class RoomSession:
    def __init__(self, tasks: dict[str, str] | None = None, conf: float = 0.25, data_dir: str = ROOM_DATA_DIR):
        self.tracker = ScreenTracker()
        self.report = RoomReport()
        self.tasks = tasks or {}  # screen_id -> task string; empty = describe-only, no on/off-task judgment
        self.conf = conf
        self.data_dir = data_dir
        self._known_ids: set[str] = set()
        os.makedirs(self.data_dir, exist_ok=True)
        reset_session()

    def _context_path(self, screen_id: str) -> str:
        return os.path.join(self.data_dir, f"{screen_id}.txt")

    def run_cycle(self, frame) -> dict[str, dict]:
        """Detect + track + analyze every screen visible in `frame`.
        Returns {screen_id: analysis_result} for screens seen this cycle."""
        detections = detect_screens(frame, conf=self.conf)
        boxes = [d["box"] for d in detections]
        screen_ids = self.tracker.update(boxes)

        results: dict[str, dict] = {}
        for screen_id, detection in zip(screen_ids, detections, strict=True):
            image_b64 = _encode_jpeg(detection["image"])
            context_path = self._context_path(screen_id)
            task = self.tasks.get(screen_id, "")

            if not os.path.exists(context_path):
                context_log.init_log(context_path, task)
            context = context_log.read_tail(context_path)

            result = analyze_screen(screen_id, image_b64, context=context, task=task)
            activity = result.get("activity", "unknown")
            on_task = result.get("onTask")

            log_line = activity if on_task is not False else f"[OFF-TASK] {activity}"
            context_log.append(context_path, log_line)
            self.report.log(screen_id, activity, on_task=on_task)
            results[screen_id] = result

        self._forget_evicted_screens()
        return results

    def _forget_evicted_screens(self) -> None:
        """Drop analyzer notes for screens the tracker no longer sees, so a
        future unrelated screen never inherits stale context."""
        active = set(self.tracker.active_ids)
        for screen_id in self._known_ids - active:
            forget_screen(screen_id)
        self._known_ids = active
