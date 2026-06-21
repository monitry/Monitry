import json
import anthropic
import config

_client = None


def _get_client():
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
    return _client


SYSTEM_PROMPT = """You are a productivity monitor. Given a screenshot of the user's screen, recent keystrokes,
an activity log, and the task they want to accomplish, determine if they are on task.

Respond ONLY with a JSON object (no markdown, no extra text):
{
  "onTask": true or false,
  "activity": "brief description of what they appear to be doing right now",
  "reminder": "if off-task, a short firm reminder of what they should be doing instead"
}

Be realistic — browsing documentation, writing code, or reading relevant material counts as on-task.
Social media, YouTube, games, or unrelated browsing is off-task."""


def analyze(task: str, screenshot_b64: str, keylog: str, context: str) -> dict:
    """Send screenshot + context to Claude and return parsed JSON response."""
    user_text = f"""Task the user wants to complete: {task}

    Recent keystrokes (last 20s): {keylog or "(none)"}

    Activity log so far:
{context or "(empty — just started)"}

Analyze the screenshot and determine if the user is on task."""

    message = _get_client().messages.create(
        model=config.MODEL,
        max_tokens=256,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/jpeg",
                            "data": screenshot_b64,
                        },
                    },
                    {"type": "text", "text": user_text},
                ],
            }
        ],
    )

    raw = message.content[0].text.strip()
    # Strip markdown code fences if Claude wraps it anyway
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw)
