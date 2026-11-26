"""Onitry is free: default edition = own Anthropic key, no license, no Onitry server."""
import os
import subprocess
import sys
import unittest
from unittest.mock import patch

from core import edition

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _run_config(env_extra: dict, code: str) -> str:
    env = {k: v for k, v in os.environ.items() if not k.startswith("ONITRY_")}
    env.update(env_extra)
    env["PYTHONPATH"] = ROOT
    out = subprocess.run(
        [sys.executable, "-c", code], env=env, cwd=ROOT, capture_output=True, text=True, check=True
    )
    return out.stdout.strip()


class TestResolve(unittest.TestCase):
    def test_default_is_free(self):
        self.assertEqual(edition.resolve(""), edition.FREE)
        self.assertEqual(edition.resolve(None), edition.FREE)
        self.assertEqual(edition.resolve("nonsense"), edition.FREE)

    def test_dev_still_works(self):
        self.assertEqual(edition.resolve("dev"), edition.DEV)
        self.assertEqual(edition.resolve(" DEV "), edition.DEV)

    def test_legacy_editions_fall_back_to_free_by_default(self):
        self.assertEqual(edition.resolve("byok"), edition.FREE)
        self.assertEqual(edition.resolve("managed"), edition.FREE)

    def test_legacy_editions_honored_only_with_flag(self):
        self.assertEqual(edition.resolve("byok", legacy_enabled=True), "byok")
        self.assertEqual(edition.resolve("managed", legacy_enabled=True), "managed")
        self.assertEqual(edition.resolve("", legacy_enabled=True), edition.FREE)


class TestFreeStart(unittest.TestCase):
    @patch("core.license.verify", side_effect=AssertionError("free must never verify a license"))
    @patch("httpx.post", side_effect=AssertionError("free must never hit the network here"))
    @patch("httpx.get", side_effect=AssertionError("free must never hit the network here"))
    def test_free_starts_with_just_a_key_and_no_network(self, *_mocks):
        self.assertIsNone(edition.start_error(edition.FREE, "sk-ant-test", license_verified=False))

    def test_free_without_key_says_set_key_and_nothing_about_paying(self):
        msg = edition.start_error(edition.FREE, "", license_verified=False)
        self.assertIn("Set Key", msg)
        for word in ("license", "License", "$", "subscri", "Google", "sign in", "upgrade"):
            self.assertNotIn(word, msg)

    def test_free_does_not_require_license(self):
        self.assertFalse(edition.requires_license(edition.FREE))
        self.assertFalse(edition.requires_license(edition.DEV))
        self.assertTrue(edition.requires_license(edition.LEGACY_BYOK))

    def test_legacy_byok_still_gates_on_cached_license_flag(self):
        self.assertIn("License", edition.start_error("byok", "sk-ant-test", license_verified=False))
        self.assertIsNone(edition.start_error("byok", "sk-ant-test", license_verified=True))

    def test_free_uses_own_key(self):
        self.assertTrue(edition.uses_own_api_key(edition.FREE))
        self.assertFalse(edition.uses_own_api_key("managed"))


class TestConfigDefaults(unittest.TestCase):
    def test_unset_env_gives_free(self):
        self.assertEqual(_run_config({}, "import config; print(config.EDITION)"), "free")

    def test_stale_byok_env_gives_free(self):
        self.assertEqual(
            _run_config({"ONITRY_EDITION": "byok"}, "import config; print(config.EDITION)"), "free"
        )

    def test_stale_managed_env_gives_free_and_no_managed_mode(self):
        out = _run_config(
            {"ONITRY_EDITION": "managed"},
            "import config; print(config.EDITION, config.LEGACY_EDITIONS_ENABLED, config.MANAGED_MODE)",
        )
        self.assertEqual(out, "free False False")

    def test_legacy_flag_revives_byok(self):
        out = _run_config(
            {"ONITRY_EDITION": "byok", "ONITRY_ENABLE_LEGACY_EDITIONS": "1"},
            "import config; print(config.EDITION)",
        )
        self.assertEqual(out, "byok")

    def test_importing_config_does_not_load_legacy_modules(self):
        out = _run_config(
            {}, "import config, sys; print('core.license' in sys.modules, 'core.auth' in sys.modules)"
        )
        self.assertEqual(out, "False False")


if __name__ == "__main__":
    unittest.main()
