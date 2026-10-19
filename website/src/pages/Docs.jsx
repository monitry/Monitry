import { useState } from "react";
import styles from "./Docs.module.css";

// ── Content ────────────────────────────────────────────────────────────────

const SECTIONS = [
  { id: "installation",     label: "Installation",        group: "Full Focus" },
  { id: "how-it-works",     label: "How monitoring works", group: "Full Focus" },
  { id: "configuration",    label: "Configuration",        group: "Full Focus" },
  { id: "faq",              label: "FAQ",                  group: "Full Focus" },
  { id: "cw-installation",  label: "Installation",         group: "ClassWatch" },
  { id: "cw-how-it-works",  label: "How it works",         group: "ClassWatch" },
  { id: "cw-usage",         label: "Usage",                group: "ClassWatch" },
  { id: "cw-faq",           label: "FAQ",                  group: "ClassWatch" },
];

const GROUPS = ["Full Focus", "ClassWatch"];

function Installation() {
  return (
    <article className={styles.article}>
      <h1>Full Focus — Installation</h1>
      <p className={styles.lead}>Get Full Focus running on your Mac in under 5 minutes.</p>

      <h2>Requirements</h2>
      <ul>
        <li>macOS 13 (Ventura) or later</li>
        <li>Python 3.10+ with <code>conda</code> (or any virtualenv)</li>
        <li>If you're on the BYOK plan: an AI API key. Managed plan: just a Google account.</li>
      </ul>

      <h2>1 — Clone the repo</h2>
      <pre><code>{`git clone https://github.com/monitry/Monitry.git
cd Monitry`}</code></pre>

      <h2>2 — Create the environment</h2>
      <pre><code>{`conda create -n opencv-env python=3.11
conda activate opencv-env
pip install -r requirements.txt`}</code></pre>

      <h2>3 — Pick your edition</h2>
      <p>
        Full Focus ships as two editions from the same codebase, selected with an environment
        variable. Set it once before launching:
      </p>
      <pre><code>{`export ONITRY_EDITION=byok      # own API key, $30 one-time
export ONITRY_EDITION=managed   # Google sign-in, free or $19/mo`}</code></pre>
      <p>
        Leaving it unset runs the unrestricted developer build (model picker, every
        resolution, no license/sign-in gate) — useful for trying things out locally.
      </p>

      <h2>4 — Grant permissions</h2>
      <p>Full Focus needs <strong>Screen Recording</strong> permission to capture screenshots.</p>
      <ol>
        <li>Open <strong>System Settings → Privacy &amp; Security → Screen Recording</strong></li>
        <li>Toggle on your terminal app (e.g. Terminal, iTerm2)</li>
        <li>Restart the terminal</li>
      </ol>

      <h2>5 — Set your API key or sign in</h2>
      <p>
        Launch the app. On BYOK, click <strong>Set Key</strong> — your key is stored securely
        in the macOS Keychain, never written to disk in plaintext. On Managed, click
        <strong> Sign in with Google</strong> instead — no key needed.
      </p>
      <pre><code>{`conda run -n opencv-env python gui.py`}</code></pre>

      <h2>6 — Start monitoring</h2>
      <p>
        Type your task and click <strong>Start Monitoring</strong>.
        Full Focus waits 5 seconds before the first check so you can get settled.
      </p>

      <div className={styles.tip}>
        <strong>Tip:</strong> Run <code>python menubar.py</code> instead to get a persistent
        menu bar icon that survives across sessions. It spawns the GUI window on demand.
      </div>
    </article>
  );
}

