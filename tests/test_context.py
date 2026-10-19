import os
import shutil
import tempfile
import unittest

from core import context


class TestContextLog(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.path = os.path.join(self.tmpdir, "session", "context.txt")

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_read_tail_missing_file_returns_empty(self):
        self.assertEqual(context.read_tail(self.path), "")

    def test_init_log_creates_header(self):
        context.init_log(self.path, "finish the report")
        with open(self.path) as f:
            content = f.read()
        self.assertIn("Task: finish the report", content)

    def test_append_then_read_tail(self):
        context.init_log(self.path, "task")
        context.append(self.path, "reading docs")
        context.append(self.path, "writing code")
        tail = context.read_tail(self.path)
        self.assertIn("reading docs", tail)
        self.assertIn("writing code", tail)

    def test_relative_path_with_no_directory_component(self):
        # Regression test: os.path.dirname("context.txt") == "", and
        # os.makedirs("", exist_ok=True) raises FileNotFoundError — init_log/append
        # must not blindly call makedirs on an empty directory component.
        orig_cwd = os.getcwd()
        try:
            os.chdir(self.tmpdir)
            context.init_log("context.txt", "task")
            context.append("context.txt", "activity")
            self.assertTrue(os.path.exists("context.txt"))
        finally:
            os.chdir(orig_cwd)

    def test_read_tail_limits_to_max_lines(self):
        context.init_log(self.path, "task")
        for i in range(15):
            context.append(self.path, f"activity {i}")
        tail = context.read_tail(self.path, max_lines=10)
        lines = tail.splitlines()
        self.assertEqual(len(lines), 10)
        self.assertIn("activity 14", tail)
        self.assertNotIn("activity 4\n", tail + "\n")  # earliest kept lines dropped


if __name__ == "__main__":
    unittest.main()
