"""Register (or remove) Onitry's native-messaging host so the Timecheck
extension's "Launch Onitry" button works.

    python native_host/install.py                 # Chrome, Chromium, Brave, Edge, Arc
    python native_host/install.py --extension-id <id>   # if you loaded it under another ID
    python native_host/install.py --uninstall

Run it with the Python you use for Onitry: the launcher it writes reuses that
interpreter (so your venv and its packages come along).
"""

from __future__ import annotations

import argparse
import json
import os
import stat
import sys

HOST_NAME = "com.onitry.host"
# Fixed by the "key" in timecheck/manifest.json, so it's the same on every machine.
DEFAULT_EXTENSION_ID = "dadagbofodnllhcohbhmjkdolklihcgn"

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOST_SCRIPT = os.path.join(ROOT, "native_host", "host.py")

_MAC_BROWSERS = [
    "Google/Chrome",
    "Google/Chrome Beta",
    "Google/Chrome Canary",
    "Chromium",
    "BraveSoftware/Brave-Browser",
    "Microsoft Edge",
    "Arc/User Data",
]
_LINUX_BROWSERS = [
    "google-chrome",
    "google-chrome-beta",
    "chromium",
    "BraveSoftware/Brave-Browser",
    "microsoft-edge",
]
_WIN_KEYS = [
    r"Software\Google\Chrome\NativeMessagingHosts",
    r"Software\Chromium\NativeMessagingHosts",
    r"Software\BraveSoftware\Brave-Browser\NativeMessagingHosts",
    r"Software\Microsoft\Edge\NativeMessagingHosts",
]


def browser_dirs() -> list[str]:
    """NativeMessagingHosts folders for browsers that are installed (Chrome always)."""
    home = os.path.expanduser("~")
    if sys.platform == "darwin":
        base, names = os.path.join(home, "Library", "Application Support"), _MAC_BROWSERS
    else:
        base, names = os.path.join(home, ".config"), _LINUX_BROWSERS
    out = []
    for i, name in enumerate(names):
        profile = os.path.join(base, name)
        if i == 0 or os.path.isdir(profile):
            out.append(os.path.join(profile, "NativeMessagingHosts"))
    return out


def write_launcher() -> str:
    data = os.path.join(ROOT, "data")
    os.makedirs(data, exist_ok=True)
    if sys.platform == "win32":
        path = os.path.join(data, "onitry-native-host.bat")
        with open(path, "w") as f:
            f.write(f'@echo off\r\n"{sys.executable}" "{HOST_SCRIPT}" %*\r\n')
    else:
        path = os.path.join(data, "onitry-native-host")
        with open(path, "w") as f:
            f.write(f'#!/bin/sh\nexec "{sys.executable}" "{HOST_SCRIPT}" "$@"\n')
        os.chmod(path, os.stat(path).st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return path


def host_manifest(launcher: str, extension_id: str) -> dict:
    return {
        "name": HOST_NAME,
        "description": "Onitry: lets the Timecheck extension start the Onitry app",
        "path": launcher,
        "type": "stdio",
        "allowed_origins": [f"chrome-extension://{extension_id}/"],
    }


def install(extension_id: str) -> list[str]:
    launcher = write_launcher()
    manifest = json.dumps(host_manifest(launcher, extension_id), indent=2)
    written = []
    if sys.platform == "win32":
        import winreg

        path = os.path.join(ROOT, "data", f"{HOST_NAME}.json")
        with open(path, "w") as f:
            f.write(manifest)
        for key in _WIN_KEYS:
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, rf"{key}\{HOST_NAME}") as k:
                winreg.SetValue(k, "", winreg.REG_SZ, path)
            written.append(rf"HKCU\{key}\{HOST_NAME}")
        return written
    for folder in browser_dirs():
        os.makedirs(folder, exist_ok=True)
        path = os.path.join(folder, f"{HOST_NAME}.json")
        with open(path, "w") as f:
            f.write(manifest)
        written.append(path)
    return written


def uninstall() -> list[str]:
    removed = []
    if sys.platform == "win32":
        import winreg

        for key in _WIN_KEYS:
            try:
                winreg.DeleteKey(winreg.HKEY_CURRENT_USER, rf"{key}\{HOST_NAME}")
                removed.append(rf"HKCU\{key}\{HOST_NAME}")
            except OSError:
                pass
        return removed
    for folder in browser_dirs():
        path = os.path.join(folder, f"{HOST_NAME}.json")
        if os.path.exists(path):
            os.remove(path)
            removed.append(path)
    return removed


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--extension-id", default=DEFAULT_EXTENSION_ID)
    parser.add_argument("--uninstall", action="store_true")
    args = parser.parse_args()
    if args.uninstall:
        paths = uninstall()
        print("Removed:" if paths else "Nothing to remove.", *paths, sep="\n  ")
        return
    paths = install(args.extension_id)
    print(f"Registered {HOST_NAME} for chrome-extension://{args.extension_id}/ in:", *paths, sep="\n  ")
    print("Restart the browser, then use Timecheck → ⚙ → Launch Onitry.")


if __name__ == "__main__":
    main()
