# Progress log (newest first)

Rule: see `CLAUDE.md`. Add an entry for every change. Don't edit old entries except to add a correction note beneath.
Each entry: what, why, files, how verified, not verified, known issues, what's left.

---

## 2026-11-26: Mac app (`af55823`, `d2b9a0c`)

- **What:** a clickable `Onitry.app` (and `.dmg`) built by CI for Apple Silicon and Intel; icon; data folder that works inside a
  bundle; site and docs updated to lead with the download.
- **Files:** `onitry_app.py`, `core/paths.py` (+ `config.py`, `room/session.py` use it), `packaging/{make_icon.py,onitry.spec,build_mac.sh}`,
  `.github/workflows/build-mac.yml`, `native_host/host.py` (`installed_app`, opens the app), `tests/test_paths.py`,
  `tests/test_native_host.py`; site pages (`Docs.jsx`, `Home.jsx`, `FullFocus.jsx`, `About.jsx`, `Privacy.jsx`, `site.js`).
- **Verified:** 243 unit tests + `ruff` pass locally. CI run `45781596064` (both macOS jobs green): PyInstaller build, ad-hoc
  codesign, `Onitry --selftest`, app opened and still running after 8 s, ~53 MB `.dmg` artifact uploaded.
- **Not verified (needs a person on a Mac):** dragging the `.dmg` to Applications, the first-run approval flow, Set Key in the
  bundled app, granting Screen Recording to "Onitry", a real monitoring session, the Keychain prompt, the Timecheck
  "Launch Onitry" button opening the installed app.
- **Not done:** Apple notarization (needs a paid Developer account); no release tag pushed (so the site's Download button
  404s until `v1.0.0` or similar is tagged, which also requires the repo to be public).

## 2026-11-26: website rewrite and QA (`9b1d030` .. `109ec81`)

- Hash routes with real pages (`App.jsx`), Home/Full Focus/ClassWatch/Docs/About/Privacy/Terms rewritten by separate agents
  from `docs/WEBSITE_BRIEF.md`, each claim checked against code. A QA agent drove a real browser at 360/768/1280 px:
  zero console errors, no horizontal scroll, no banned wording; it fixed docs deep links (`#/docs/install`), a cost-arithmetic
  error, scroll behaviour, a shared footer, mobile wrapping, meta tags.
- **Not verified:** the site on the real domain; Privacy/Terms were not reviewed by a lawyer (they say so).
- Owner decisions still open: license, repo visibility, About-page story (marker in `About.jsx`), contact address.

## 2026-11-26: merge of `main` (`c065c7b`)

`main` and this branch had diverged from `acfa4c3`. Branch-only: bridge, native host, weekly review. Main-only: idle detection,
ClassWatch, CI, README, the two-product site. Merged with conflicts resolved in `gui.py` (kept the bridge controller and main's
`FullFocusApp`/idle wiring; the class was renamed from `OnitryApp`), `server/README.md`, and site routing. Verified: 236 tests,
`ruff` clean.

## 2026-11-26: Onitry is free, bring your own key (`9c3acea`)

- **Why:** owner decision: no license fee, no subscription, no accounts. The paid backend was never deployed.
- **What:** default edition `free`; `byok`/`managed` kept but unreachable without `ONITRY_ENABLE_LEGACY_EDITIONS=1`. Files:
  `core/edition.py` (new), `config.py`, `ai/client.py`, `gui.py`, docstring marks in `core/license.py`, `core/auth.py`,
  `server/README.md`, `tests/test_edition.py`, `tests/test_client_managed.py`.
- **Verified:** 125 tests pass (venv) after the change; the free flow never calls `license.verify` or `httpx` to an Onitry host
  (mocked to fail if called).
- **Not verified:** the GUI itself (no tkinter here): only `py_compile`.
- **Choice left open:** free users are locked to Haiku (preserves old byok behaviour); a model picker exists for `dev`.

## 2026-11-26: launch plan and repo hygiene (`9b1d030`, `837ffe8`)

`docs/LAUNCH.md` (route to launch, status, owner decisions). `website/node_modules` (1,399 files, macOS binaries) untracked.

## 2026-10-23: rename to Timecheck (`3881d11`)

The browser extension "Onitry Plan" became **Timecheck** (docs, docstrings, native host). Extension ID, host name
`com.onitry.host` and the bridge API are unchanged.

## 2026-10-22: bridge pause/resume (`3d32a12`)

`POST /v1/pause {minutes}` (0-240) and `/v1/resume`, used by the planner's Pause button and break blocks.

## 2026-10-12: weekly review and native launcher (`f2e062a`)

`/v1/review` and `ai/review.py` (`config.REVIEW_MODEL`), `native_host/` (`com.onitry.host`, `install.py`), `BRIDGE.md`.

## 2026-10-11: local browser bridge (`5fe76bd`)

`core/bridge.py`: stdlib HTTP server on 127.0.0.1:47323 with a pairing code; endpoints ping, status, task, stop; GUI starts it and
shows the code in Configure.

## Earlier (2026-07 to 2026-08, on `main`)

Core monitoring, adaptive intervals, typing challenge, session memory, pause button, idle detection (main), ClassWatch (main),
`byok`/`managed` paid designs and the `server/` backend (never deployed), keylogger code removed (2026-07-21).

## Open items

- Decide license + repo visibility; open the PR into `main`; tag a release; deploy the site (see `docs/LAUNCH.md`).
- Small product fixes from the audit (see ARCHITECTURE "Known issues"): Haiku for `cli.py`/chat, Keychain in `cli.py`,
  review model pricing, pairing-path text.
- Test the Mac app on a real Mac; notarize when the owner has a Developer account.
