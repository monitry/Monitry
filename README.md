# Onitry

Two AI-powered focus-monitoring products, one codebase, one site
(`website/`), built on shared `core/` logic:

- **Full Focus** — watches your own screen (`gui.py`/`menubar.py`/`cli.py`).
  Interrupts you with popups when you drift off task.
- **ClassWatch** — points a camera at a room instead (`room_cli.py`). A
  passive observer with no popups — finds every laptop/monitor in view and
  builds a per-screen activity log.

This README mostly covers **Full Focus**, the app with most of the setup steps. ClassWatch's setup/usage is documented
on the ClassWatch section of `website/` and in `room_cli.py`'s own `--help`.

## Free, bring your own key

Onitry is free. You bring your own Anthropic API key (saved in the macOS Keychain, or set `ANTHROPIC_API_KEY`).
There is no license, subscription or account, and Onitry never contacts an Onitry server: only Anthropic is called,
using your key. Set a monthly spending limit in the Anthropic console.

`config.EDITION` (env var `ONITRY_EDITION`) picks the mode:

| Edition | Model | Key | Status |
| --- | --- | --- | --- |
| `free` (default) | Haiku 4.5 | your own | the product |
| `dev` | any | your own | everything unlocked, for development and testing |
| `byok`, `managed` | n/a | n/a | legacy paid designs, not offered; ignored unless `ONITRY_ENABLE_LEGACY_EDITIONS=1` (see `server/README.md`) |

```bash
python gui.py
```

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
  session-log I/O, persisted settings; `auth.py`/`license.py` are legacy and unused by the free edition
- `ai/client.py` — talks to Claude directly with your key
- `capture/screen.py` — `mss`-based screenshot capture for Full Focus
- `alerts/notifier.py` — macOS notification/TTS
- `server/` — LEGACY, not used by the free edition: the FastAPI backend of the old paid `managed`/`byok` designs
  (Stripe, Google sign-in, usage caps). Never deployed; see `server/README.md`.
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