function HowItWorks() {
  return (
    <article className={styles.article}>
      <h1>How monitoring works</h1>
      <p className={styles.lead}>
        Full Focus periodically screenshots your screen, sends it to an AI model, and acts on the result.
        Here's exactly what happens each cycle.
      </p>

      <h2>The monitoring loop</h2>
      <ol>
        <li>A screenshot is taken at the configured resolution</li>
        <li>The image, your task description, recent activity log, and the AI's running notes are sent to the API</li>
        <li>The AI responds with a JSON object — <code>onTask</code>, <code>interrupt</code>, <code>activity</code>, <code>reminder</code>, and updated <code>notes</code></li>
        <li>Full Focus acts on the result (see below), logs the activity, and waits for the next interval</li>
      </ol>

      <h2>Adaptive intervals</h2>
      <p>
        The check interval starts at <strong>10 seconds</strong> and increases by 10 seconds
        after each check, up to a maximum of <strong>120 seconds</strong>. This slows down
        polling when you're in a steady flow state to save API costs.
      </p>
      <p>
        If you're caught off task, the interval immediately snaps back to 10 seconds to
        watch you more closely while you find your footing again.
      </p>
      <p>
        Every interval also has a <strong>jitter</strong> of 0.4–1.6× applied, so checks
        don't feel mechanical. The effective minimum is always 10 seconds.
      </p>

      <h2>Interrupt vs soft notification</h2>
      <p>
        The AI decides whether your situation warrants a hard interrupt or a soft nudge
        by setting the <code>interrupt</code> field in its response.
      </p>
      <div className={styles.twoCol}>
        <div className={styles.card}>
          <h3>Hard interrupt</h3>
          <p>A red popup appears <em>above all other windows</em>, plays a spoken reminder via TTS, and requires you to type a full sentence before you can dismiss it.</p>
        </div>
        <div className={styles.card}>
          <h3>Soft notification</h3>
          <p>A silent macOS banner appears in the top-right corner. It doesn't steal focus or make noise — just a gentle tap on the shoulder.</p>
        </div>
      </div>

      <h2>Session memory</h2>
      <p>
        The AI maintains a short <code>notes</code> field across every check in a session.
        This lets it build context over time — e.g. noting that you've been off task
        twice already, or that you seem to be in a reading phase.
      </p>

      <h2>Typing challenge</h2>
      <p>
        Hard-interrupt popups can't be dismissed with a single click. You must type a
        randomly chosen ~25-word sentence exactly before the "Back to work" button activates.
        While the popup is open, monitoring is paused — no new checks run until you dismiss it.
      </p>

      <h2>Idle detection</h2>
      <p>
        If your mouse and keyboard have been untouched for 5 minutes, checks pause
        automatically — no screenshot, no API call, no cost — until you're back. This
        applies regardless of edition.
      </p>
    </article>
  );
}

function Configuration() {
  return (
    <article className={styles.article}>
      <h1>Configuration</h1>
      <p className={styles.lead}>
        What you can configure depends on which edition you're running — this keeps costs
        predictable for the managed plan and keeps BYOK fully in your control.
      </p>

      <h2>Model</h2>
      <p>
        <strong>BYOK and Managed are both locked to a single fast, cheap model</strong> —
        there's no picker, and on Managed the server enforces this too, so a modified client
        can't request a pricier model against the flat subscription. Only the unrestricted
        developer build (no <code>ONITRY_EDITION</code> set) exposes a model picker, for testing.
      </p>

      <h2>Resolution</h2>
      <table className={styles.table}>
        <thead>
          <tr><th>Option</th><th>Max width</th><th>Available on</th></tr>
        </thead>
        <tbody>
          <tr><td>High</td><td>1280px</td><td>BYOK, developer build</td></tr>
          <tr><td>Medium</td><td>800px</td><td>All editions — the Managed free tier is locked here</td></tr>
          <tr><td>Low</td><td>512px</td><td>BYOK, developer build</td></tr>
          <tr><td>Minimal</td><td>320px</td><td>BYOK, developer build</td></tr>
        </tbody>
      </table>
      <p>
        Managed Pro subscribers get a choice between Medium and High detail; the free tier
        is fixed at Medium. BYOK keeps full JPEG-quality control (20–100) too — Managed doesn't
        expose it at all, to keep per-check cost predictable against the flat plan.
      </p>

      <h2>API key (BYOK) / Google sign-in (Managed)</h2>
      <p>
        BYOK: click <strong>Set Key</strong> to store your AI API key in the macOS Keychain —
        retrieved on startup, never written to disk in plaintext. You'll also enter your
        one-time license key once, verified against Onitry's server and then cached locally.
      </p>
      <p>
        Managed: click <strong>Sign in with Google</strong> instead. No key to manage — your
        session token is stored in the Keychain after sign-in.
      </p>

      <h2>Grace period</h2>
      <p>
        The one setting available in every edition, including Managed free. After you dismiss
        an off-task popup, Full Focus pauses new checks for this long (default 60s, 0–300s range,
        0 disables it) — enough time to actually switch tasks before being checked again.
      </p>

      <h2>Advanced — editing config.py</h2>
      <p>Lower-level constants live in <code>config.py</code> at the project root:</p>
      <pre><code>{`CHECK_INTERVAL    = 10    # minimum interval (seconds)
MAX_TOKENS_PER_RESPONSE = 512
CONTEXT_MAX_CHARS = 2000  # chars of activity log sent to the AI`}</code></pre>
    </article>
  );
}

