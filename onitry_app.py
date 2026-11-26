"""Entry point of the packaged macOS app (the thing the Onitry icon runs).

    Onitry.app            opens the Full Focus window
    Onitry --selftest     imports everything the app needs and exits 0 (used by CI to check a build)

From a checkout you can still run `python gui.py` or `python menubar.py` as before.
"""
import multiprocessing
import sys


def selftest() -> int:
    """Import every module the window needs, without opening one. Exits non-zero with the reason on failure."""
    problems = []
    for name in ("tkinter", "httpx", "anthropic", "keyring", "mss", "numpy", "cv2", "config", "gui", "core.paths"):
        try:
            __import__(name)
        except Exception as exc:  # report every failure, not just the first
            problems.append(f"{name}: {exc}")
    try:
        import keyring

        backend = keyring.get_keyring().__class__.__name__
        print(f"keyring backend: {backend}")
    except Exception as exc:
        problems.append(f"keyring backend: {exc}")
    try:
        import os

        from core import paths

        folder = paths.data_dir(os.path.dirname(os.path.abspath(__file__)))
        os.makedirs(folder, exist_ok=True)
        probe = os.path.join(folder, ".selftest")
        with open(probe, "w") as f:
            f.write("ok")
        os.remove(probe)
        print(f"data folder: {folder}")
    except Exception as exc:
        problems.append(f"data folder: {exc}")
    if problems:
        print("selftest FAILED")
        for p in problems:
            print("  ", p)
        return 1
    print("selftest ok")
    return 0


def main() -> int:
    multiprocessing.freeze_support()  # needed in a frozen app before anything else
    if "--selftest" in sys.argv:
        return selftest()
    import gui

    gui.main()
    return 0


if __name__ == "__main__":
    sys.exit(main())
