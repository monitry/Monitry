# Architecture (current truth)

Keep this file in step with the code. See `CLAUDE.md` for the rule. Last full review: 2026-11-26.

Product: **Onitry**, a macOS app that watches your screen with Claude and interrupts you when you drift. Free; the user
brings an Anthropic API key. Two products share the code: **Full Focus** (screen) and **ClassWatch** (camera, experimental).
GitHub repo: `monitry/Monitry`. Work branch: `claude/bold-davinci-spz652` (contains `main` merged in; no PR opened).

## Entry points

| File | What |
| --- | --- |
| `onitry_app.py` | The packaged app's entry. Opens the Full Focus window. `--selftest` imports everything and exits 0 (used by CI) |
| `gui.py` | Full Focus window (tkinter). `FullFocusApp`, `main()`. Also the bridge controller (`_BrowserBridgeController`) |
| `menubar.py` | Optional menu bar app (rumps). Spawns `gui.py` with `subprocess` using `sys.executable`. Not in the packaged app |
| `cli.py` | Terminal version. Reads `ANTHROPIC_API_KEY` from the environment only (not the Keychain). Uses `config.MODEL` (Sonnet) |
| `room_cli.py` + `room/` | ClassWatch. Needs `requirements-room.txt` (ultralytics, torch) and a camera |

## Configuration and files

- `config.py`: constants and edition. `DATA_DIR = core/paths.data_dir(...)`; `CONTEXT_FILE`, `STATUS_FILE`, `SETTINGS_FILE`,
  `BRIDGE_TOKEN_FILE` are in it. `MODEL` (Sonnet 4.6, used by `cli.py` and the menu bar "Ask Claude"), `HAIKU_MODEL`
  (`claude-haiku-4-5-20251001`, the free edition), `REVIEW_MODEL` (`claude-opus-5-5`, weekly review; no entry in the cost
  table), `BRIDGE_PORT` 47323.
- `core/paths.py`: **data folder rule.** `ONITRY_DATA_DIR` if set; else `~/Library/Application Support/Onitry` when
  `sys.frozen` (packaged app); else `<repo>/data`. `room/session.py` uses `<data>/room`.
- Files in the data folder (plain text, unencrypted): `context.txt` (activity lines, overwritten per session), `status.json`,
  `settings.json` (settings and last 8 task titles), `bridge_token`, `native_launch.log`, `room/*`. API key: macOS Keychain,
  service `onitry`, account `anthropic_api_key` (via `keyring`). **No screenshot is ever written to disk.**

## Editions (`core/edition.py`, `config.EDITION`)

`free` (default): user's key, Haiku, no license, no account, no Onitry server. `dev`: everything unlocked (model picker).
`byok` and `managed`: LEGACY paid designs, resolve to `free` unless `ONITRY_ENABLE_LEGACY_EDITIONS=1`. `edition.start_error()`
is the start check and makes no network call. `import config` must not import `core.license` or `core.auth`
(`tests/test_edition.py` checks). `ai/client.py`'s managed-proxy path is gated by the same flag.

## The monitoring loop (`gui.py`, `core/`)

- First check ~5 s after start. `core/interval.py` `AdaptiveInterval`: base 10 s (`MIN_INTERVAL`), +10 s per check up to 120 s
  (`MAX_INTERVAL`), wait = base x U(0.4, 1.6), floor 10 s minus API time; off-task snaps base to 10 s.
- `core/idle.py`: reads `ioreg` idle time; checks are skipped after 300 s (`IDLE_THRESHOLD_SECONDS`); fails open.
- Pause button: `PAUSE_MINUTES` = 10. Grace period after a popup: setting, 0-300 s, default 60.
- `core/check.py` `run_check` takes the screenshot (`capture/screen.py`, primary monitor only, `mss`, JPEG, default width 1280,
  quality 75), calls `ai/client.py` `analyze` with task + last 10 log lines (`core/context.py`) + running notes, returns
  status/activity/reminder/interrupt. Session cost is computed in memory from the `PRICING` table (token counts are not logged).
- Interrupts: the AI sets `interrupt`; a hard popup is topmost, speaks via `say`, and needs a typing challenge (one of ten fixed
  sentences, 14-18 words, `gui.py` ~l.100); it auto-dismisses after 90 s and has a "Not actually off task?" flag button that
  appends a correction to the log. Soft: a silent `osascript` notification (`alerts/notifier.py`).
- The popup also runs AppleScript against System Events (may trigger an Automation prompt; unverified).

## Browser bridge (`core/bridge.py`, `BRIDGE.md`)