function FAQ() {
  const items = [
    {
      q: "Is my screen data stored anywhere?",
      a: "No. Screenshots are sent directly to the AI API for analysis and are not retained by Full Focus.",
    },
    {
      q: "Does it log my keystrokes?",
      a: "No. An earlier version included a keylogger for additional context, but it was removed. Full Focus now relies entirely on screenshots.",
    },
    {
      q: "What if I'm doing something personal on screen?",
      a: "Full Focus captures whatever is on your primary display. If you want a break, click Stop Monitoring — it's your tool.",
    },
    {
      q: "Why is it macOS only?",
      a: "The menu bar app uses rumps (macOS-specific), and screen capture relies on mss with macOS permissions. Windows/Linux support is on the roadmap.",
    },
    {
      q: "Can I use it without the menu bar app?",
      a: "Yes — run gui.py directly. The menu bar app (menubar.py) is optional; it just adds a persistent status icon (and, on the developer/BYOK builds, an AI chat feature).",
    },
    {
      q: "The popup appeared but I'm actually on task. What happened?",
      a: "The AI makes mistakes sometimes. Click \"Not actually off task?\" on the popup (or the flag button in the main window) and explain what you were really doing — that feedback gets fed back into the AI's context so it recalibrates on the next check.",
    },
    {
      q: "BYOK or Managed — which should I pick?",
      a: "BYOK if you already have an Anthropic API key and want a one-time cost with full control. Managed if you'd rather not deal with API keys at all — sign in with Google and start free immediately, upgrade only if the 1hr/day cap is limiting.",
    },
  ];

  return (
    <article className={styles.article}>
      <h1>FAQ</h1>
      <p className={styles.lead}>Common questions about Full Focus.</p>
      <div className={styles.faqList}>
        {items.map(({ q, a }) => (
          <div key={q} className={styles.faqItem}>
            <h3>{q}</h3>
            <p>{a}</p>
          </div>
        ))}
      </div>
    </article>
  );
}

function CwInstallation() {
  return (
    <article className={styles.article}>
      <h1>ClassWatch — Installation</h1>
      <p className={styles.lead}>Get ClassWatch running on your Mac in a few minutes.</p>

      <h2>Requirements</h2>
      <ul>
        <li>macOS 13 (Ventura) or later</li>
        <li>Python 3.10+ with <code>conda</code> (or any virtualenv)</li>
        <li>A camera that can see the room (a webcam is fine)</li>
        <li>An Anthropic API key</li>
      </ul>

      <h2>1 — Clone the repo</h2>
      <pre><code>{`git clone https://github.com/monitry/Monitry.git
cd Monitry`}</code></pre>

      <h2>2 — Create the environment</h2>
      <pre><code>{`conda create -n opencv-env python=3.11
conda activate opencv-env
pip install -r requirements.txt`}</code></pre>

      <h2>3 — Install the room-monitor dependencies</h2>
      <p>
        ClassWatch needs a heavier, optional dependency set (pulls in a vision model + torch)
        that isn't installed by the base app:
      </p>
      <pre><code>{`pip install -r requirements-room.txt`}</code></pre>

      <h2>4 — Set your API key</h2>
      <pre><code>{`export ANTHROPIC_API_KEY=your_key_here`}</code></pre>

      <h2>5 — Run it</h2>
      <pre><code>{`conda run -n opencv-env python room_cli.py`}</code></pre>

      <div className={styles.tip}>
        <strong>Tip:</strong> Point the camera so it can see the screens you want tracked, then
        run with <code>--task</code> to get on/off-task judgments instead of just an activity log.
      </div>
    </article>
  );
}

function CwHowItWorks() {
  return (
    <article className={styles.article}>
      <h1>ClassWatch — How it works</h1>
      <p className={styles.lead}>
        ClassWatch is a passive observer — no popups, no spoken reminders, no interrupts.
        It just logs what's visible on each screen it can see and writes a report.
      </p>

      <h2>What it's for</h2>
      <p>
        Watching several physical screens at once from a single camera — a lab, a shared
        workspace, a classroom. Unlike Full Focus's per-device monitor, nothing installs on
        the machines being watched; everything happens from the camera side.
      </p>

      <h2>How it identifies screens</h2>
      <ol>
        <li>A vision model detects every laptop and monitor in the camera frame</li>
        <li>Each screen's surface is segmented and perspective-corrected into a flat rectangle
          (falls back to a plain crop if segmentation fails on a low-quality shot — a screen is
          never silently dropped)</li>
        <li>Screens are matched across capture cycles by position, so the same physical screen
          keeps the same ID even as the camera captures repeatedly</li>
        <li>Each tracked screen gets its own independent activity log and AI-maintained notes</li>
      </ol>

      <h2>With vs. without a task</h2>
      <div className={styles.twoCol}>
        <div className={styles.card}>
          <h3>With --task</h3>
          <p>Every detected screen is judged on/off task against the same shared task description, same as Full Focus's screenshot checks.</p>
        </div>
        <div className={styles.card}>
          <h3>Without --task</h3>
          <p>No on/off-task judgment — ClassWatch just logs what activity it sees on each screen, with no verdict attached.</p>
        </div>
      </div>
    </article>
  );
}

