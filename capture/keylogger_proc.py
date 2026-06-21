"""
Subprocess-based keyboard logger for GUI mode.

pynput's keyboard.Listener crashes when tkinter's AppKit event loop owns the
main dispatch queue (TSMGetInputSourceProperty asserts main queue). Running
pynput in a child process gives it a clean main queue with no conflict.

Same public API as keylogger.py: start() / stop() / get_recent().
"""
import multiprocessing
import threading
import time
import queue as _queue_mod
from collections import deque

_proc: "multiprocessing.Process | None" = None
_mp_queue: "multiprocessing.Queue | None" = None
_log: deque = deque()
_lock = threading.Lock()
_drain_thread: "threading.Thread | None" = None


def _worker(q):
    """Runs in the child process — pynput gets its own AppKit main queue."""
    import time as _t
    from pynput import keyboard

    def on_press(key):
        try:
            ch = key.char if hasattr(key, "char") and key.char else f"[{key.name}]"
        except AttributeError:
            ch = f"[{key}]"
        q.put((_t.time(), ch))

    with keyboard.Listener(on_press=on_press) as listener:
        listener.join()


def _drain(q):
    while True:
        try:
            item = q.get(timeout=0.5)
            if item is None:
                break
            with _lock:
                _log.append(item)
        except _queue_mod.Empty:
            continue
        except Exception:
            break


def start():
    global _proc, _mp_queue, _drain_thread
    _mp_queue = multiprocessing.Queue()
    _proc = multiprocessing.Process(target=_worker, args=(_mp_queue,), daemon=True)
    _proc.start()
    _drain_thread = threading.Thread(target=_drain, args=(_mp_queue,), daemon=True)
    _drain_thread.start()


def stop():
    global _proc, _mp_queue
    if _proc and _proc.is_alive():
        _proc.terminate()
        _proc.join(timeout=2)
    if _mp_queue:
        try:
            _mp_queue.put(None)
        except Exception:
            pass
    _proc = None
    _mp_queue = None


def get_recent(window_seconds: int = 20) -> str:
    cutoff = time.time() - window_seconds
    with _lock:
        recent = [ch for ts, ch in _log if ts >= cutoff]
        while _log and _log[0][0] < cutoff - 60:
            _log.popleft()
    return "".join(recent)
