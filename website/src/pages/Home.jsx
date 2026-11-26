import styles from "./Home.module.css";
import { ANTHROPIC_CONSOLE_URL, ANTHROPIC_PRIVACY_URL, ISSUES_URL } from "../site.js";

// ── Shared pieces (App.jsx renders SiteFooter under every page) ─────────────

export function SiteFooter() {
  return (
    <footer className={styles.footer}>
      <div className={styles.footerInner}>
        <span className={styles.footerLogo}>Onit<span>ry</span></span>
        <span>© 2026 Onitry</span>
        <nav aria-label="Footer" className={styles.footerLinks}>
          <a href="#/docs">Docs</a>
          <a href="#/about">About</a>
          <a href="#/privacy">Privacy</a>
          <a href="#/terms">Terms</a>
          <a href={ISSUES_URL} target="_blank" rel="noopener noreferrer">GitHub issues</a>
        </nav>
      </div>
    </footer>
  );
}

function Step({ num, title, children }) {
  return (
    <div className={styles.step}>
      <div className={styles.stepNum}>{num}</div>
      <h3>{title}</h3>
      <p>{children}</p>
    </div>
  );
}

function Fact({ title, children }) {
  return (
    <div className={styles.fact}>
      <h3>{title}</h3>
      {children}
    </div>
  );
}

// ── Page ───────────────────────────────────────────────────────────────────

