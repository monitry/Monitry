import styles from "./Home.module.css";

function ProductCard({ eyebrow, title, body, bullets, cta, onClick }) {
  return (
    <div className={styles.pricingCard}>
      <div className={styles.pricingName}>{eyebrow}</div>
      <div className={styles.price} style={{ fontSize: 32 }}>{title}</div>
      <div className={styles.period}>{body}</div>
      <div className={styles.pricingDivider} />
      <ul className={styles.pricingList}>
        {bullets.map((b) => <li key={b}>{b}</li>)}
      </ul>
      <button className={styles.pricingCta} onClick={onClick}>{cta}</button>
    </div>
  );
}

export default function Home({ onNav }) {
  return (
    <main>
      {/* Hero */}
      <section className={styles.hero}>
        <div className={styles.badge}>
          <span className={styles.badgeDot} />
          macOS · AI-powered focus tools
        </div>
        <h1>Two ways to<br /><em>stay on task.</em></h1>
        <p>Onitry builds AI-powered focus monitors — point one at your own screen, or at a whole room.</p>
      </section>

      {/* Products */}
      <section className={styles.section} style={{ background: "var(--bg2)" }} id="products">
        <div className={styles.inner}>
          <p className={styles.sectionLabel}>Products</p>
          <h2 className={styles.sectionTitle}>Pick your setup</h2>
          <p className={styles.sectionSub}>Both are built on the same core monitoring engine, aimed at two different problems.</p>

          <div className={styles.pricingGrid}>
            <ProductCard
              eyebrow="Personal"
              title="Full Focus"
              body="Watches your own screen"
              bullets={[
                "Screenshots your screen and calls you out when you drift",
                "Hard interrupts with a typing-challenge dismissal",
                "BYOK from $30 one-time, or a free managed plan",
              ]}
              cta="Explore Full Focus"
              onClick={() => onNav?.("fullfocus")}
            />
            <ProductCard
              eyebrow="Room"
              title="ClassWatch"
              body="Watches a room via camera"
              bullets={[
                "Tracks every laptop/monitor a camera can see at once",
                "Passive observer — no popups, just a report",
                "Free, open source, command-line",
              ]}
              cta="Explore ClassWatch"
              onClick={() => onNav?.("classwatch")}
            />
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
