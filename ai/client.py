import json
import time

import anthropic
import httpx

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


class DailyLimitReached(Exception):
    """LEGACY managed edition only (not offered) — the server rejected the check because
    today's cap is used up. Never raised in the free edition."""

# Errors worth a short retry — transient network/server issues, not bad requests.
_RETRYABLE_ERRORS = (
    anthropic.APIConnectionError,
    anthropic.APITimeoutError,
    anthropic.RateLimitError,
    anthropic.InternalServerError,
    anthropic.OverloadedError,
)

# Managed mode's equivalent: connection-level failures only (timeout, connection
# refused, DNS) — not httpx.HTTPStatusError, since that also covers 401/402/429
# responses from our own server that must propagate immediately, not be retried.
_MANAGED_RETRYABLE_ERRORS = (httpx.TransportError,)


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


def _post_managed_with_retry(url: str, json_body: dict, timeout: float, retries: int = 2, backoff: float = 1.5):
    for attempt in range(retries + 1):
        try:
            return httpx.post(url, json=json_body, timeout=timeout)
        except _MANAGED_RETRYABLE_ERRORS:
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


def analyze(task: str, screenshot_b64: str, context: str, elapsed_seconds: float = 0.0) -> dict:
    """Send screenshot + context to Claude with the user's own key and return the parsed
    JSON response. The free edition only ever talks to Anthropic.

    The legacy managed proxy (server/) is reachable only when
    config.LEGACY_EDITIONS_ENABLED is on; `elapsed_seconds` is used only on that path."""
    if config.LEGACY_EDITIONS_ENABLED and config.MANAGED_MODE and config.MANAGED_TOKEN:
        return _analyze_managed(task, screenshot_b64, context, elapsed_seconds)
    return _analyze_direct(task, screenshot_b64, context)


def _analyze_direct(task: str, screenshot_b64: str, context: str) -> dict:
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
    # Strip markdown code fences if Claude wraps it anyway. Trim the leading/trailing
    # fence directly rather than splitting on every "```" in the text — the JSON
    # payload itself can legitimately contain that sequence (e.g. an "activity"
    # description quoting code on screen), and a naive split would truncate on it.
    if raw.startswith("```"):
        raw = raw.removeprefix("```json").removeprefix("```").strip()
        if raw.endswith("```"):
            raw = raw.removesuffix("```").strip()
    json_raw = json.loads(raw)
    notes = json_raw.get("notes", notes)
    return json_raw


def _analyze_managed(task: str, screenshot_b64: str, context: str, elapsed_seconds: float) -> dict:
    """LEGACY (not offered). Same contract as _analyze_direct, but via server/ so no Anthropic key is needed.
    Model is never sent — the server always uses Haiku for managed requests regardless."""
    global notes, _session_cost, _session_checks

    resp = _post_managed_with_retry(
        f"{config.MANAGED_API_URL}/v1/analyze",
        {
            "token": config.MANAGED_TOKEN,
            "task": task,
            "screenshot_b64": screenshot_b64,
            "context": context,
            "notes": notes or "",
            "elapsed_seconds": elapsed_seconds,
        },
        timeout=30.0,
    )
    if resp.status_code == 429:
        raise DailyLimitReached(resp.json().get("detail", "Daily limit reached."))
    resp.raise_for_status()
    json_raw = resp.json()

    _session_cost += json_raw.get("cost", 0.0)
    _session_checks += 1
    config.MANAGED_DAILY_REMAINING_SECONDS = json_raw.get(
        "daily_remaining_seconds", config.MANAGED_DAILY_REMAINING_SECONDS
    )
    notes = json_raw.get("notes", notes)
    return json_raw