export default function Home() {
  return (
    <main>
      {/* Hero */}
      <section className={`${styles.hero} ${styles.heroHome}`}>
        <div className={styles.badge}>
          <span className={styles.badgeDot} />
          Onitry · macOS · focus monitor
        </div>
        <h1>Tell it your task.<br /><em>It notices when you drift.</em></h1>
        <p>
          Onitry is a Mac app that looks at your screen every so often, compares it with the task you typed,
          and interrupts you when you are off it.
        </p>
        <p className={styles.offerLine}>Free. Bring your own Anthropic API key.</p>
        <div className={styles.heroCta}>
          <a className={styles.btnPrimary} href="#/docs/install">Install guide</a>
          <a className={styles.btnOutline} href="#/fullfocus">See Full Focus</a>
        </div>
        <span className={styles.heroNote}>
          macOS only. For now it is a terminal install: you download the code and run it with Python.
          It suits people who are comfortable in a terminal.
        </span>
      </section>

      {/* How it works */}
      <section className={`${styles.section} ${styles.altBg}`} id="how-it-works">
        <div className={styles.inner}>
          <p className={styles.sectionLabel}>How it works</p>
          <h2 className={styles.sectionTitle}>Three steps</h2>
          <p className={styles.sectionSub}>
            Each check is one screenshot, sent to Claude with your own key.
          </p>
          <div className={styles.steps}>
            <Step num="01" title="Type your task">
              Say what you are working on and press Start Monitoring. The first check runs about 5 seconds later.
            </Step>
            <Step num="02" title="It checks your screen">
              Claude gets a JPEG of your main display, your task and its own short notes. Checks start 10 seconds
              apart and slow to roughly every 2 minutes while you are on task. They speed up the moment you are not,
              and they pause after 5 minutes without mouse or keyboard input.
            </Step>
            <Step num="03" title="It calls you back">
              If Claude decides you are off task, you get a popup that asks you to type a sentence, or a quiet
              notification. If it got it wrong, you can say so.
            </Step>
          </div>
        </div>
      </section>

      {/* Products */}
      <section className={styles.section} id="products">
        <div className={styles.inner}>
          <p className={styles.sectionLabel}>Products</p>
          <h2 className={styles.sectionTitle}>One for your screen, one for a room</h2>
          <p className={styles.sectionSub}>
            Full Focus is the product Onitry launches with. ClassWatch is an experiment that shares the same engine.
          </p>

          <div className={styles.cardGrid}>
            <article className={`${styles.card} ${styles.cardFeatured}`}>
              <span className={styles.cardTag}>Launch product</span>
              <h3>Full Focus</h3>
              <p className={styles.cardLead}>Watches your own screen and interrupts you when you drift.</p>
              <ul className={styles.cardList}>
                <li>A popup with a typing challenge, or a quiet notification banner</li>
                <li>Checks that adapt: slower while you work, faster when you drift</li>
                <li>No checks while you are away from the keyboard</li>
                <li>A summary at the end of each session, with the percent of time on task</li>
              </ul>
              <a className={`${styles.btnPrimary} ${styles.cardCta}`} href="#/fullfocus">Full Focus details</a>
            </article>

            <article className={styles.card}>
              <span className={`${styles.cardTag} ${styles.cardTagExp}`}>Experimental</span>
              <h3>ClassWatch</h3>
              <p className={styles.cardLead}>Points a camera at a room and logs what each screen in view is showing.</p>
              <ul className={`${styles.cardList} ${styles.cardListWarn}`}>
                <li>Command line only. Needs a camera and a large extra install (it pulls in PyTorch)</li>
                <li>Passive: no popups. It writes a report when you press Ctrl+C</li>
                <li>Costs more than Full Focus: roughly $0.25 to $0.40 per screen-hour (an estimate)</li>
                <li>Unit-tested with mocks only. We have no evidence yet of how accurate it is on real classroom footage</li>
                <li>It observes other people. Get their consent and follow the rules where you are</li>
              </ul>
              <a className={`${styles.btnOutline} ${styles.cardCta}`} href="#/classwatch">About ClassWatch</a>
            </article>
          </div>
        </div>
      </section>

      {/* Cost */}
      <section className={`${styles.section} ${styles.altBg}`} id="cost">
        <div className={styles.inner}>
          <p className={styles.sectionLabel}>What it costs</p>
          <h2 className={styles.sectionTitle}>The app is free. The API usage is yours.</h2>
          <div className={styles.factGrid}>
            <Fact title="Onitry">
              <p>Nothing to buy and nothing to sign up for. There is no Onitry server.</p>
            </Fact>
            <Fact title="Anthropic usage">
              <p>
                Full Focus sends each check to Claude Haiku 4.5 on your own key. We estimate about $0.06 to $0.20
                per hour, depending on how often you drift. A calm hour is about 36 checks, roughly $0.09.
              </p>
              <p>This is an estimate, not a measurement.</p>
            </Fact>
            <Fact title="Keeping it in check">
              <p>
                Set a spending limit in the{" "}
                <a className={styles.textLink} href={ANTHROPIC_CONSOLE_URL} target="_blank" rel="noopener noreferrer">
                  Anthropic console
                </a>
                . The app also shows a running session cost while it works.
              </p>
            </Fact>
          </div>
          <div className={styles.linkRow}>
            <a className={styles.textLink} href="#/docs/costs">See the cost arithmetic in the docs</a>
          </div>
        </div>
      </section>

      {/* Privacy */}
      <section className={styles.section} id="privacy-summary">
        <div className={styles.inner}>
          <p className={styles.sectionLabel}>Privacy</p>
          <h2 className={styles.sectionTitle}>What leaves your Mac, and what stays</h2>
          <div className={styles.factGrid}>
            <Fact title="Sent to Anthropic">
              <p>
                With each check: one JPEG of your main display, your task text, the last 10 lines of the activity
                log and the running notes. They go from your Mac to Anthropic using your key.
              </p>
            </Fact>
            <Fact title="Stored on your Mac">
              <p>
                Plain-text files in the app&rsquo;s data folder: short descriptions of what you were doing, status,
                settings (including recent task names) and a pairing code. No screenshot is ever written to disk.
                Onitry does not log keystrokes.
              </p>
            </Fact>
            <Fact title="Anthropic&rsquo;s side">
              <p>
                Anthropic&rsquo;s own retention policy applies to what it receives, and we do not control it. Read{" "}
                <a className={styles.textLink} href={ANTHROPIC_PRIVACY_URL} target="_blank" rel="noopener noreferrer">
                  their privacy policy
                </a>
                .
              </p>
            </Fact>
          </div>
          <div className={styles.linkRow}>
            <a className={styles.textLink} href="#/privacy">Read the full privacy page</a>
          </div>
        </div>
      </section>

      {/* FAQ */}
      <section className={`${styles.section} ${styles.altBg}`} id="faq">
        <div className={styles.inner}>
          <p className={styles.sectionLabel}>Questions</p>
          <h2 className={styles.sectionTitle}>Plain answers</h2>
          <div className={styles.faq}>
            <h3>Is it really free?</h3>
            <p>
              Yes. You pay Onitry nothing, and there is no account to create. The only money involved is
              what you pay Anthropic for your own API usage, which we estimate at $0.06 to $0.20 per hour for Full
              Focus.
            </p>
            <h3>Why a terminal install?</h3>
            <p>
              There is no installer or .app yet. You need a Mac, Python 3.10 or newer with Tk, and an Anthropic API
              key. macOS will ask for Screen Recording permission for the app that runs Python, usually your terminal.
              The <a className={styles.textLink} href="#/docs/install">install guide</a> has the steps.
            </p>
            <h3>Does it run on Windows or Linux?</h3>
            <p>No. It is macOS only: the alerts use macOS tools (osascript and say).</p>
            <h3>Something broke. Where do I say so?</h3>
            <p>
              Open an issue on{" "}
              <a className={styles.textLink} href={ISSUES_URL} target="_blank" rel="noopener noreferrer">GitHub</a>.
            </p>
          </div>
        </div>
      </section>

    </main>
  );
}
