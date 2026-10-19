import os
import shutil
import tempfile
import unittest

from core import settings


class TestSettings(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.path = os.path.join(self.tmpdir, "settings.json")

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_load_missing_file_returns_defaults(self):
        loaded = settings.load(self.path)
        self.assertEqual(loaded, dict(settings.DEFAULTS))

    def test_save_then_load_roundtrips(self):
        settings.save(self.path, {"jpeg_quality": 40})
        loaded = settings.load(self.path)
        self.assertEqual(loaded["jpeg_quality"], 40)

    def test_save_merges_instead_of_clobbering(self):
        # One "screen" saves quality, a different one later saves model —
        # the second save must not wipe out the first screen's key.
        settings.save(self.path, {"jpeg_quality": 40})
        settings.save(self.path, {"model_label": "Haiku"})
        loaded = settings.load(self.path)
        self.assertEqual(loaded["jpeg_quality"], 40)
        self.assertEqual(loaded["model_label"], "Haiku")

    def test_save_overwrites_only_the_given_key(self):
        settings.save(self.path, {"jpeg_quality": 40, "model_label": "Haiku"})
        settings.save(self.path, {"jpeg_quality": 90})
        loaded = settings.load(self.path)
        self.assertEqual(loaded["jpeg_quality"], 90)
        self.assertEqual(loaded["model_label"], "Haiku")

    def test_relative_path_with_no_directory_component(self):
        # Regression test: os.path.dirname("settings.json") == "", and
        # os.makedirs("", exist_ok=True) raises FileNotFoundError — save() must
        # not blindly call makedirs on an empty directory component.
        orig_cwd = os.getcwd()
        try:
            os.chdir(self.tmpdir)
            settings.save("settings.json", {"jpeg_quality": 40})
            self.assertTrue(os.path.exists("settings.json"))
        finally:
            os.chdir(orig_cwd)


if __name__ == "__main__":
    unittest.main()
