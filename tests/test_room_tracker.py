import unittest

import numpy as np

from room.tracker import ScreenTracker, iou


def box(x1, y1, x2, y2):
    return np.array([x1, y1, x2, y2], dtype="float32")


class TestIou(unittest.TestCase):
    def test_identical_boxes_iou_is_one(self):
        self.assertAlmostEqual(iou(box(0, 0, 10, 10), box(0, 0, 10, 10)), 1.0)

    def test_disjoint_boxes_iou_is_zero(self):
        self.assertEqual(iou(box(0, 0, 10, 10), box(100, 100, 110, 110)), 0.0)

    def test_partial_overlap(self):
        # 10x10 boxes overlapping in a 5x5 region -> intersection 25, union 175
        score = iou(box(0, 0, 10, 10), box(5, 5, 15, 15))
        self.assertAlmostEqual(score, 25 / 175, places=4)


class TestScreenTracker(unittest.TestCase):
    def test_first_cycle_assigns_new_ids(self):
        tracker = ScreenTracker()
        ids = tracker.update([box(0, 0, 100, 100), box(200, 200, 300, 300)])
        self.assertEqual(len(ids), 2)
        self.assertEqual(len(set(ids)), 2)  # distinct

    def test_stationary_screen_keeps_its_id(self):
        tracker = ScreenTracker()
        first_ids = tracker.update([box(0, 0, 100, 100)])
        second_ids = tracker.update([box(2, 2, 102, 102)])  # nearly identical, tiny jitter
        self.assertEqual(first_ids, second_ids)

    def test_two_screens_matched_independently_not_crossed(self):
        tracker = ScreenTracker()
        first_ids = tracker.update([box(0, 0, 100, 100), box(500, 500, 600, 600)])
        second_ids = tracker.update([box(500, 500, 600, 600), box(0, 0, 100, 100)])  # order swapped
        # second_ids[0] corresponds to the (500,500) box -> should match first_ids[1]
        self.assertEqual(second_ids[0], first_ids[1])
        self.assertEqual(second_ids[1], first_ids[0])

    def test_screen_that_jumps_far_gets_a_new_id(self):
        # No motion prediction by design — a screen that moves further than the
        # IoU threshold in one step is indistinguishable from a brand new screen.
        tracker = ScreenTracker()
        first_ids = tracker.update([box(0, 0, 100, 100)])
        second_ids = tracker.update([box(900, 900, 1000, 1000)])
        self.assertNotEqual(first_ids[0], second_ids[0])

    def test_track_survives_a_brief_disappearance(self):
        tracker = ScreenTracker(max_missed=2)
        first_ids = tracker.update([box(0, 0, 100, 100)])
        tracker.update([])  # screen briefly not detected
        tracker.update([])
        third_ids = tracker.update([box(0, 0, 100, 100)])  # reappears in the same spot
        self.assertEqual(first_ids[0], third_ids[0])

    def test_track_evicted_after_max_missed_cycles(self):
        tracker = ScreenTracker(max_missed=1)
        first_ids = tracker.update([box(0, 0, 100, 100)])
        tracker.update([])  # missed 1
        tracker.update([])  # missed 2 -> exceeds max_missed=1, evicted
        fourth_ids = tracker.update([box(0, 0, 100, 100)])
        self.assertNotEqual(first_ids[0], fourth_ids[0])

    def test_new_track_is_not_penalized_in_the_cycle_it_appears(self):
        # Regression test: a freshly created track must start with missed=0,
        # not be immediately aged in the same update() call that created it.
        tracker = ScreenTracker(max_missed=0)
        ids = tracker.update([box(0, 0, 100, 100)])
        # With max_missed=0, if the new track were incorrectly aged this cycle,
        # it would already be evicted -- confirm it's still active.
        self.assertIn(ids[0], tracker.active_ids)

    def test_active_ids_reflects_current_tracks(self):
        tracker = ScreenTracker()
        tracker.update([box(0, 0, 100, 100), box(200, 200, 300, 300)])
        self.assertEqual(len(tracker.active_ids), 2)

    def test_empty_boxes_returns_empty_ids(self):
        tracker = ScreenTracker()
        self.assertEqual(tracker.update([]), [])


if __name__ == "__main__":
    unittest.main()
