from ai import client as ai_client
from capture import screen


def run_check(task: str, context: str, max_width: int = 1280, quality: int = 75) -> dict:
    """Capture the screen and ask the AI whether the user is on task."""
    screenshot_b64 = screen.grab_screenshot(max_width, quality)
    return ai_client.analyze(task, screenshot_b64, context)


def reset_session() -> None:
    """Clear running notes and cost — call at the start of a new monitoring session."""
    ai_client.reset_session()


def session_cost() -> float:
    """Total $ spent on checks since the last reset_session()."""
    return ai_client.session_cost()
