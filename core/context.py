import datetime
import os


def init_log(path: str, task: str) -> None:
    """Create/overwrite the session log with a header line for a new session."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(path, "w") as f:
        f.write(f"Session started: {ts}\nTask: {task}\n\n")


def append(path: str, activity: str) -> None:
    """Append a timestamped activity line to the session log."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    ts = datetime.datetime.now().strftime("%H:%M:%S")
    with open(path, "a") as f:
        f.write(f"[{ts}] {activity}\n")


def read_tail(path: str, max_lines: int = 10) -> str:
    """Return the last ``max_lines`` non-empty lines of the session log."""
    if not os.path.exists(path):
        return ""
    with open(path) as f:
        lines = [line.rstrip() for line in f if line.strip()]
    return "\n".join(lines[-max_lines:])
