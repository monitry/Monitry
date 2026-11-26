import os
import shutil
import tempfile
import unittest
from unittest.mock import patch

import numpy as np

from room.session import RoomSession


def _fake_detection(box, class_name="laptop"):
    return {
        "box": np.array(box, dtype="float32"),
        "corners": None,
        "image": np.zeros((20, 20, 3), dtype="uint8"),
        "method": "raw_crop",
        "class_name": class_name,
    }


class TestRoomSession(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.frame = np.zeros((100, 100, 3), dtype="uint8")

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    @patch("room.session.analyze_screen")
    @patch("room.session.detect_screens")
    def test_run_cycle_logs_each_detected_screen(self, mock_detect, mock_analyze):
        mock_detect.return_value = [_fake_detection([0, 0, 50, 50])]
        mock_analyze.return_value = {"activity": "coding", "onTask": True, "notes": ""}

        session = RoomSession(data_dir=self.tmpdir)
        results = session.run_cycle(self.frame)

        self.assertEqual(len(results), 1)
        screen_id = next(iter(results))
        self.assertEqual(screen_id, "screen-1")
        entries = session.report.entries_for(screen_id)
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["activity"], "coding")
        self.assertTrue(entries[0]["on_task"])

    @patch("room.session.analyze_screen")
    @patch("room.session.detect_screens")
    def test_run_cycle_creates_a_context_file_per_screen(self, mock_detect, mock_analyze):
        mock_detect.return_value = [_fake_detection([0, 0, 50, 50])]
        mock_analyze.return_value = {"activity": "coding", "onTask": True, "notes": ""}

        session = RoomSession(data_dir=self.tmpdir)
        session.run_cycle(self.frame)

        self.assertTrue(os.path.exists(os.path.join(self.tmpdir, "screen-1.txt")))

    @patch("room.session.analyze_screen")
    @patch("room.session.detect_screens")
    def test_off_task_activity_gets_tagged_in_context_log(self, mock_detect, mock_analyze):
        mock_detect.return_value = [_fake_detection([0, 0, 50, 50])]
        mock_analyze.return_value = {"activity": "watching videos", "onTask": False, "notes": ""}

        session = RoomSession(data_dir=self.tmpdir)
        session.run_cycle(self.frame)

        with open(os.path.join(self.tmpdir, "screen-1.txt")) as f:
            content = f.read()
        self.assertIn("[OFF-TASK] watching videos", content)

    @patch("room.session.analyze_screen")
    @patch("room.session.detect_screens")
    def test_same_screen_across_cycles_keeps_its_id_and_accumulates_log(self, mock_detect, mock_analyze):
        mock_analyze.return_value = {"activity": "x", "onTask": None, "notes": ""}
        session = RoomSession(data_dir=self.tmpdir)

        mock_detect.return_value = [_fake_detection([0, 0, 50, 50])]
        first = session.run_cycle(self.frame)
        mock_detect.return_value = [_fake_detection([2, 2, 52, 52])]  # tiny jitter
        second = session.run_cycle(self.frame)

        self.assertEqual(list(first.keys()), list(second.keys()))
        self.assertEqual(len(session.report.entries_for("screen-1")), 2)

    @patch("room.session.forget_screen")
    @patch("room.session.analyze_screen")
    @patch("room.session.detect_screens")
    def test_evicted_screen_forgets_its_analyzer_notes(self, mock_detect, mock_analyze, mock_forget):
        mock_analyze.return_value = {"activity": "x", "onTask": None, "notes": ""}
        session = RoomSession(data_dir=self.tmpdir)  # default max_missed=3

        mock_detect.return_value = [_fake_detection([0, 0, 50, 50])]
        session.run_cycle(self.frame)

        mock_detect.return_value = []
        for _ in range(5):  # exceed max_missed
            session.run_cycle(self.frame)

        mock_forget.assert_called_with("screen-1")

    @patch("room.session.analyze_screen")
    @patch("room.session.detect_screens")
    def test_per_screen_task_is_passed_to_analyzer(self, mock_detect, mock_analyze):
        mock_detect.return_value = [_fake_detection([0, 0, 50, 50])]
        mock_analyze.return_value = {"activity": "x", "onTask": True, "notes": ""}

        session = RoomSession(tasks={"screen-1": "finish homework"}, data_dir=self.tmpdir)
        session.run_cycle(self.frame)

        called_task = mock_analyze.call_args.kwargs["task"]
        self.assertEqual(called_task, "finish homework")

    @patch("room.session.analyze_screen")
    @patch("room.session.detect_screens")
    def test_no_screens_detected_returns_empty_results(self, mock_detect, mock_analyze):
        mock_detect.return_value = []
        session = RoomSession(data_dir=self.tmpdir)
        results = session.run_cycle(self.frame)
        self.assertEqual(results, {})
        mock_analyze.assert_not_called()


if __name__ == "__main__":
    unittest.main()
