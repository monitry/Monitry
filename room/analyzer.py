"""Per-screen activity analysis for the room monitor.

Mirrors ai/client.py's retry/cost-tracking pattern, but keyed per screen_id
instead of a single global — each tracked physical screen gets its own
running "notes" context, since they're independent activity streams (this
is a passive observer watching several unrelated screens, not one person's
single session).

Unlike the personal app, there's no interrupt/popup/TTS here — this module
only ever produces a log entry. If no task is given for a screen, it just
describes what's on it (onTask stays None) rather than forcing a judgment
nobody asked for.
"""
import json
import time

import anthropic

import config

_client = None
_notes: dict[str, str] = {}
_session_cost = 0.0
_session_checks = 0

# $ per 1M tokens: (input, output) — kept in sync with ai/client.py's PRICING
PRICING = {
    "claude-haiku-4-5-20251001": (1.00, 5.00),
    "claude-sonnet-4-6": (3.00, 15.00),
    "claude-opus-4-8": (5.00, 25.00),
}

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
    global _notes, _session_cost, _session_checks
    _notes = {}
    _session_cost = 0.0
    _session_checks = 0


def forget_screen(screen_id: str) -> None:
    """Drop a single screen's notes — call when its track is evicted (screen
    left view for good) so a later, unrelated screen never inherits stale context."""
    _notes.pop(screen_id, None)


def session_cost() -> float:
    return _session_cost


def _create_with_retry(retries: int = 2, backoff: float = 1.5, **kwargs):
    for attempt in range(retries + 1):
        try:
            return _get_client().messages.create(**kwargs)
        except _RETRYABLE_ERRORS:
            if attempt == retries:
                raise
            time.sleep(backoff * (attempt + 1))


SYSTEM_PROMPT = """You are observing a physical screen (laptop or monitor) captured by a room
camera, as one of possibly several screens being watched at once. You are given a cropped
photo of just that one screen.

Respond ONLY with a JSON object (no markdown, no extra text):
{
  "activity": "brief description of what's visibly on the screen right now",
  "onTask": true, false, or null — null if no task was specified for this screen, otherwise
            whether the visible activity matches the stated task,
  "notes": "short running notes about this screen across checks, carried forward each time — modify if useful, keep brief, leave close to unchanged if nothing new"
}

The photo may be low quality, off-angle, or partially obscured (camera glare, hands, an
open textbook). Describe your best read of it rather than refusing — say "screen unclear"
as the activity only if genuinely nothing is legible."""


def analyze_screen(screen_id: str, image_b64: str, context: str = "", task: str = "") -> dict:
    """Analyze one tracked screen's current image. `context` is that screen's
    own recent activity log tail (not shared across screens)."""
    notes = _notes.get(screen_id)

    user_text = f"""Task assigned to this screen: {task or "(none specified — just describe activity, don't judge on/off-task)"}

Recent activity log for this screen:
{context or "(empty — just started watching this screen)"}

notes:
{notes or "no notes yet"}

Analyze the photo of this screen."""

    message = _create_with_retry(
        model=config.HAIKU_MODEL,
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
                            "data": image_b64,
                        },
                    },
                    {"type": "text", "text": user_text},
                ],
            }
        ],
    )

    global _session_cost, _session_checks
    in_price, out_price = PRICING.get(config.HAIKU_MODEL, (0.0, 0.0))
    _session_cost += (message.usage.input_tokens / 1_000_000) * in_price
    _session_cost += (message.usage.output_tokens / 1_000_000) * out_price
    _session_checks += 1

    raw = message.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.removeprefix("```json").removeprefix("```").strip()
        if raw.endswith("```"):
            raw = raw.removesuffix("```").strip()
    parsed = json.loads(raw)
    _notes[screen_id] = parsed.get("notes", notes)
    return parsed
