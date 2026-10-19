# Onitry

Two AI-powered focus-monitoring products, one codebase, one site
(`website/`), built on shared `core/` logic:

- **Full Focus** — watches your own screen (`gui.py`/`menubar.py`/`cli.py`).
  Interrupts you with popups when you drift off task.
- **ClassWatch** — points a camera at a room instead (`room_cli.py`). A
  passive observer with no popups — finds every laptop/monitor in view and
  builds a per-screen activity log.

This README mostly covers **Full Focus**, since it's the app with editions,
a backend, and most of the setup steps. ClassWatch's setup/usage is documented
on the ClassWatch section of `website/` and in `room_cli.py`'s own `--help`.

## Three product editions, one codebase (Full Focus)

`config.EDITION` (env var `ONITRY_EDITION`, default `dev`) picks which:

| Edition   | Model    | Own API key? | Cost                              |
| --------- | -------- | ------------- | ---------------------------------- |
| `dev`     | any      | yes           | whatever you use — unrestricted, for development/testing |
| `byok`    | Haiku only | yes (+ a one-time $30 license) | your own Anthropic usage |
| `managed` | Haiku only | no — Google sign-in | free (1hr/day) or $19/mo (10hr/day) |

```bash
ONITRY_EDITION=byok conda run -n opencv-env python gui.py
```

See `server/README.md` for the licensing/subscription backend (Stripe +
Google OAuth) behind `byok`/`managed`.

## Entry points

```bash
conda run -n opencv-env python menubar.py     # menu bar app (spawns gui.py)
conda run -n opencv-env python gui.py         # tkinter GUI standalone
conda run -n opencv-env python cli.py "task"  # terminal only, no GUI
```

ClassWatch's entry point (`room_cli.py`) needs the heavier
`requirements-room.txt` (pulls in `ultralytics`/torch for screen detection).

## Project layout

- `gui.py` / `menubar.py` / `cli.py` — **Full Focus**, the personal desktop
  app (watches your own screen via `mss`), in its three flavors
- `room_cli.py` + `room/` — **ClassWatch**, the camera-based room monitor:
  finds every laptop/monitor in a camera's view, tracks each one's identity
  across photos, and builds a per-screen activity log. Passive observer — no
  popups/TTS, unlike Full Focus.
- `core/` — logic shared across entry points: adaptive check interval,
  session-log I/O, persisted settings, Google OAuth, BYOK license check
- `ai/client.py` — talks to Claude directly (dev/byok editions)
- `capture/screen.py` — `mss`-based screenshot capture for Full Focus
- `alerts/notifier.py` — macOS notification/TTS
- `server/` — FastAPI backend for Full Focus's `managed`/`byok` editions
  (Stripe billing, Google sign-in, usage-cap enforcement) — see
  `server/README.md`. ClassWatch doesn't use this backend.
- `website/` — Vite + React marketing site for Onitry, covering both products
- `tests/` — stdlib `unittest`, no real network/API calls (everything mocked)

## Development

```bash
pip install -r requirements.txt          # base app (Full Focus)
pip install -r requirements-room.txt     # + ClassWatch (adds ultralytics/torch)
pip install -r requirements-dev.txt      # + ruff/pytest for local dev

python -m unittest discover -s tests
ruff check .
```

macOS only (relies on `osascript`/`say` for alerts, and `mss` for
screen capture in the personal-app editions).
