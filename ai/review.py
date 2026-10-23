"""Weekly review for the Timecheck browser extension.

The extension computes the week's numbers locally (tasks done per subject,
focus minutes, on-task %, distraction passes, journal lines) and posts them to
the bridge's /v1/review. This turns them into a short, honest coaching note.
Runs on the user's own API key, so the extension never needs one.
"""

from __future__ import annotations

import json

import anthropic

import config

REVIEW_SYSTEM = """You are the weekly-review coach inside Onitry, a focus app used by a busy high-school student \
(classes, robotics, Model UN, side projects). You get one week of their planner data as JSON: tasks finished and \
missed per subject, focus blocks with Onitry's on-task percentage, distracting sites they asked to unlock and why, \
their end-of-day ratings and journal lines, and next week's tests and deadlines.

Write a short review they will actually read on a Sunday night:
- Open with one sentence on how the week went, grounded in the numbers.
- "What worked": 2-3 bullets, each citing a concrete number or day.
- "What slipped": 2-3 bullets, naming the pattern (e.g. which site or time of day), not just the symptom.
- "Next week": 3 specific, schedulable actions tied to the upcoming deadlines in the data.

Be direct and warm, never preachy. Don't invent facts that aren't in the data; if the data is thin, say so in one \
line and keep the review short. Plain Markdown, under 220 words."""


class ReviewUnavailable(Exception):
    """Raised with a user-facing reason when no review can be written."""


def _client() -> anthropic.Anthropic:
    return anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)


def weekly_review(stats: dict) -> dict:
    """Return {"text": markdown, "model": served-by model id}. Raises ReviewUnavailable."""
    if config.MANAGED_MODE or not config.ANTHROPIC_API_KEY:
        raise ReviewUnavailable("The AI review needs an Anthropic API key in Onitry (dev or BYOK edition).")

    try:
        response = _client().beta.messages.create(
            model=config.REVIEW_MODEL,
            max_tokens=16000,
            output_config={"effort": "medium"},
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
            system=REVIEW_SYSTEM,
            messages=[
                {
                    "role": "user",
                    "content": "Here is my week:\n\n" + json.dumps(stats, ensure_ascii=False, indent=1),
                }
            ],
        )
    except anthropic.AuthenticationError as exc:
        raise ReviewUnavailable("Onitry's API key was rejected.") from exc
    except anthropic.RateLimitError as exc:
        raise ReviewUnavailable("Rate limited by the Anthropic API. Try again in a minute.") from exc
    except anthropic.APIStatusError as exc:
        raise ReviewUnavailable(f"Anthropic API error ({exc.status_code}).") from exc
    except anthropic.APIConnectionError as exc:
        raise ReviewUnavailable("Couldn't reach the Anthropic API.") from exc

    if response.stop_reason == "refusal":
        raise ReviewUnavailable("The model declined to write this review.")
    text = "".join(block.text for block in response.content if block.type == "text").strip()
    if not text:
        raise ReviewUnavailable("The review came back empty.")
    return {"text": text, "model": response.model}
