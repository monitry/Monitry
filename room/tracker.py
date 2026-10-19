"""Persistent screen identity across capture cycles.

A fresh YOLO detection pass has no memory — box order and count can shift
frame to frame even for a stationary camera (occlusion, jitter, confidence
threshold flicker). ScreenTracker assigns a stable "screen-N" id to each
detected box by greedy IoU matching against the previous cycle's tracks, so
a per-screen activity log can be built across many captures.

No Kalman filtering / motion prediction — captures here are sparse (an
interval-based loop, not 30fps video), so plain IoU-overlap-between-
consecutive-captures is the right amount of complexity, not SORT/DeepSORT.
"""
from __future__ import annotations

import numpy as np


def iou(box_a: np.ndarray, box_b: np.ndarray) -> float:
    ax1, ay1, ax2, ay2 = box_a
    bx1, by1, bx2, by2 = box_b

    ix1, iy1 = max(ax1, bx1), max(ay1, by1)
    ix2, iy2 = min(ax2, bx2), min(ay2, by2)
    inter_w, inter_h = max(0.0, ix2 - ix1), max(0.0, iy2 - iy1)
    intersection = inter_w * inter_h
    if intersection <= 0:
        return 0.0

    area_a = max(0.0, ax2 - ax1) * max(0.0, ay2 - ay1)
    area_b = max(0.0, bx2 - bx1) * max(0.0, by2 - by1)
    union = area_a + area_b - intersection
    return intersection / union if union > 0 else 0.0


class ScreenTracker:
    def __init__(self, iou_threshold: float = 0.3, max_missed: int = 3):
        self.iou_threshold = iou_threshold
        self.max_missed = max_missed
        self._tracks: dict[str, dict] = {}  # id -> {"box": ndarray, "missed": int}
        self._next_id = 1

    def _new_id(self) -> str:
        screen_id = f"screen-{self._next_id}"
        self._next_id += 1
        return screen_id

    def update(self, boxes: list[np.ndarray]) -> list[str]:
        """Match this cycle's boxes against existing tracks. Returns screen
        ids in the same order as `boxes` (one id per input box)."""
        previous_ids = set(self._tracks.keys())

        candidates = []
        for track_id, track in self._tracks.items():
            for box_idx, box in enumerate(boxes):
                score = iou(track["box"], box)
                if score >= self.iou_threshold:
                    candidates.append((score, track_id, box_idx))
        candidates.sort(key=lambda c: c[0], reverse=True)

        matched_track_ids: set[str] = set()
        matched_box_idxs: set[int] = set()
        assignment: dict[int, str] = {}

        for _score, track_id, box_idx in candidates:
            if track_id in matched_track_ids or box_idx in matched_box_idxs:
                continue
            assignment[box_idx] = track_id
            matched_track_ids.add(track_id)
            matched_box_idxs.add(box_idx)

        result_ids: list[str] = []
        for box_idx, box in enumerate(boxes):
            track_id = assignment.get(box_idx) or self._new_id()
            self._tracks[track_id] = {"box": box, "missed": 0}
            result_ids.append(track_id)

        # Age out only tracks that existed before this cycle and went unmatched —
        # tracks created just now (above) must never be touched here.
        for track_id in previous_ids - matched_track_ids:
            self._tracks[track_id]["missed"] += 1
            if self._tracks[track_id]["missed"] > self.max_missed:
                del self._tracks[track_id]

        return result_ids

    @property
    def active_ids(self) -> list[str]:
        return list(self._tracks.keys())
