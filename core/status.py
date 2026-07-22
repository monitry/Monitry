import json
import os


def write(path: str, status: str, task: str = "", activity: str = "") -> None:
    """Write the current session status for the menu bar app to poll."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump({"status": status, "task": task, "activity": activity}, f)
