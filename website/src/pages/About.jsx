import styles from "./About.module.css";

const ROADMAP = [
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
    title: "Idle detection",
    body: "Skip API calls when the mouse and keyboard have been idle — save costs when you step away.",
  },
  {
    status: "planned",
    title: "Windows / Linux support",
    body: "Cross-platform builds without macOS-specific dependencies.",
  },
  {
    status: "planned",
    title: "Session reports",
    body: "End-of-session summary: time on task, off-task events, activity breakdown.",
  },
];

export default function About() {
  const shipped = ROADMAP.filter((r) => r.status === "shipped");
  const planned = ROADMAP.filter((r) => r.status === "planned");

  return (
    <main className={styles.page}>
      <div className={styles.inner}>

        {/* Roadmap */}
        <section className={styles.section}>
          <p className={styles.label}>Roadmap</p>
          <h2 className={styles.title}>What's been built &amp; what's coming</h2>

          <div className={styles.roadmapGroup}>
            <h3 className={styles.groupTitle}>
              <span className={styles.dotShipped} /> Shipped
            </h3>
            <div className={styles.roadmapList}>
              {shipped.map((item) => (
                <RoadmapItem key={item.title} {...item} />
              ))}
            </div>
          </div>

          <div className={styles.roadmapGroup}>
            <h3 className={styles.groupTitle}>
              <span className={styles.dotPlanned} /> Planned
            </h3>
            <div className={styles.roadmapList}>
              {planned.map((item) => (
                <RoadmapItem key={item.title} {...item} />
              ))}
            </div>
          </div>
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
              value="github.com/yourname/onitry"
              href="https://github.com"
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
