# Browser bridge (Onitry ↔ Timecheck extension)

Onitry runs a small local HTTP bridge so the browser extension can plan your day
and drive monitoring:

- Starting a **focus block** in the browser starts Onitry monitoring on that task.
  The planner also sends context ("due tomorrow; also on today's list: …"), which
  is added to what the AI sees.
- The planner shows Onitry's live **on task / off task** verdict, and records the
  session's on-task percentage in its journal.
- Ending the focus block stops monitoring (configurable in the extension).
- If Onitry reports **off task** during a focus block, the extension revokes any
  site passes and locks its distraction gate for 10 minutes.
- **Weekly review:** the extension sends the week's stats to `/v1/review`, and
  Onitry writes a short review with Claude (`ai/review.py`, `config.REVIEW_MODEL`)
  on its own API key. The extension never holds a key. This needs an Anthropic
  API key set in Onitry (the free edition's normal setup).
- **Launch Onitry:** a native-messaging host lets the extension start Onitry when
  it isn't running (see below).

## Pairing

1. Run Onitry (`python gui.py` or the menu bar app).
2. Open **⚙ Configure**, then copy the **Browser planner pairing code** (e.g. `K7QM-29XD`).
3. In the extension: ⚙ → Onitry → paste the code → **Test connection**.

The code is stored in `data/bridge_token` (gitignored). Delete that file to make a new one.

## Security

`core/bridge.py` binds to `127.0.0.1` only. Every endpoint except `/v1/ping` needs
the pairing code in an `X-Onitry-Token` header. It's a custom header, so a web page
can't send it without a CORS preflight, and preflights are only answered for
`chrome-extension://` origins. It also rejects any non-extension `Origin`, and any
`Host` other than `127.0.0.1` / `localhost`, which blocks DNS rebinding.

## API

| Method | Path | Body | Notes |
| --- | --- | --- | --- |
| GET | `/v1/ping` | – | No code needed. `{app: "onitry", paired}` |
| GET | `/v1/status` | – | `running, status (on_task/off_task/idle), task, activity, on_task_seconds, off_task_seconds, interrupts, paused, last_error` |
| POST | `/v1/task` | `{task, details?}` | Starts monitoring the task. If a different task is running, it stops that one first, without showing its summary popup. |
| POST | `/v1/stop` | `{}` | Stops monitoring. |
| POST | `/v1/pause` | `{minutes}` | Pauses monitoring (0–240 min, resumes by itself). The planner's Pause button and break blocks use this. |
| POST | `/v1/resume` | `{}` | Ends a pause early. |
| POST | `/v1/review` | `{stats}` | Weekly review: `{text, model}`, or `503 {error}` when there's no API key or the call fails. Body limit 64 KB. |

The port is `47323` (override with `ONITRY_BRIDGE_PORT`). Tests: `python -m unittest tests.test_bridge`.

## Launching Onitry from the browser

```bash
python native_host/install.py            # use the same Python you run Onitry with
python native_host/install.py --uninstall
```

This registers `com.onitry.host` with Chrome, Chromium, Brave, Edge and Arc (on
Windows it goes in the registry). Only the Timecheck extension
(`chrome-extension://dadagbofodnllhcohbhmjkdolklihcgn/`, fixed by the `key` in its
manifest) can call it. It accepts two commands: `ping`, and `launch`, which starts
`gui.py` detached unless the bridge is already listening. Tests:
`python -m unittest tests.test_native_host`.
