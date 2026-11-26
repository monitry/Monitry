# Instructions for Claude and other agents working in this repo

## Documentation rule (permanent)

**Every change that adds, changes or removes behaviour must update the agent documentation in `docs/` in the same
session, before you finish.** Write it for the next agent, not for an end user: what has been done, and the specifics of
how things work. (End-user text lives in `README.md` and the website under `website/`; don't confuse the two.)

What to update, and how:

1. **`docs/PROGRESS.md`**: add a dated entry at the top (newest first). Say what was done and why, which files, how it
   was verified (exact commands and result, e.g. "236 tests pass in the venv, ruff clean"), what was **not** verified
   (anything needing a real Mac, a real API key, or a person), known issues, and what is left. Entries are history: never
   delete or rewrite old ones; correct a wrong statement by adding a note under it.
2. **`docs/ARCHITECTURE.md`**: the current truth about how things work. If you change an internal (a config value, a data
   file, an endpoint, a build step, an invariant), change this file so it matches the code. Stale architecture notes are
   worse than none.
3. **`docs/DECISIONS.md`**: when you choose between approaches, record the choice, the reason, and what you rejected.
4. Be **specific**: file paths, function names, config keys, endpoints, constants, commands, numbers, gotchas and how you
   found them. Short precise facts beat paragraphs. No marketing.
5. Be **honest**: mark what you did not test or could not verify. Don't write that something works unless you ran it.
6. Read `docs/ARCHITECTURE.md` and the top of `docs/PROGRESS.md` **before** you start, so you build on what exists.
7. Commit the docs with the code they describe.

Research-only tasks need no docs change unless you learned something a future agent would otherwise have to rediscover.

Related files: `docs/LAUNCH.md` is the launch plan and its status; `docs/WEBSITE_BRIEF.md` is the verified-facts brief for
website copy. Update them when the facts they hold change.

## Hard constraints

- **Onitry is free and bring-your-own-key.** Don't reintroduce prices, plans, a license check, accounts or calls to an
  Onitry server in the default flow. The paid designs (`byok`, `managed`, `server/`, `core/license.py`, `core/auth.py`)
  are legacy and unreachable unless `ONITRY_ENABLE_LEGACY_EDITIONS=1`.
- **Never write a screenshot to disk.** Capture, encode and send from memory only. No keylogging.
- **Website claims must be true in the code.** Check `docs/WEBSITE_BRIEF.md` rules before editing `website/src`.
- Don't open a pull request unless the user asks. Develop on the branch you were given and push to it.
- Never commit secrets, `data/`, `website/node_modules/`, or build output at the repo root (`build/`, `dist/`).

## How to check your work

```bash
python -m unittest discover -s tests        # needs the deps in requirements*.txt; see ARCHITECTURE.md "Testing"
ruff check .
cd website && npx vite build --outDir /tmp/site-check --emptyOutDir   # the site builds
```

The Mac app is built and smoke-tested by `.github/workflows/build-mac.yml` on real Macs; you can read results with the
GitHub Actions tools. The GUI cannot be run on Linux (no tkinter, no macOS APIs).
