import io
import json
import os
import struct
import sys
import tempfile
import unittest
from unittest import mock

from native_host import host, install


def _frame(obj) -> bytes:
    body = json.dumps(obj).encode()
    return struct.pack("<I", len(body)) + body


class _Stdio:
    def __init__(self, data: bytes):
        self.buffer = io.BytesIO(data)


class TestHostProtocol(unittest.TestCase):
    def run_host(self, message):
        stdin, stdout = _Stdio(_frame(message)), _Stdio(b"")
        with mock.patch.object(sys, "stdin", stdin), mock.patch.object(sys, "stdout", stdout):
            host.main()
        raw = stdout.buffer.getvalue()
        (n,) = struct.unpack("<I", raw[:4])
        return json.loads(raw[4 : 4 + n])

    def test_ping(self):
        with mock.patch.object(host, "bridge_listening", return_value=False):
            self.assertEqual(self.run_host({"cmd": "ping"}), {"ok": True, "bridge": False})

    def test_launch_skips_when_running(self):
        with (
            mock.patch.object(host, "bridge_listening", return_value=True),
            mock.patch.object(host.subprocess, "Popen") as popen,
        ):
            out = self.run_host({"cmd": "launch"})
        self.assertTrue(out["already_running"])
        popen.assert_not_called()

    def test_launch_starts_detached_gui(self):
        with (
            tempfile.TemporaryDirectory() as tmp,
            mock.patch.object(host, "ROOT", tmp),
            mock.patch.object(host, "bridge_listening", return_value=False),
            mock.patch.object(host.subprocess, "Popen") as popen,
        ):
            out = self.run_host({"cmd": "launch"})
        self.assertTrue(out["launched"])
        args, kwargs = popen.call_args
        self.assertTrue(args[0][1].endswith("gui.py"))
        self.assertTrue(kwargs["start_new_session"])
        self.assertIsNot(kwargs["stdout"], None)

    def test_unknown_command(self):
        self.assertFalse(self.run_host({"cmd": "rm -rf"})["ok"])


@unittest.skipIf(sys.platform == "win32", "file-based install only")
class TestInstall(unittest.TestCase):
    def test_install_and_uninstall(self):
        with (
            tempfile.TemporaryDirectory() as tmp,
            mock.patch.dict(os.environ, {"HOME": tmp}),
            mock.patch.object(install, "ROOT", tmp),
        ):
            paths = install.install("abcdefghijklmnopabcdefghijklmnop")
            self.assertTrue(paths)
            with open(paths[0]) as f:
                manifest = json.load(f)
            self.assertEqual(manifest["name"], "com.onitry.host")
            self.assertEqual(
                manifest["allowed_origins"], ["chrome-extension://abcdefghijklmnopabcdefghijklmnop/"]
            )
            self.assertTrue(os.access(manifest["path"], os.X_OK))
            self.assertEqual(install.uninstall(), paths)


if __name__ == "__main__":
    unittest.main()