function CwUsage() {
  return (
    <article className={styles.article}>
      <h1>ClassWatch — Usage</h1>
      <p className={styles.lead}>Command-line flags and what the final report looks like.</p>

      <h2>Basic usage</h2>
      <pre><code>{`python room_cli.py
python room_cli.py --task "working on the lab assignment" --interval 20
python room_cli.py --camera 1 --conf 0.3 --max-cycles 5`}</code></pre>

      <h2>Flags</h2>
      <table className={styles.table}>
        <thead>
          <tr><th>Flag</th><th>Default</th><th>Meaning</th></tr>
        </thead>
        <tbody>
          <tr><td><code>--camera</code></td><td>0</td><td>Camera index to capture from</td></tr>
          <tr><td><code>--interval</code></td><td>15</td><td>Seconds between capture cycles</td></tr>
          <tr><td><code>--conf</code></td><td>0.25</td><td>Detection confidence threshold</td></tr>
          <tr><td><code>--task</code></td><td>none</td><td>Shared task for every detected screen — omit to just log activity</td></tr>
          <tr><td><code>--report-path</code></td><td><code>data/room/report.md</code></td><td>Where the final report is written</td></tr>
          <tr><td><code>--max-cycles</code></td><td>none</td><td>Stop after N cycles instead of running forever</td></tr>
        </tbody>
      </table>

      <h2>Stopping and the report</h2>
      <p>
        Press <code>Ctrl+C</code> to stop. ClassWatch then writes a markdown report with every
        tracked screen's timeline and on-task percentage to <code>--report-path</code>.
      </p>
    </article>
  );
}

function CwFAQ() {
  const items = [
    {
      q: "Does anything install on the watched laptops/monitors?",
      a: "No. ClassWatch only needs a camera that can see the room — nothing runs on the machines being tracked.",
    },
    {
      q: "Is video or audio stored anywhere?",
      a: "No. Camera frames are sent directly to the AI API for analysis and are not retained by ClassWatch.",
    },
    {
      q: "Does it interrupt people or show popups?",
      a: "No — unlike Full Focus, ClassWatch is a passive observer. No popups, no TTS, no interrupts. It just logs and reports.",
    },
    {
      q: "Is there a GUI?",
      a: "Not yet — it's a command-line tool for now. A live-view GUI is on the roadmap.",
    },
    {
      q: "Why is it macOS only?",
      a: "The current build relies on macOS-specific camera/permission handling. Cross-platform support isn't ruled out, just not built yet.",
    },
    {
      q: "What does it cost to run?",
      a: "ClassWatch itself is free and open source. You pay only for your own Anthropic API usage, same as Full Focus's BYOK mode.",
    },
  ];

  return (
    <article className={styles.article}>
      <h1>FAQ</h1>
      <p className={styles.lead}>Common questions about ClassWatch.</p>
      <div className={styles.faqList}>
        {items.map(({ q, a }) => (
          <div key={q} className={styles.faqItem}>
            <h3>{q}</h3>
            <p>{a}</p>
          </div>
        ))}
      </div>
    </article>
  );
}

// ── Page ───────────────────────────────────────────────────────────────────

const CONTENT = {
  "installation":    Installation,
  "how-it-works":    HowItWorks,
  "configuration":   Configuration,
  "faq":             FAQ,
  "cw-installation": CwInstallation,
  "cw-how-it-works": CwHowItWorks,
  "cw-usage":        CwUsage,
  "cw-faq":          CwFAQ,
};

export default function Docs() {
  const [active, setActive] = useState("installation");
  const Content = CONTENT[active];

  return (
    <div className={styles.layout}>
      {/* Sidebar */}
      <aside className={styles.sidebar}>
        {GROUPS.map((group) => (
          <div key={group}>
            <p className={styles.sidebarLabel}>{group}</p>
            <nav>
              {SECTIONS.filter((s) => s.group === group).map((s) => (
                <button
                  key={s.id}
                  className={`${styles.sidebarLink} ${active === s.id ? styles.sidebarActive : ""}`}
                  onClick={() => setActive(s.id)}
                >
                  {s.label}
                </button>
              ))}
            </nav>
          </div>
        ))}
      </aside>

      {/* Content */}
      <main className={styles.content}>
        <Content />
      </main>
    </div>
  );
}
