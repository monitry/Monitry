import styles from "./About.module.css";
import { ISSUES_URL } from "../site.js";

// Every "built" item below was checked against the code (see the audit notes in the launch report).
// "Not built yet" lists only things that do not exist in the repo today.

const FULLFOCUS_BUILT = [
  {
    title: "Screen checks",
    body: "Takes a screenshot of your main display and asks Claude whether you are on task. Runs as a window, as an optional menu bar app, or in the terminal.",
  },
  {
    title: "Adaptive check interval",
    body: "Checks start 10 seconds apart and slowly stretch to 120 seconds while you stay on task, with some randomness. They drop back to 10 seconds as soon as you drift.",
  },
  {
    title: "Soft and hard interrupts",
    body: "The AI decides how loud to be: a silent notification banner, or a red popup on top of everything with the reminder read aloud.",
  },
  {
    title: "Typing challenge",
    body: "To close a hard popup early you type one of ten fixed sentences. It is a nudge, not a lock: the popup closes by itself after 90 seconds.",
  },
  {
    title: "Session memory",
    body: "Claude keeps short running notes between checks, and sees the last 10 lines of the session log, so it knows what you were doing a minute ago.",
  },
  {
    title: "Flag a false positive",
    body: "“Not actually off task?” lets you say what you were really doing. Your correction goes into the log for the next checks.",
  },
  {
    title: "Grace period and pause",
    body: "After you dismiss a popup, checks wait for a grace period you set (0 to 300 seconds). A Pause button gives you 10 minutes of break.",
  },
  {
    title: "Idle detection",
    body: "Checks stop after 5 minutes without mouse or keyboard input, so you are not paying for checks while you are away.",
  },
  {
    title: "Session summary",
    body: "When you stop, you get the time monitored, percent on task, a timeline bar, the number of interruptions and what the session cost.",
  },
  {
    title: "Browser bridge",
    body: "A local connection, protected by a pairing code, lets the separate Timecheck browser extension start, pause and stop monitoring and show your status.",
  },
  {
    title: "Weekly review",
    body: "On request from the Timecheck extension, Claude writes a short review of your week from the numbers the extension sends, using your own API key.",
  },
];

const FULLFOCUS_NOT_BUILT = [
  {
    title: "Audio input",
    body: "Using background sound (music, video, calls) as an extra signal next to the screenshot.",
  },
  {
    title: "Network-level site blocking",
    body: "Blocking distracting sites for the whole computer while a session runs. Onitry only watches and nudges today.",
  },
  {
    title: "A packaged Mac app",
    body: "Today you install from a terminal, which suits people comfortable with one. There is no installer or .app yet.",
  },
  {
    title: "Windows and Linux",
    body: "Onitry is macOS only: notifications, speech, idle detection and the menu bar all use macOS tools.",
  },
];

const CLASSWATCH_BUILT = [
  {
    title: "Screen detection",
    body: "A detection model finds laptops and monitors in a camera frame.",
  },
  {
    title: "Tracking by position",
    body: "Each screen keeps an ID between captures by matching where it sits in the frame.",
  },
  {
    title: "Flattened crops",
    body: "Each screen is cut out and straightened when possible, and cropped plainly when not.",
  },
  {
    title: "Per-screen notes and log",
    body: "Claude describes each screen and keeps its own running notes and text log for it.",
  },
  {
    title: "Markdown report",
    body: "Pressing Ctrl+C stops the run and writes a report with a timeline for each screen.",
  },
];

const CLASSWATCH_NOT_BUILT = [
  {
    title: "A live window",
    body: "ClassWatch is terminal-only. You see a text log while it runs and a report at the end.",
  },
  {
    title: "More than one camera",
    body: "It reads one camera at a time.",
  },
];

function ItemList({ items }) {
  return (
    <ul className={styles.roadmapList}>
      {items.map((item) => (
        <li key={item.title} className={styles.roadmapItem}>
          <strong>{item.title}</strong>
          <p>{item.body}</p>
        </li>
      ))}
    </ul>
  );
}

function ProductRoadmap({ name, note, built, notBuilt }) {
  return (
    <div className={styles.productGroup}>
      <h3 className={styles.productTitle}>{name}</h3>
      {note && <p className={styles.productNote}>{note}</p>}

      <div className={styles.roadmapGroup}>
        <h4 className={styles.groupTitle}>
          <span className={styles.dotBuilt} aria-hidden="true" /> Built
        </h4>
        <ItemList items={built} />
      </div>

      <div className={styles.roadmapGroup}>
        <h4 className={styles.groupTitle}>
          <span className={styles.dotNot} aria-hidden="true" /> Not built yet
        </h4>
        <ItemList items={notBuilt} />
      </div>
    </div>
  );
}

export default function About() {
  return (
    <main className={styles.page}>
      <div className={styles.inner}>
        <header className={styles.header}>
          <p className={styles.label}>About</p>
          <h1 className={styles.pageTitle}>About Onitry</h1>
          <p className={styles.lead}>
            Onitry is a free Mac tool that watches your screen and nudges you when you drift off the task you
            set. You bring your own Anthropic API key. There is no account and no Onitry server.
          </p>
        </header>

        {/* Who makes this */}
        <section className={styles.section}>
          <h2 className={styles.title}>Who makes this, and why it&rsquo;s free</h2>
          {/* OWNER: replace or extend this paragraph with a real name or short story. */}
          <p className={styles.body}>
            Onitry is an independent project. It is free to use with your own Anthropic API key, so the only
            money involved is what you pay Anthropic for your own usage. Nobody here gets your data, because
            nothing is sent to us.
          </p>
          <p className={styles.body}>
            Read the <a href="#/privacy">Privacy</a> and <a href="#/terms">Terms</a> pages for the details.
          </p>
        </section>

        {/* Roadmap */}
        <section className={styles.section}>
          <h2 className={styles.title}>What&rsquo;s built and what isn&rsquo;t</h2>
          <p className={styles.body}>
            This list matches the code today. &ldquo;Not built yet&rdquo; means no dates and no promises.
          </p>

          <ProductRoadmap
            name="Full Focus"
            built={FULLFOCUS_BUILT}
            notBuilt={FULLFOCUS_NOT_BUILT}
          />
          <ProductRoadmap
            name="ClassWatch (experimental)"
            note="Its automated tests use stand-ins for the camera and the AI. It has not been measured on real classroom footage."
            built={CLASSWATCH_BUILT}
            notBuilt={CLASSWATCH_NOT_BUILT}
          />
        </section>

        {/* Contact */}
        <section className={styles.section}>
          <h2 className={styles.title}>Bugs and ideas</h2>
          <p className={styles.body}>
            Found a bug, or have an idea? Open an issue on GitHub. Please leave out screenshots and private
            details.
          </p>
          <a href={ISSUES_URL} className={styles.contactCard} target="_blank" rel="noreferrer">
            <div>
              <span className={styles.contactTitle}>GitHub Issues</span>
              <span className={styles.contactValue}>Report a bug or suggest something</span>
            </div>
            <span className={styles.arrow} aria-hidden="true">&rarr;</span>
          </a>
        </section>

      </div>
    </main>
  );
}
