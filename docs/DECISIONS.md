# Decisions (why things are the way they are)

Rule: see `CLAUDE.md`. Add an entry when you choose between approaches. Format: decision, reason, rejected alternatives.

## Free + bring your own key

- **Decision:** no license, subscription, account or Onitry server. The user's Anthropic key calls Anthropic directly.
- **Why:** owner decision (2026-11-26). The paid backend (`server/`: Stripe, Google OAuth) was never deployed, so removing it
  makes launching simple and shrinks the privacy and legal surface.
- **Rejected:** deleting the paid code (kept, unreachable behind `ONITRY_ENABLE_LEGACY_EDITIONS=1`, so it can be revived or
  removed later); a hosted managed plan.
- **Open:** Haiku-only for free users (kept from old `byok`); letting free users pick a model is a small change and was suggested.

## `free` is `byok` minus the license

Smallest safe change: reuse the existing key row and Haiku limit, drop the license verification and any network call to an Onitry host.

## Data folder depends on how the app runs

Source checkout: `<repo>/data` (unchanged). Packaged app: `~/Library/Application Support/Onitry`, because a `.app` bundle is read-only
in practice and replaced on update. `ONITRY_DATA_DIR` overrides. Implemented in `core/paths.py`; `config.DATA_DIR` is the single value.

## PyInstaller for the Mac app (not py2app)

Works from a plain CI runner with python.org-style Python and Tk; windowed bundle from one entry file (`onitry_app.py`);
`--selftest` lets CI check the bundle imports everything. The packaged app opens the Full Focus window directly; the optional
menu bar app (rumps) is excluded because it spawns `gui.py` with `sys.executable`, which doesn't work inside a bundle.
Rejected: shipping a launcher that creates a venv on first run (slow, fragile); py2app (not tried).

## Ad-hoc signed, not notarized

Apple Silicon refuses unsigned code, so the build is ad-hoc signed (`codesign --sign -`). Notarization needs a US$99/year Developer
account; until then users approve the app once and the site says exactly how. Rejected: hiding the warning; asking users to
disable Gatekeeper.

## Two macOS runners

`macos-latest` (Apple Silicon) and `macos-15-intel` build separate `.dmg`s (a universal2 build needs a universal Python, which the
setup action does not provide). `fail-fast: false` so one architecture failing doesn't block the other.

## Website: hash routing, no router library

Static hosting (Porkbun) needs no rewrites with hash routes; every page still has a shareable URL and working back button.
Docs sections use `#/docs/<section>`. Rejected: `react-router` (extra dependency, needs server rewrites).

## Website copy comes from a verified brief

`docs/WEBSITE_BRIEF.md` lists verified facts with the rules (no prices, no "open source" until a LICENSE exists, no personal email,
no unverified claims). Page agents had disjoint file ownership; one QA agent reviewed in a real browser and was the only editor then.

## ClassWatch is shown as experimental

Unit-tested with mocks only; no evidence of accuracy on real footage; it observes other people (consent and local rules);
`ultralytics` is AGPL-3.0. The site labels it experimental and says so plainly.

## Git

Merged `main` into the work branch (instead of rebasing) to keep history and resolve conflicts once. `website/node_modules` was removed
from tracking (it was already in `.gitignore`). Git history still holds personal commit emails; rewriting history is the owner's call.
