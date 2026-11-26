import json
import os
import shutil
import tempfile
import unittest

from core import status


class TestStatusWrite(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.mkdtemp()
        self._orig_cwd = os.getcwd()

    def tearDown(self):
        os.chdir(self._orig_cwd)
        shutil.rmtree(self._tmpdir, ignore_errors=True)

    def test_writes_expected_json_shape(self):
        path = os.path.join(self._tmpdir, "status.json")
        status.write(path, "on_task", task="write code", activity="coding", cost=1.23)

        with open(path) as f:
            data = json.load(f)
        self.assertEqual(
            data, {"status": "on_task", "task": "write code", "activity": "coding", "cost": 1.23}
        )

    def test_creates_missing_parent_directories(self):
        path = os.path.join(self._tmpdir, "nested", "dirs", "status.json")
        status.write(path, "idle")
        self.assertTrue(os.path.exists(path))

    def test_relative_path_with_no_directory_component(self):
        # Regression test: os.path.dirname("status.json") == "", and
        # os.makedirs("", exist_ok=True) raises FileNotFoundError — write()
        # must not blindly call makedirs on an empty directory component.
        os.chdir(self._tmpdir)
        status.write("status.json", "idle")
        self.assertTrue(os.path.exists("status.json"))

    def test_defaults_for_optional_fields(self):
        path = os.path.join(self._tmpdir, "status.json")
        status.write(path, "stopped")
        with open(path) as f:
            data = json.load(f)
        self.assertEqual(data, {"status": "stopped", "task": "", "activity": "", "cost": 0.0})


if __name__ == "__main__":
    unittest.main()
