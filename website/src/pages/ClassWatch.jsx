import styles from "./Home.module.css";

// ── Subcomponents ──────────────────────────────────────────────────────────

function TerminalPreview() {
  return (
    <div className={styles.previewWrap}>
      <div className={styles.window}>
        <div className={styles.titlebar}>
          <span className={styles.dot} style={{ background: "#ff5f57" }} />
          <span className={styles.dot} style={{ background: "#febc2e" }} />
          <span className={styles.dot} style={{ background: "#28c840" }} />
          <span className={styles.windowTitle}>classwatch</span>
        </div>
        <div className={styles.windowBody}>
          <div className={styles.log}>
            <p>$ python room_cli.py --task "lab assignment"</p>
            <p className={styles.logOn}>[10:14:32] screen_1 (ON TASK): Writing code in VS Code &nbsp;</p>
            <p className={styles.logOff}>[10:14:47] screen_2 (OFF TASK): Watching a video &nbsp;</p>
            <p className={styles.logOn}>[10:15:02] screen_3 (ON TASK): Reading course PDF &nbsp;</p>
            <p className={styles.logOn}>[10:15:17] screen_1 (ON TASK): Writing code in VS Code &nbsp;</p>
          </div>
        </div>
      </div>
    </div>
  );
}

function Step({ num, title, body }) {
  return (
    <div className={styles.step}>
      <div className={styles.stepNum}>{num}</div>
      <h3>{title}</h3>
      <p>{body}</p>
    </div>
  );
}

function Feature({ icon, title, body }) {
  return (
    <div className={styles.feature}>
      <div className={styles.featureIcon}>{icon}</div>
      <h3>{title}</h3>
      <p>{body}</p>
    </div>
  );
}

function scrollToId(id) {
  document.getElementById(id)?.scrollIntoView({ behavior: "smooth" });
}

// ── Page ───────────────────────────────────────────────────────────────────

export default function ClassWatch({ onNav }) {
  return (
    <main>
      {/* Hero */}
      <section className={styles.hero}>
        <div className={styles.badge}>
          <span className={styles.badgeDot} />
          Onitry · macOS · Camera-based · Free CLI tool
        </div>
        <h1>Watch the room,<br /><em>not just the screen.</em></h1>
        <p>ClassWatch points a camera at a room and tracks activity across every laptop and monitor in view — a lab, a shared workspace, a classroom.</p>
        <div className={styles.heroCta}>
          <button className={styles.btnPrimary} onClick={() => onNav?.("docs")}>Get started</button>
          <button className={styles.btnOutline} onClick={() => scrollToId("how-it-works")}>See how it works</button>
        </div>
        <span className={styles.heroNote}>Command-line, no GUI yet · open source · macOS only</span>
        <TerminalPreview />
      </section>

      {/* How it works */}
      <section className={styles.section} style={{ background: "var(--bg2)" }} id="how-it-works">
        <div className={styles.inner}>
          <p className={styles.sectionLabel}>How it works</p>
          <h2 className={styles.sectionTitle}>One camera, every screen in view</h2>
          <p className={styles.sectionSub}>Point it at a room once, then let it run — no per-device install, no agent on the watched machines.</p>
          <div className={styles.steps}>
            <Step num="01" title="Point a camera at the room" body="Any camera ClassWatch can see through — a webcam works fine for a small lab or classroom." />
            <Step num="02" title="Screens are detected and tracked" body="A vision model finds every laptop/monitor in frame and keeps each one's identity across capture cycles." />
            <Step num="03" title="Get a per-screen activity log" body="Each tracked screen gets its own independent activity log and a final markdown report." />
          </div>
        </div>
      </section>

      {/* Features */}
      <section className={styles.section}>
        <div className={styles.inner}>
          <p className={styles.sectionLabel}>Features</p>
          <h2 className={styles.sectionTitle}>Built for watching a room, not a person</h2>
          <div className={styles.features}>
            <Feature icon="📷" title="Multi-screen tracking"     body="Finds every laptop and monitor in a single camera frame — not limited to one device." />
            <Feature icon="🕵️" title="Passive observer"          body="No popups, no spoken reminders, no interrupts. It just logs what's visible and writes a report." />
            <Feature icon="🔗" title="Identity across frames"    body="Screens are matched by position across capture cycles, so the same physical screen keeps the same ID." />
            <Feature icon="📝" title="Markdown session reports"  body="Ctrl+C stops it and writes a full timeline and on-task percentage per screen." />
            <Feature icon="🖥️" title="No install on watched machines" body="Nothing runs on the laptops/monitors being watched — everything happens from the camera side." />
            <Feature icon="🆓" title="Free, open source"         body="No license, no account, no subscription — clone it and run it." />
          </div>
        </div>
      </section>

      {/* Get started */}
      <section className={styles.section} style={{ background: "var(--bg2)" }} id="get-started">
        <div className={styles.inner}>
          <p className={styles.sectionLabel}>Get started</p>
          <h2 className={styles.sectionTitle}>Free — clone it and run it.</h2>
          <p className={styles.sectionSub}>ClassWatch is a command-line tool. No pricing, no account — see the docs for full setup.</p>
          <div className={styles.heroCta} style={{ justifyContent: "flex-start", marginTop: 32 }}>
            <button className={styles.btnPrimary} onClick={() => onNav?.("docs")}>
              View installation docs
            </button>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className={styles.footer}>
        <div className={styles.footerInner}>
          <span className={styles.footerLogo}>Onit<span>ry</span></span>
          <span>© 2026 Onitry. All rights reserved.</span>
          <span>
            <a href="#">Privacy</a> · <a href="#">Terms</a>
          </span>
        </div>
      </footer>
    </main>
  );
}
