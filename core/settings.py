import json
import os

DEFAULTS = {
    "jpeg_quality": 75,
}


def load(path: str) -> dict:
    """Load persisted settings, filling in defaults for anything missing/unreadable."""
    settings = dict(DEFAULTS)
    if os.path.exists(path):
        try:
            with open(path) as f:
                settings.update(json.load(f))
        except (OSError, json.JSONDecodeError):
            pass
    return settings


def save(path: str, settings: dict) -> None:
    """Merge ``settings`` into whatever is already on disk and write it back.

    Callers only need to pass the keys they're updating — this avoids one
    caller's save() clobbering keys another part of the app owns.
    """
    merged = load(path)
    merged.update(settings)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(merged, f)
