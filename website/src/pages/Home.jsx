import styles from "./Home.module.css";

// ── Subcomponents ──────────────────────────────────────────────────────────

function AppPreview() {
  return (
    <div className={styles.previewWrap}>
      <div className={styles.window}>
        <div className={styles.titlebar}>
          <span className={styles.dot} style={{ background: "#ff5f57" }} />
          <span className={styles.dot} style={{ background: "#febc2e" }} />
          <span className={styles.dot} style={{ background: "#28c840" }} />
          <span className={styles.windowTitle}>Onitry</span>
        </div>
        <div className={styles.windowBody}>
          <Row label="Task:"  value="Finish the linear algebra coursework" />
          <Row label="Model:" value="Haiku 4.5 — ~$0.09/hr" select />
          <div className={styles.divider} />
          <div className={styles.startBtn}>Stop Monitoring</div>
          <div className={styles.statusOn}>ON TASK</div>
          <div className={styles.log}>
            <p className={styles.logOn}>[10:14:32] ON TASK: Reading MIT OpenCourseWare lecture notes &nbsp;(next in 47s)</p>
            <p className={styles.logOff}>[10:13:41] OFF TASK: Browsing YouTube &nbsp;(next in 10s)</p>
            <p className={styles.logOn}>[10:12:58] ON TASK: Writing Python implementation &nbsp;(next in 38s)</p>
          </div>
        </div>
      </div>
    </div>
  );
}

function Row({ label, value, select }) {
  return (
    <div className={styles.row}>
      <span className={styles.rowLabel}>{label}</span>
      <div className={`${styles.field} ${select ? styles.select : ""}`}>{value}</div>
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

// ── Page ───────────────────────────────────────────────────────────────────

export default function Home() {
  return (
    <main>
      {/* Hero */}
      <section className={styles.hero}>
        <div className={styles.badge}>
          <span className={styles.badgeDot} />
          macOS · AI-powered focus
        </div>
        <h1>Stay on task.<br /><em>Automatically.</em></h1>
        <p>Onitry watches your screen with AI and calls you out the moment you drift. No willpower required.</p>
        <div className={styles.heroCta}>
          <button className={styles.btnPrimary}>Start for $19/mo</button>
          <button className={styles.btnOutline}>See how it works</button>
        </div>
        <span className={styles.heroNote}>Cancel anytime · macOS only</span>
        <AppPreview />
      </section>

      {/* How it works */}
      <section className={styles.section} style={{ background: "var(--bg2)" }}>
        <div className={styles.inner}>
          <p className={styles.sectionLabel}>How it works</p>
          <h2 className={styles.sectionTitle}>Three steps to deep focus</h2>
          <p className={styles.sectionSub}>Set it once, then forget it. Onitry runs quietly in your menu bar and only interrupts when it matters.</p>
          <div className={styles.steps}>
            <Step num="01" title="Tell it your task" body="Type what you're working on. That's all the context Onitry needs." />
            <Step num="02" title="AI watches your screen" body="Onitry takes a screenshot every few seconds and decides if you're on track — no keystroke logging, no invasive monitoring." />
            <Step num="03" title="Get called back in" body="When you drift, Onitry interrupts you with a firm reminder and makes you type a full sentence to dismiss it." />
          </div>
        </div>
      </section>

      {/* Features */}
      <section className={styles.section}>
        <div className={styles.inner}>
          <p className={styles.sectionLabel}>Features</p>
          <h2 className={styles.sectionTitle}>Built to actually keep you honest</h2>
          <div className={styles.features}>
            <Feature icon="👁"  title="Vision-based detection"    body="No browser extension, no app integrations. The AI reads your screen exactly as you see it." />
            <Feature icon="⌨️"  title="Typing challenge dismissal" body="Can't click away from the warning. You have to type a full sentence to get back in." />
            <Feature icon="🧠"  title="Session memory"            body="Onitry builds notes across checks so it understands your session context, not just the last screenshot." />
            <Feature icon="📈"  title="Adaptive intervals"        body="Checks slow down when you're in flow, snap back to fast when you go off task." />
            <Feature icon="🔒"  title="Private by design"         body="Screenshots go directly to the AI API and are never stored. No keylogging." />
            <Feature icon="💸"  title="Pennies per hour"          body="Runs on a lightweight AI model for as little as $0.09/hr in API costs. Bring your own key." />
          </div>
        </div>
      </section>

      {/* Pricing */}
      <section className={styles.section} style={{ background: "var(--bg2)" }} id="pricing">
        <div className={styles.inner}>
          <p className={styles.sectionLabel}>Pricing</p>
          <h2 className={styles.sectionTitle}>One plan. No fluff.</h2>
          <p className={styles.sectionSub}>You bring your own AI API key — the usage costs are yours to control.</p>
          <div className={styles.pricingCard}>
            <div className={styles.pricingName}>Pro</div>
            <div className={styles.price}><sup>$</sup>19</div>
            <div className={styles.period}>per month</div>
            <div className={styles.pricingDivider} />
            <ul className={styles.pricingList}>
              {[
                "Full macOS app — menu bar + GUI",
                "Unlimited monitoring sessions",
                "Choose your AI model tier",
                "Adjustable screenshot resolution",
                "Typing-challenge off-task dismissal",
                "Session memory & activity log",
                "Soft or hard interrupt — AI decides",
                "Your own AI API key (pay what you use)",
              ].map((f) => <li key={f}>{f}</li>)}
            </ul>
            <button
              className={styles.pricingCta}
              onClick={() => alert("Coming soon — thanks for your interest!")}
            >
              Get Onitry
            </button>
            <p className={styles.pricingNote}>Cancel anytime · macOS 13+ required</p>
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
