"""macOS idle-time detection — skip monitoring checks (and their API cost)
while the user is away from the keyboard/mouse.

Uses `ioreg`, which ships with every macOS install — no pyobjc/Quartz
dependency needed for something this small.
"""
import re
import subprocess

_IDLE_RE = re.compile(rb'"HIDIdleTime"\s*=\s*(\d+)')


def get_idle_seconds() -> float:
    """Seconds since the last mouse/keyboard event.

    Fails open (returns 0.0, i.e. "not idle") on anything unexpected — not
    macOS, `ioreg` missing, unparseable output — so idle detection can never
    itself cause monitoring to silently stop; worst case it just never
    activates.
    """
    try:
        output = subprocess.run(
            ["ioreg", "-c", "IOHIDSystem"],
            capture_output=True, timeout=5, check=True,
        ).stdout
    except (subprocess.SubprocessError, OSError):
        return 0.0

    match = _IDLE_RE.search(output)
    if not match:
        return 0.0
    return int(match.group(1)) / 1_000_000_000  # HIDIdleTime is nanoseconds
