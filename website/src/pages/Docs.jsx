import { useState } from "react";
import styles from "./Docs.module.css";

// ── Content ────────────────────────────────────────────────────────────────

const SECTIONS = [
  { id: "installation", label: "Installation" },
  { id: "how-it-works", label: "How monitoring works" },
  { id: "configuration", label: "Configuration" },
  { id: "faq",          label: "FAQ" },
];

function Installation() {
  return (
    <article className={styles.article}>
      <h1>Installation</h1>
      <p className={styles.lead}>Get Onitry running on your Mac in under 5 minutes.</p>

      <h2>Requirements</h2>
      <ul>
        <li>macOS 13 (Ventura) or later</li>
        <li>Python 3.10+ with <code>conda</code> (or any virtualenv)</li>
        <li>An AI API key</li>
      </ul>

      <h2>1 — Clone the repo</h2>
      <pre><code>{`git clone https://github.com/yourname/onitry.git
cd onitry`}</code></pre>

      <h2>2 — Create the environment</h2>
      <pre><code>{`conda create -n opencv-env python=3.11
conda activate opencv-env
pip install -r requirements.txt`}</code></pre>

      <h2>3 — Grant permissions</h2>
      <p>Onitry needs <strong>Screen Recording</strong> permission to capture screenshots.</p>
      <ol>
        <li>Open <strong>System Settings → Privacy &amp; Security → Screen Recording</strong></li>
        <li>Toggle on your terminal app (e.g. Terminal, iTerm2)</li>
        <li>Restart the terminal</li>
      </ol>

      <h2>4 — Set your API key</h2>
      <p>
        Launch the app and click <strong>Set Key</strong> in the GUI. Your key is stored securely
        in the macOS Keychain — it is never written to disk in plaintext.
      </p>
      <pre><code>{`conda run -n opencv-env python gui.py`}</code></pre>

      <h2>5 — Start monitoring</h2>
      <p>
        Type your task, choose a model and resolution, and click <strong>Start Monitoring</strong>.
        Onitry waits 5 seconds before the first check so you can get settled.
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
        Onitry periodically screenshots your screen, sends it to an AI model, and acts on the result.
        Here's exactly what happens each cycle.
      </p>

      <h2>The monitoring loop</h2>
      <ol>
        <li>A screenshot is taken at the configured resolution</li>
        <li>The image, your task description, recent activity log, and the AI's running notes are sent to the API</li>
        <li>The AI responds with a JSON object — <code>onTask</code>, <code>interrupt</code>, <code>activity</code>, <code>reminder</code>, and updated <code>notes</code></li>
        <li>Onitry acts on the result (see below), logs the activity, and waits for the next interval</li>
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
    </article>
  );
}

function Configuration() {
  return (
    <article className={styles.article}>
      <h1>Configuration</h1>
      <p className={styles.lead}>All options are set in the GUI before starting a session.</p>

      <h2>Model</h2>
      <table className={styles.table}>
        <thead>
          <tr><th>Option</th><th>Model</th><th>API cost</th><th>Best for</th></tr>
        </thead>
        <tbody>
          <tr><td>Fast</td><td>Lightweight model</td><td>~$0.09/hr</td><td>Daily use — fast &amp; cheap</td></tr>
          <tr><td>Balanced</td><td>Mid-tier model</td><td>~$0.28/hr</td><td>Better context understanding</td></tr>
          <tr><td>Powerful</td><td>Full-size model</td><td>~$0.47/hr</td><td>Maximum accuracy</td></tr>
        </tbody>
      </table>
      <p>These are AI API costs billed to your own key — not Onitry subscription charges.</p>

      <h2>Resolution</h2>
      <table className={styles.table}>
        <thead>
          <tr><th>Option</th><th>Max width</th><th>Relative cost</th><th>Notes</th></tr>
        </thead>
        <tbody>
          <tr><td>High</td><td>1280px</td><td>Baseline</td><td>Best for dense UIs</td></tr>
          <tr><td>Medium</td><td>800px</td><td>~40%</td><td>Recommended — good balance</td></tr>
          <tr><td>Low</td><td>512px</td><td>~16%</td><td>Works for most content</td></tr>
          <tr><td>Minimal</td><td>320px</td><td>~6%</td><td>Cheapest; may miss small text</td></tr>
        </tbody>
      </table>

      <h2>API key</h2>
      <p>
        Click <strong>Set Key</strong> in the GUI to store your AI API key in the macOS Keychain.
        It is retrieved on startup and never written to disk. To update it, click Set Key again.
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
      a: "No. Screenshots are sent directly to the AI API for analysis and are not retained by Onitry.",
    },
    {
      q: "Does it log my keystrokes?",
      a: "No. An earlier version included a keylogger for additional context, but it was removed. Onitry now relies entirely on screenshots.",
    },
    {
      q: "What if I'm doing something personal on screen?",
      a: "Onitry captures whatever is on your primary display. If you want a break, click Stop Monitoring — it's your tool.",
    },
    {
      q: "Why is it macOS only?",
      a: "The menu bar app uses rumps (macOS-specific), and screen capture relies on mss with macOS permissions. Windows/Linux support is on the roadmap.",
    },
    {
      q: "Can I use it without the menu bar app?",
      a: "Yes — run gui.py directly. The menu bar app (menubar.py) is optional; it just adds a persistent status icon and the AI chat feature.",
    },
    {
      q: "The popup appeared but I'm actually on task. What happened?",
      a: "The AI makes mistakes. If it's happening often, try a higher-tier model or a higher resolution. You can also make your task description more specific.",
    },
  ];

  return (
    <article className={styles.article}>
      <h1>FAQ</h1>
      <p className={styles.lead}>Common questions about Onitry.</p>
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
  "installation": Installation,
  "how-it-works": HowItWorks,
  "configuration": Configuration,
  "faq":           FAQ,
};

export default function Docs() {
  const [active, setActive] = useState("installation");
  const Content = CONTENT[active];

  return (
    <div className={styles.layout}>
      {/* Sidebar */}
      <aside className={styles.sidebar}>
        <p className={styles.sidebarLabel}>Documentation</p>
        <nav>
          {SECTIONS.map((s) => (
            <button
              key={s.id}
              className={`${styles.sidebarLink} ${active === s.id ? styles.sidebarActive : ""}`}
              onClick={() => setActive(s.id)}
            >
              {s.label}
            </button>
          ))}
        </nav>
      </aside>

      {/* Content */}
      <main className={styles.content}>
        <Content />
      </main>
    </div>
  );
}
