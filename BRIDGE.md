# Browser bridge (Onitry ↔ Inkwell "Today" planner)

Onitry runs a small local HTTP bridge so the browser extension can plan your day
and drive monitoring:

- Starting a **focus block** in the browser starts Onitry monitoring on that task.
  The planner also sends context ("due tomorrow; also on today's list: …"), which
  is added to what the AI sees.
- The planner shows Onitry's live **on task / off task** verdict, and records the
  session's on-task percentage in its journal.
- Ending the focus block stops monitoring (configurable in the extension).

## Pairing

1. Run Onitry (`python gui.py` or the menu bar app).
2. Open **⚙ Configure**, then copy the **Browser planner pairing code** (e.g. `K7QM-29XD`).
3. In the extension: Today → ⚙ → Onitry → paste the code → **Test connection**.

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

The port is `47323` (override with `ONITRY_BRIDGE_PORT`). Tests: `python -m unittest tests.test_bridge`.