Stdlib HTTP server on `127.0.0.1:47323`, started whenever the GUI opens (`gui.py _start_bridge`). Header `X-Onitry-Token` carries a
pairing code (`data/bridge_token`, shown in Configure). Only `chrome-extension://` origins get CORS preflights; other
`Origin`/`Host` values are rejected. Endpoints: `/v1/ping`, `status`, `task`, `stop`, `pause` (0-240 min), `resume`,
`review` (weekly review via `ai/review.py`, uses the user's key). The Timecheck extension (repo `Craig47313/ChromeExtensionTest`)
is the client. `native_host/` (`host.py`, `install.py`): Chrome native-messaging host `com.onitry.host` so the extension can
launch Onitry; `launch_gui` opens `/Applications/Onitry.app` (or `~/Applications`) with `open` if installed, else runs
`gui.py`. Locked to Timecheck's fixed extension ID `dadagbofodnllhcohbhmjkdolklihcgn`.

## Mac app (`packaging/`, `.github/workflows/build-mac.yml`)

PyInstaller (`packaging/onitry.spec`), windowed, `Onitry.app`, bundle id `app.onitry.focus`, icon generated by
`packaging/make_icon.py` (Pillow, writes `.icns`; generated files are git-ignored). Excludes rumps/ultralytics/torch.
`packaging/build_mac.sh`: icon, build, ad-hoc `codesign --sign -`, `Onitry --selftest`, `.dmg` with an Applications link.
Workflow: matrix `macos-latest` (Apple Silicon) and `macos-15-intel`; runs on pushes to `claude/**`/`main` that touch
packaging, `onitry_app.py`, `requirements.txt`, or the workflow; tags `v*` also create a GitHub Release with the `.dmg`s;
always uploads an artifact. **Not notarized**: macOS asks for approval on first open (Control-click, Open; macOS 15+: Settings,
Privacy & Security, Open Anyway). Notarization needs an Apple Developer account (not set up).
`ci.yml` (tests on macOS) runs on pushes to `main` and pull requests.

## Website (`website/`)

Vite + React, CSS modules, no router library. **Hash routes**: `#/`, `#/fullfocus`, `#/classwatch`, `#/docs[/<section>]`,
`#/about`, `#/privacy`, `#/terms` (`src/App.jsx`; docs sections scroll to `id="sec-<section>"`). Pages call
`onNav("docs")`, which sets the hash. `src/site.js` holds URLs and constants (`REPO_URL`, `ISSUES_URL`, `DOWNLOAD_URL`,
`CLONE_URL`, `APP_DATA_FOLDER`, `LAST_UPDATED`); change URLs only there. Copy rules: `docs/WEBSITE_BRIEF.md`.
Build quirk: committed history had macOS-only `node_modules`; it is now untracked. On Linux run
`npm install --no-save @rollup/rollup-linux-x64-gnu` once, then `npx vite build`. Use `--outDir /tmp/x` to avoid touching the
tracked `website/dist`. Hosting: the `website-deploy` branch holds static build output for Porkbun.

## Legacy (not used by the free edition)

`server/` (FastAPI, Stripe, Google OAuth, SQLite; never deployed), `core/license.py`, `core/auth.py`, managed paths in
`ai/client.py` and `gui.py`. Kept so the paid design can be revived or deleted later.

## Testing

- `python -m unittest discover -s tests` (243 at last run). Needs: anthropic, httpx, keyring, fastapi, stripe, pydantic,
  google-auth, uvicorn, numpy, pillow, opencv-python-headless, mss. Bare system Python lacks them; make a venv.
- `ruff check .` must pass (CI lints).
- Cannot be tested on Linux: the GUI (no tkinter), macOS permissions, the packaged app's behaviour (CI covers build, selftest
  and "stays running for 8 s"), a real monitoring session (needs a real key and screen).

## Known issues and traps (from the 2026-11-26 audit)

- `cli.py` and the menu bar chat use Sonnet (about 3x Haiku cost); `cli.py` ignores the Keychain and prints "every 10s" though it
  ramps; `room_cli.py` demands the API key even for `--help`.
- GUI text says pairing is under "Today -> Settings -> Onitry" while `BRIDGE.md` says the extension's settings, Onitry section.
- `REVIEW_MODEL` has no price in `PRICING`, so review cost is not in the session cost.
- `CONTEXT_MAX_CHARS` (config) is unused; `CHECK_INTERVAL` only affects `cli.py`.
- Git history contains two personal commit emails and an early real activity log (removed later, still in history).
- No LICENSE file. `ultralytics` (ClassWatch) is AGPL-3.0.
- Menu bar idle icon is the letter "M" (leftover from the old name).
