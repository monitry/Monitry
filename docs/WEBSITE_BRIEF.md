# Website brief: Onitry launch site

Audience: students and knowledge workers on a Mac who lose focus, and developers comfortable with a terminal (the first
users). Tone: plain, direct, a little dry. Short sentences. No hype words ("revolutionary", "supercharge"), no fake
urgency, no invented numbers or testimonials.

## The offer (decided)

**Onitry is free. You bring your own Anthropic API key.** No license fee, no subscription, no account, no Onitry server.
The only money involved is what you pay Anthropic for your own usage.

Two products share one site:
- **Full Focus**: watches your screen and interrupts you when you drift. This is the launch product.
- **ClassWatch**: points a camera at a room and logs each screen it sees. **Experimental.** Say so.

Companion (separate download, not part of this repo): the **Timecheck** Chrome extension, a planner with focus blocks, a
distraction gate and a journal. It talks to Onitry over a local bridge. Mention it briefly; don't oversell it.

## Rules for every page

1. **Every factual claim must be true in the code.** Read the code (this repo, merged branch) before you write a claim.
   If you can't verify it, leave it out. List what you verified, with file:line, in your final report.
2. **Nothing about prices, licenses, plans, tiers, "Pro", "Managed", "BYOK", daily caps, sign-in, or Stripe** anywhere on
   the site. Those designs are legacy and unreachable. The words "free" and "bring your own key" are the offer.
3. **Do not claim "open source"** (there is no LICENSE file yet). Say "free". You may say the code is on GitHub only
   via the constants in `website/src/site.js`.
4. **No personal email addresses.** Contact is GitHub Issues (`ISSUES_URL` in `site.js`).
5. **Be honest about installation:** there is a downloadable Mac app (built by CI, Apple Silicon and Intel), and it is
   not notarized, so macOS asks the user to approve it once. There is also a run-from-source route for people who prefer a
   terminal. Say both plainly.
6. **Be honest about cost and privacy** using the verified facts below. Never write "Anthropic never stores images".
7. Use `site.js` constants for any URL. Don't hardcode `github.com/...` or an email.
8. Hash routes: pages are `#/`, `#/fullfocus`, `#/classwatch`, `#/docs`, `#/about`, `#/privacy`, `#/terms`. Link with
   `href="#/docs"` (or call the `onNav("docs")` prop pages already receive).
9. Keep the existing visual language (dark theme, CSS variables in `src/index.css`, CSS modules). Don't add
   dependencies. Responsive down to 360px. Real headings in order, alt text, visible focus, sufficient contrast.
10. Only edit the files your task owns. `npm run build` in `website/` must pass when you finish.

## Verified facts (from an audit of the code)

**Platform and setup**
- macOS only: `alerts/notifier.py` uses `osascript` and `say`; `requirements.txt` includes `rumps` (menu bar).
- Python 3.11 is what CI uses; 3.10 is the floor (`X | None` annotations). Needs Tk (conda and python.org builds have it).
- Dependencies: `requirements.txt` (anthropic, httpx, keyring, rumps, mss, opencv-python, Pillow, numpy).
- Run: `python gui.py` (window) or `python menubar.py` (menu bar app, optional) or `python cli.py "task"` (terminal).
- API key: stored in the macOS Keychain (service `onitry`) through the app's Set Key row, or `ANTHROPIC_API_KEY` for
  `cli.py`. "No minimum macOS version" is known; do not write "macOS 13+".

**Permissions**
- Screen Recording for the app that runs Python (the terminal or Python itself). `capture/screen.py` uses `mss`.
- The hard-interrupt popup runs an AppleScript against System Events, which may trigger an Automation prompt (unverified:
  say "macOS may ask").
- Keychain prompts come from `keyring`. ClassWatch needs Camera permission.

**What is sent and stored**
- Each check sends one JPEG of the primary monitor, the task text, the last 10 log lines and the running notes to
  Anthropic with the user's key. With the Timecheck bridge, the planner's task context is added.
- Stored locally, in plain text, in `data/`: `context.txt` (descriptions of activity), `status.json`, `settings.json`
  (including recent task names), `bridge_token`. **No screenshot is ever written to disk.** No keylogging.
- Anthropic's own retention policy applies to what they receive. We don't control it. Link to their policy; don't
  paraphrase it.

**How checking works**
- First check about 5 s after start. Interval starts at 10 s, grows by 10 s per check up to 120 s while you are on task
  (with random jitter 0.4x to 1.6x), and snaps back to 10 s the moment you go off task.
- Idle detection: checks are skipped after 5 minutes of no mouse or keyboard (`core/idle.py`).
- A 10-minute Pause button exists. A grace period after a popup is configurable (0 to 300 s).
- The AI decides whether to interrupt. Hard interrupt: a topmost red popup, speech, and a typing challenge (one of ten
  fixed sentences of 14 to 18 words). It auto-dismisses after 90 s and has a "Not actually off task?" button that feeds a
  correction back. Soft: a silent notification banner.
- End of session summary: duration, percent on task, timeline, interrupt count, cost.

**Model and cost (free edition)**
- Haiku 4.5 (`claude-haiku-4-5-20251001`). The model picker exists only in the `dev` edition.
- Default screenshot width 1280 px, JPEG quality 75. (Verify in `gui.py` which of these the free edition exposes before
  documenting them as user settings.)
- Rough cost, an estimate (the app doesn't log token usage): **about $0.06 to $0.20 per hour on Haiku**, depending on how
  often you drift (a calm hour is about 36 checks, about $0.09; more drifting means more frequent checks). Show the
  arithmetic in the docs. Say it is an estimate and tell people to set a spending limit in the Anthropic console.

**Timecheck bridge** (`BRIDGE.md`): a local HTTP server on 127.0.0.1:47323, requires a pairing code (shown in
Configure), accepts only the extension's origin and checks the Host header. The extension can start and stop
monitoring, pause, and request a weekly review (uses the user's key; model from `config.REVIEW_MODEL`).

**ClassWatch** (`room_cli.py`, `room/`): CLI only. Camera plus `requirements-room.txt` (pulls in `ultralytics` and
torch); model weights download on first run. Detects screens with YOLO, tracks them, has Haiku describe each, writes a
Markdown report on Ctrl+C. Roughly $0.25 to $0.40 per screen-hour (estimate). Unit-tested with mocks only; no evidence of
accuracy on real classroom footage. It observes other people: say plainly that consent and local rules apply. Do not call
it production-ready.

## Things that were wrong on the old site (don't repeat)

- "Cancel anytime", prices, plan names, "Get Onitry" alert.
- "Can't be dismissed": it auto-dismisses after 90 s and can be flagged as a mistake.
- "~25-word sentence": they are 14 to 18 words.
- Resolution "cost ratios" (40%/16%/6%): only image tokens scale that way, not the total.
- `git clone https://github.com/yourname/onitry.git` (placeholder; use `site.js`).
- "No browser extension" and "runs in your menu bar": the menu bar app is optional and the Timecheck extension exists.
- Roadmap listing idle detection as planned (it's built) or "activity breakdown" in session reports (it's not).
- Personal email on the About page.

## Acceptance (for the QA agent)

Builds; every link resolves; no price or plan words; no "open source"; no personal email; no placeholder URL; reads well
at 360, 768 and 1280 px; keyboard focus visible; headings in order; each claim traceable to the facts above or the code.
