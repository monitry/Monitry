import unittest

from room.report import RoomReport


class TestRoomReport(unittest.TestCase):
    def test_no_screens_yields_empty_screens_list(self):
        report = RoomReport()
        self.assertEqual(report.screens(), [])

    def test_log_accumulates_entries(self):
        report = RoomReport()
        report.log("screen-1", "reading docs", on_task=True, timestamp=100.0)
        report.log("screen-1", "watching a video", on_task=False, timestamp=110.0)
        entries = report.entries_for("screen-1")
        self.assertEqual(len(entries), 2)
        self.assertEqual(entries[0]["activity"], "reading docs")
        self.assertEqual(entries[1]["on_task"], False)

    def test_screens_ordered_by_first_seen(self):
        report = RoomReport()
        report.log("screen-2", "x", timestamp=200.0)
        report.log("screen-1", "y", timestamp=50.0)
        # screen-1's first entry (50.0) precedes screen-2's (200.0), regardless of log() call order.
        self.assertEqual(report.screens(), ["screen-1", "screen-2"])

    def test_summary_for_unknown_screen(self):
        report = RoomReport()
        summary = report.summary_for("nope")
        self.assertEqual(summary["entry_count"], 0)
        self.assertIsNone(summary["pct_on_task"])

    def test_summary_computes_duration_and_pct_on_task(self):
        report = RoomReport()
        report.log("screen-1", "a", on_task=True, timestamp=0.0)
        report.log("screen-1", "b", on_task=True, timestamp=60.0)
        report.log("screen-1", "c", on_task=False, timestamp=120.0)

        summary = report.summary_for("screen-1")
        self.assertEqual(summary["entry_count"], 3)
        self.assertEqual(summary["duration_seconds"], 120.0)
        self.assertAlmostEqual(summary["pct_on_task"], 200 / 3, places=3)  # 2/3 * 100

    def test_summary_excludes_none_judgments_from_pct(self):
        report = RoomReport()
        report.log("screen-1", "a", on_task=None, timestamp=0.0)
        report.log("screen-1", "b", on_task=True, timestamp=10.0)
        summary = report.summary_for("screen-1")
        self.assertEqual(summary["pct_on_task"], 100.0)  # only the judged entry counts

    def test_summary_all_none_judgments_gives_none_pct(self):
        report = RoomReport()
        report.log("screen-1", "a", on_task=None, timestamp=0.0)
        summary = report.summary_for("screen-1")
        self.assertIsNone(summary["pct_on_task"])

    def test_to_dict_structure(self):
        report = RoomReport()
        report.log("screen-1", "coding", on_task=True, timestamp=0.0)
        data = report.to_dict()
        self.assertIn("screen-1", data["screens"])
        self.assertEqual(data["screens"]["screen-1"]["summary"]["entry_count"], 1)
        self.assertEqual(len(data["screens"]["screen-1"]["entries"]), 1)

    def test_to_markdown_empty_report(self):
        report = RoomReport()
        md = report.to_markdown()
        self.assertIn("No screens were observed", md)

    def test_to_markdown_includes_screen_and_activity(self):
        report = RoomReport()
        report.log("screen-1", "reading the spec", on_task=True, timestamp=0.0)
        report.log("screen-1", "checking social media", on_task=False, timestamp=60.0)
        md = report.to_markdown()
        self.assertIn("screen-1", md)
        self.assertIn("reading the spec", md)
        self.assertIn("[OFF TASK]", md)
        self.assertIn("[on task]", md)

    def test_multiple_screens_each_get_their_own_section(self):
        report = RoomReport()
        report.log("screen-1", "a", timestamp=0.0)
        report.log("screen-2", "b", timestamp=0.0)
        md = report.to_markdown()
        self.assertIn("## screen-1", md)
        self.assertIn("## screen-2", md)


if __name__ == "__main__":
    unittest.main()
