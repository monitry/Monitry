# Onitry launch plan: free, bring your own API key

Decision this plan assumes: **Onitry is free. You bring your own Anthropic API key.** No license fee, no subscription,
no accounts, no Onitry servers. That deletes the whole backend (`server/`: Stripe, Google sign-in, usage caps) from the
launch path. Nothing in it was ever deployed.

What exists today (checked in the repo, not guessed):

- The app is a macOS Python app you clone and run from a conda environment. There is no installer.
- The website (`website/`, Vite + React) still sells "Pro, $19/month"; its button shows a "coming soon" alert; the
  Privacy and Terms links go nowhere; the contact card has a personal email and a placeholder GitHub link; the roadmap
  lists features as planned that the code already has.
- Hosting is static: the `website-deploy` branch holds built output "for Porkbun hosting".
- `main` is behind the working branch: the browser bridge to the Timecheck extension is only on
  `claude/bold-davinci-spz652`.
- `website/node_modules` (1,399 files, macOS binaries) and `website/dist` are committed to git.
- There is no LICENSE file.

## The route

Each step has a gate: don't start the next one until it holds.

### 0. Decisions only you can make (before anything ships)

| Decision | Why it blocks | Suggested default |
| --- | --- | --- |
| Free + bring-your-own-key, confirmed | Everything below depends on it | Yes |
| Open source or just free? Which license? | The site, README and releases must say the same thing. A public repo with no license is "all rights reserved". | MIT, public repo |
| One name: **Onitry** or **Monitry**? | The repo says Monitry, the product says Onitry | Onitry everywhere; rename the repo |
| Public contact | The site shows a personal Gmail address | A role address on your domain (hello@…) |
| How people install it | See step 4: the biggest gap | Developer install first, signed app later |
| Does ClassWatch launch with it? | It needs a camera and heavy dependencies (torch) | No: Full Focus only; mention ClassWatch as "coming" |

### 1. Make the product match the promise (agent: product)

Gate: the app starts with only an API key, never calls an Onitry server, no UI text mentions a price, license or
sign-in, and the tests pass. Revivable billing code stays but is unreachable.

### 2. Establish the facts (agent: fact-check)

Gate: a verified list of what the site may claim: cost per hour of monitoring (computed from the code), what leaves
the machine, what is stored on disk, which macOS permissions are needed, which features exist. Every marketing claim
on the new site traces to it.

### 3. Rewrite the website (agents: home, docs, about + legal, QA)

Gate: the site builds, every link works, no claim without a source in step 2, it reads well on a phone, and QA has
looked at it in a real browser at phone and desktop width.

### 4. Make it installable (needs you, and a Mac)

This is what stands between "a website" and "a launch". Options, in order of effort:

1. **Developer install** (days): a tagged GitHub release plus a one-command `install.sh` that creates the environment.
   Honest about the audience ("for people comfortable with a terminal").
2. **Packaged app** (about a week, needs macOS and an Apple Developer account, US$99/year): build a `.app` (py2app or
   Briefcase), sign and notarize it, ship a `.dmg`. Without notarization macOS shows a scary warning to every user.

Cannot be done from this Linux sandbox. Recommendation: launch with option 1, say so plainly, and do option 2 when
people ask for it.

### 5. Repo hygiene and merge

- Add `LICENSE`; remove personal data and placeholder URLs; `git rm -r --cached website/node_modules`
  (it is already in `.gitignore`); stop committing `website/dist` to `main`.
- Merge `claude/bold-davinci-spz652` into `main` (needs a pull request; not opened yet).
- Tag `v1.0.0`; write release notes.

### 6. Deploy

- `npm run build` in `website/`, copy `dist/` to the `website-deploy` branch, upload to Porkbun.
- Verify on the real domain: every page, every link, mobile width, the download button, privacy page.
- Hash routing (`#/docs`) means no server rewrites are needed on static hosting.

### 7. Soft launch, then public

- Soft: ten people you know, on fresh Macs. Watch where install fails; fix; update the docs.
- Public: a "Show HN" post and r/macapps, with the honest cost story ("about X per hour on your own key"). Product Hunt
  only once the app installs without a terminal.
- No analytics scripts on the site (it is a privacy-first product); measure with GitHub stars and release downloads.

### 8. After launch

- Watch cost reports: the first thing people ask about is the bill. The site's cost explanation must stay accurate when
  the default model or interval changes.
- Revisit a hosted option only if users ask for it. The revivable managed code is the starting point.

## Risks to keep in view

- **Claims that can't be backed up** (accuracy of on/off-task detection, "never stored" for screenshots) are the
  easiest way to lose trust. The fact-check step exists for this.
- **API cost surprises**: a runaway session costs real money on the user's key. The site and the app should both say how
  to set a spending limit in the Anthropic console.
- **Screen Recording permission** is a trust moment. The docs must say exactly why it's needed and what is sent.
- **Support load** for a free app with a terminal install: put the troubleshooting list in the docs before launch.
