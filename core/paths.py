"""Where Onitry keeps its files.

Running from a checkout, files live in the repo's `data/` folder (as they always did). Inside the packaged macOS app
the code folder is read-only and gets replaced on every update, so files go in
`~/Library/Application Support/Onitry` instead. `ONITRY_DATA_DIR` overrides both.
"""
import os
import sys

APP_NAME = "Onitry"


def frozen() -> bool:
    """True inside the packaged app (PyInstaller sets `sys.frozen`)."""
    return bool(getattr(sys, "frozen", False))


def data_dir(code_root: str) -> str:
    env = os.environ.get("ONITRY_DATA_DIR", "").strip()
    if env:
        return os.path.expanduser(env)
    if frozen():
        return os.path.join(os.path.expanduser("~/Library/Application Support"), APP_NAME)
    return os.path.join(code_root, "data")
