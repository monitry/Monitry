import json
import time

import anthropic

import config

_client = None
notes = None

# $ per 1M tokens: (input, output)
PRICING = {
    "claude-haiku-4-5-20251001": (1.00, 5.00),
    "claude-sonnet-4-6": (3.00, 15.00),
    "claude-opus-4-8": (5.00, 25.00),
}

_session_cost = 0.0
_session_checks = 0

# Errors worth a short retry — transient network/server issues, not bad requests.
_RETRYABLE_ERRORS = (
    anthropic.APIConnectionError,
    anthropic.APITimeoutError,
    anthropic.RateLimitError,
    anthropic.InternalServerError,
    anthropic.OverloadedError,
)


def _get_client():
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
    return _client


def reset_session() -> None:
    """Clear running notes and cost — call at the start of a new monitoring session."""
    global notes, _session_cost, _session_checks
    notes = None
    _session_cost = 0.0
    _session_checks = 0


def session_cost() -> float:
    """Total $ spent on analyze() calls since the last reset_session()."""
    return _session_cost


def _create_with_retry(retries: int = 2, backoff: float = 1.5, **kwargs):
    for attempt in range(retries + 1):
        try:
            return _get_client().messages.create(**kwargs)
        except _RETRYABLE_ERRORS:
            if attempt == retries:
                raise
            time.sleep(backoff * (attempt + 1))


SYSTEM_PROMPT = """You are a productivity monitor. Given a screenshot of the user's screen,
an activity log, and the task they want to accomplish, determine if they are on task.

Respond ONLY with a JSON object (no markdown, no extra text):
{
  "onTask": true or false,
  "interrupt": true or false (whether you want the reminder to interrupt the tab or be a softer notification),
  "activity": "brief description of what they appear to be doing right now",
  "reminder": "if off-task, a short firm reminder of what they should be doing instead or a gentle notice if they are taking a while to do something",
  "notes": "you will be given notes from previous calls, modify it if necessary however keep it short and don't add if you don't need to"
}

Be realistic — browsing documentation, writing code, or reading relevant material counts as on-task.
Social media, YouTube, games, or unrelated browsing is off-task."""


def analyze(task: str, screenshot_b64: str, context: str) -> dict:
    """Send screenshot + context to Claude and return parsed JSON response."""
    global notes

    user_text = f"""Task the user wants to complete: {task}

    Activity log so far:
    {context or "(empty — just started)"}

    notes:
    {notes or "no notes have been given so far"}

Analyze the screenshot and determine if the user is on task."""

    message = _create_with_retry(
        model=config.MODEL,
        max_tokens=config.MAX_TOKENS_PER_RESPONSE,
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

    global _session_cost, _session_checks
    in_price, out_price = PRICING.get(config.MODEL, (0.0, 0.0))
    _session_cost += (message.usage.input_tokens / 1_000_000) * in_price
    _session_cost += (message.usage.output_tokens / 1_000_000) * out_price
    _session_checks += 1

    raw = message.content[0].text.strip()
    # Strip markdown code fences if Claude wraps it anyway
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    json_raw = json.loads(raw)
    notes = json_raw.get("notes", notes)
    return json_raw
