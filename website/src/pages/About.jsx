import styles from "./About.module.css";

const FULLFOCUS_ROADMAP = [
  {
    status: "shipped",
    title: "Core monitoring",
    body: "Screenshot-based on-task detection, adaptive intervals, tkinter GUI, macOS menu bar.",
  },
  {
    status: "shipped",
    title: "Typing-challenge dismissal",
    body: "Hard-interrupt popups require typing a full sentence before dismissing — no easy opt-out.",
  },
  {
    status: "shipped",
    title: "Session memory",
    body: "The AI maintains running notes across checks within a session for richer context.",
  },
  {
    status: "shipped",
    title: "Soft vs hard interrupt",
    body: "The AI decides whether a situation warrants a focus-stealing popup or a silent banner.",
  },
  {
    status: "shipped",
    title: "Pause without quitting",
    body: "A 10-minute pause button for real breaks, instead of closing the app and forgetting to reopen it.",
  },
  {
    status: "shipped",
    title: "Flag false positives",
    body: "Tell the AI when it got a call wrong — the correction feeds back into its context for the next check.",
  },
  {
    status: "shipped",
    title: "Session reports",
    body: "End-of-session summary: time on task, off-task events, a visual timeline, activity breakdown.",
  },
  {
    status: "shipped",
    title: "BYOK & Managed editions",
    body: "A $30 one-time bring-your-own-key plan, and a Google-sign-in managed plan with a free tier.",
  },
  {
    status: "shipped",
    title: "Idle detection",
    body: "Checks pause after 5 minutes with no mouse/keyboard input — no wasted API cost while you're away.",
  },
  {
    status: "planned",
    title: "Audio input",
    body: "Detect background noise (music, video, calls) as an additional signal alongside the screenshot.",
  },
  {
    status: "planned",
    title: "Focus mode",
    body: "Block distracting sites at the network level while a session is active.",
  },
  {
    status: "planned",
    title: "Windows / Linux support",
    body: "Cross-platform builds without macOS-specific dependencies.",
  },
];

const CLASSWATCH_ROADMAP = [
  {
    status: "shipped",
    title: "Multi-screen detection",
    body: "A vision model finds every laptop/monitor in a single camera frame.",
  },
  {
    status: "shipped",
    title: "Cross-frame identity tracking",
    body: "Screens are matched by position across capture cycles, so the same physical screen keeps the same ID.",
  },
  {
    status: "shipped",
    title: "Perspective correction",
    body: "Each screen's surface is segmented and perspective-corrected into a flat rectangle before analysis.",
  },
  {
    status: "shipped",
    title: "Per-screen activity log",
    body: "Each tracked screen gets its own independent activity log and AI-maintained notes.",
  },
  {
    status: "shipped",
    title: "Markdown session reports",
    body: "Stopping the run writes a full timeline and on-task percentage per screen.",
  },
  {
    status: "planned",
    title: "Live-view GUI",
    body: "A proper window instead of a CLI-only tool — live view, not just a report at the end.",
  },
  {
    status: "planned",
    title: "Multi-camera support",
    body: "Cover a larger room or multiple rooms from more than one camera feed at once.",
  },
  {
    status: "planned",
    title: "Windows / Linux support",
    body: "Cross-platform builds without macOS-specific dependencies.",
  },
];

function ProductRoadmap({ name, items }) {
  const shipped = items.filter((r) => r.status === "shipped");
  const planned = items.filter((r) => r.status === "planned");

  return (
    <div className={styles.productGroup}>
      <h3 className={styles.productTitle}>{name}</h3>

      <div className={styles.roadmapGroup}>
        <h4 className={styles.groupTitle}>
          <span className={styles.dotShipped} /> Shipped
        </h4>
        <div className={styles.roadmapList}>
          {shipped.map((item) => (
            <RoadmapItem key={item.title} {...item} />
          ))}
        </div>
      </div>

      <div className={styles.roadmapGroup}>
        <h4 className={styles.groupTitle}>
          <span className={styles.dotPlanned} /> Planned
        </h4>
        <div className={styles.roadmapList}>
          {planned.map((item) => (
            <RoadmapItem key={item.title} {...item} />
          ))}
        </div>
      </div>
    </div>
  );
}

export default function About() {
  return (
    <main className={styles.page}>
      <div className={styles.inner}>

        {/* Roadmap */}
        <section className={styles.section}>
          <p className={styles.label}>Roadmap</p>
          <h2 className={styles.title}>What's been built &amp; what's coming</h2>

          <ProductRoadmap name="Full Focus" items={FULLFOCUS_ROADMAP} />
          <ProductRoadmap name="ClassWatch" items={CLASSWATCH_ROADMAP} />
        </section>

        {/* Contact */}
        <section className={styles.section}>
          <p className={styles.label}>Contact</p>
          <h2 className={styles.title}>Get in touch</h2>
          <p className={styles.sub}>
            Found a bug, have a feature idea, or just want to say hi? Reach out.
          </p>

          <div className={styles.contactGrid}>
            <ContactCard
              icon="✉️"
              title="Email"
              value="calebcraig81@gmail.com"
              href="mailto:calebcraig81@gmail.com"
            />
            <ContactCard
              icon="🐙"
              title="GitHub"
              value="github.com/monitry/Monitry"
              href="https://github.com/monitry/Monitry"
            />
          </div>
        </section>

      </div>
    </main>
  );
}

function RoadmapItem({ title, body }) {
  return (
    <div className={styles.roadmapItem}>
      <h4>{title}</h4>
      <p>{body}</p>
    </div>
  );
}

function ContactCard({ icon, title, value, href }) {
  return (
    <a href={href} className={styles.contactCard} target="_blank" rel="noreferrer">
      <span className={styles.contactIcon}>{icon}</span>
      <div>
        <div className={styles.contactTitle}>{title}</div>
        <div className={styles.contactValue}>{value}</div>
      </div>
    </a>
  );
}
