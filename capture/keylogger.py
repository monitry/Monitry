import threading
import time
from collections import deque
from pynput import keyboard

# Each entry: (timestamp, key_string)
_log: deque = deque()
_lock = threading.Lock()
_listener = None


def _on_press(key):
    try:
        ch = key.char if hasattr(key, "char") and key.char else f"[{key.name}]"
    except AttributeError:
        ch = f"[{key}]"
    with _lock:
        _log.append((time.time(), ch))


def start():
    global _listener
    _listener = keyboard.Listener(on_press=_on_press)
    _listener.daemon = True
    _listener.start()


def stop():
    if _listener:
        _listener.stop()


def get_recent(window_seconds: int = 20) -> str:
    """Return keystrokes from the last `window_seconds` as a readable string."""
    cutoff = time.time() - window_seconds
    with _lock:
        recent = [ch for ts, ch in _log if ts >= cutoff]
        # Prune old entries
        while _log and _log[0][0] < cutoff - 60:
            _log.popleft()
    return "".join(recent)
