from ai import client as ai_client
from capture import screen


def run_check(task: str, context: str, max_width: int = 1280) -> dict:
    """Capture the screen and ask the AI whether the user is on task."""
    screenshot_b64 = screen.grab_screenshot(max_width)
    return ai_client.analyze(task, screenshot_b64, context)
