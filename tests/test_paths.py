"""Where files go: the repo's data/ folder, the app's Application Support folder, or an override."""
import os
import subprocess
import sys
import unittest
from unittest import mock

from core import paths

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class DataDirTests(unittest.TestCase):
    def test_a_checkout_keeps_using_its_own_data_folder(self):
        with mock.patch.dict(os.environ, {}, clear=False), mock.patch.object(paths, "frozen", return_value=False):
            os.environ.pop("ONITRY_DATA_DIR", None)
            self.assertEqual(paths.data_dir("/code"), os.path.join("/code", "data"))

    def test_the_packaged_app_uses_application_support(self):
        with mock.patch.dict(os.environ, {}, clear=False), mock.patch.object(paths, "frozen", return_value=True):
            os.environ.pop("ONITRY_DATA_DIR", None)
            got = paths.data_dir("/inside/Onitry.app")
            self.assertTrue(got.endswith(os.path.join("Library", "Application Support", "Onitry")))
            self.assertNotIn("Onitry.app", got, "never inside the (read-only, replaced-on-update) app bundle")

    def test_the_environment_overrides_both(self):
        with mock.patch.dict(os.environ, {"ONITRY_DATA_DIR": "/tmp/somewhere"}), mock.patch.object(paths, "frozen", return_value=True):
            self.assertEqual(paths.data_dir("/code"), "/tmp/somewhere")

    def test_frozen_follows_pyinstaller(self):
        with mock.patch.object(sys, "frozen", True, create=True):
            self.assertTrue(paths.frozen())
        self.assertFalse(paths.frozen())

    def test_config_files_live_in_the_data_folder(self):
        code = (
            "import config, os\n"
            "d = config.DATA_DIR\n"
            "files = [config.CONTEXT_FILE, config.STATUS_FILE, config.SETTINGS_FILE, config.BRIDGE_TOKEN_FILE]\n"
            "assert all(os.path.dirname(f) == d for f in files), files\n"
            "print(d)\n"
        )
        env = dict(os.environ, ONITRY_DATA_DIR="/tmp/onitry-paths-test")
        out = subprocess.run([sys.executable, "-c", code], cwd=ROOT, env=env, capture_output=True, text=True)
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertEqual(out.stdout.strip(), "/tmp/onitry-paths-test")


if __name__ == "__main__":
    unittest.main()
