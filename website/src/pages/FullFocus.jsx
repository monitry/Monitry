import styles from "./Home.module.css";
import { ANTHROPIC_CONSOLE_URL } from "../site.js";

// ── Subcomponents ──────────────────────────────────────────────────────────

// An illustration of the app window, not a screenshot. Marked as an image so
// screen readers read the caption instead of the mock log lines.
function AppPreview() {
  return (
    <figure className={styles.previewWrap}>
      <div
        className={styles.window}
        role="img"
        aria-label="Illustration of the Full Focus window: a task box, a Stop Monitoring button, an ON TASK status, a session cost and a log of checks."
      >
        <div className={styles.titlebar}>
          <span className={styles.dot} style={{ background: "#ff5f57" }} />
          <span className={styles.dot} style={{ background: "#febc2e" }} />
          <span className={styles.dot} style={{ background: "#28c840" }} />
          <span className={styles.windowTitle}>Full Focus</span>
        </div>
        <div className={styles.windowBody} aria-hidden="true">
          <Row label="Task:" value="Finish the linear algebra coursework" />
          <div className={styles.divider} />
          <div className={styles.startBtn}>Stop Monitoring</div>
          <div className={styles.statusOn}>ON TASK</div>
          <p className={styles.previewCost}>Session cost: $0.004</p>
          <div className={styles.log}>
            <p className={styles.logOn}>[10:12:58] ON TASK: Writing Python implementation &nbsp;(next in 38s)</p>
            <p className={styles.logOff}>[10:13:41] OFF TASK: Browsing YouTube &nbsp;(next in 12s)</p>
            <p className={styles.logOn}>[10:13:54] ON TASK: Reading lecture notes &nbsp;(next in 24s)</p>
          </div>
        </div>
      </div>
      <figcaption className={styles.caption}>
        An illustration, not a screenshot. On Haiku 4.5, a check costs a fraction of a cent: we estimate about
        $0.06 to $0.20 per hour on your own key.
      </figcaption>
    </figure>
  );
}

function Row({ label, value }) {
  return (
    <div className={styles.row}>
      <span className={styles.rowLabel}>{label}</span>
      <div className={styles.field}>{value}</div>
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

function Feature({ title, body }) {
  return (
    <div className={styles.feature}>
      <h3>{title}</h3>
      <p>{body}</p>
    </div>
  );
}

function scrollToId(id) {
  document.getElementById(id)?.scrollIntoView({ behavior: "smooth" });
}

// ── Page ───────────────────────────────────────────────────────────────────

export default function FullFocus() {
  return (
    <main>
      {/* Hero */}
      <section className={`${styles.hero} ${styles.heroHome}`}>
        <div className={styles.badge}>
          <span className={styles.badgeDot} />
          Onitry · Full Focus · macOS
        </div>
        <h1>Stay on task.<br /><em>It notices when you don&rsquo;t.</em></h1>
        <p>
          Full Focus compares your screen with the task you typed and interrupts you when you drift.
        </p>
        <p className={styles.offerLine}>Free. Bring your own Anthropic API key.</p>
        <div className={styles.heroCta}>
          <a className={styles.btnPrimary} href="#/docs/install">Install guide</a>
          <button type="button" className={styles.btnOutline} onClick={() => scrollToId("how-it-works")}>
            See how it works
          </button>
        </div>
        <span className={styles.heroNote}>
          macOS only. For now it is a terminal install, so it suits people who are comfortable in a terminal.
        </span>
        <AppPreview />
      </section>

      {/* How it works */}
      <section className={`${styles.section} ${styles.altBg}`} id="how-it-works">
        <div className={styles.inner}>
          <p className={styles.sectionLabel}>How it works</p>
          <h2 className={styles.sectionTitle}>Type a task, then get on with it</h2>
          <p className={styles.sectionSub}>
            Each check is one screenshot, sent to Claude with your own key.
          </p>
          <div className={styles.steps}>
            <Step
              num="01"
              title="Tell it your task"
              body="Type what you are working on, or pick a recent task, and press Start Monitoring."
            />
            <Step
              num="02"
              title="Claude checks your screen"
              body="Each check sends a JPEG of your main display, your task, the last 10 lines of the activity log and Claude's own short notes. Claude replies with whether you are on task, what you seem to be doing, and whether to interrupt."
            />
            <Step
              num="03"
              title="You get called back"
              body="If you are off task, you get one of two interruptions, below. If Claude got it wrong, you can tell it."
            />
          </div>
        </div>
      </section>

      {/* Interrupts */}
      <section className={styles.section} id="interrupts">
        <div className={styles.inner}>
          <p className={styles.sectionLabel}>Interruptions</p>
          <h2 className={styles.sectionTitle}>Two ways to be interrupted</h2>
          <p className={styles.sectionSub}>
            Claude decides which one fits each check.
          </p>
          <div className={styles.cardGrid}>
            <article className={`${styles.card} ${styles.cardFeatured}`}>
              <h3>Hard interrupt</h3>
              <p className={styles.cardLead}>A red popup that is hard to ignore, but not impossible to close.</p>
              <ul className={styles.cardList}>
                <li>It sits on top of your other windows and reads the reminder aloud.</li>
                <li>Checks pause while it is open.</li>
                <li>
                  &ldquo;Back to work&rdquo; only works once you have typed one of ten fixed sentences (14 to 18
                  words each) exactly.
                </li>
                <li>It closes by itself after 90 seconds.</li>
                <li>
                  &ldquo;Not actually off task?&rdquo; closes it and asks what you were really doing. Your answer is
                  added to the activity log that Claude reads on later checks.
                </li>
                <li>
                  After it closes there is a grace period with no checks: 60 seconds by default, 0 to 300 in
                  Configure.
                </li>
              </ul>
            </article>

            <article className={styles.card}>
              <h3>Soft banner</h3>
              <p className={styles.cardLead}>A nudge, for when a popup would be too much.</p>
              <ul className={styles.cardList}>
                <li>A silent macOS notification with Claude&rsquo;s reminder.</li>
                <li>No sound, no popup, nothing to type.</li>
                <li>Checks carry on as normal.</li>
              </ul>
            </article>
          </div>
        </div>
      </section>

      {/* Features */}
      <section className={`${styles.section} ${styles.altBg}`} id="features">
        <div className={styles.inner}>
          <p className={styles.sectionLabel}>Details</p>
          <h2 className={styles.sectionTitle}>Fewer checks when you are fine</h2>
          <p className={styles.sectionSub}>Every check costs a little on your key, so Full Focus avoids the ones it can.</p>
          <div className={styles.features}>
            <Feature
              title="Adaptive checking"
              body="The first check is about 5 seconds after you start. After that the gap starts at 10 seconds and grows by 10 seconds per check while you stay on task, up to 120, with random jitter. The moment you go off task it drops back to 10."
            />
            <Feature
              title="Idle skipping"
              body="After 5 minutes with no mouse or keyboard input, checks are skipped and the status reads AWAY. They resume when you come back. It reads macOS's idle timer, not your keystrokes."
            />
            <Feature
              title="Pause without quitting"
              body="Pause 10m stops checks for ten minutes. Press it again to resume early."
            />
            <Feature
              title="Session notes"
              body="Claude keeps a few short notes during a session and sees the last 10 lines of an activity log, so it judges against context rather than one screenshot. The log is overwritten when you start the next session."
            />
            <Feature
              title="Image detail"
              body="In Configure, pick a screenshot width (1280, 800, 512 or 320 px) and a JPEG quality (20 to 100). Defaults are 1280 and 75. Lower is cheaper and shows less."
            />
            <Feature
              title="Session summary"
              body="When you stop: how long you monitored, the percent of time on task, a timeline bar, the number of interruptions and what the session cost."
            />
          </div>
        </div>
      </section>

      {/* Timecheck */}
      <section className={styles.section} id="timecheck">
        <div className={styles.inner}>
          <p className={styles.sectionLabel}>Optional companion</p>
          <h2 className={styles.sectionTitle}>Works with Timecheck</h2>
          <div className={styles.factGrid}>
            <Fact2 title="What it is">
              Timecheck is a separate Chrome extension: a planner with focus blocks, a distraction gate and a
              journal. It is a separate download and Full Focus does not need it.
            </Fact2>
            <Fact2 title="What the link does">
              Once paired, starting a focus block in the browser starts Full Focus on that task, and the on-task
              or off-task verdict shows up in the browser. The planner&rsquo;s task context is added to what is sent
              with each check.
            </Fact2>
            <Fact2 title="How it connects">
              Over a connection that stays on your computer (127.0.0.1). It needs a pairing code that Full Focus
              shows in Configure. The extension can also ask for a weekly review, which is one more request on
              your key; the week&rsquo;s planner stats go to Anthropic with it.
            </Fact2>
          </div>
        </div>
      </section>

      {/* Offer */}
      <section className={`${styles.section} ${styles.altBg}`} id="cost">
        <div className={styles.inner}>
          <p className={styles.sectionLabel}>What it costs</p>
          <h2 className={styles.sectionTitle}>Free. Bring your own key.</h2>
          <article className={`${styles.card} ${styles.cardFeatured} ${styles.cardSingle}`}>
            <span className={styles.cardTag}>Free</span>
            <h3>Your Anthropic API key</h3>
            <p className={styles.cardLead}>
              Full Focus costs nothing. You pay Anthropic directly for the checks it makes with your key.
            </p>
            <ul className={styles.cardList}>
              <li>Nothing to buy, no account to create, and no Onitry server.</li>
              <li>About $0.06 to $0.20 per hour on Haiku 4.5. That is an estimate, not a measurement.</li>
              <li>
                <span>
                  Set a spending limit in the{" "}
                  <a className={styles.textLink} href={ANTHROPIC_CONSOLE_URL} target="_blank" rel="noopener noreferrer">
                    Anthropic console
                  </a>
                  .
                </span>
              </li>
              <li>The app shows a running session cost, and the summary shows the total.</li>
              <li>macOS only, with a terminal install for now.</li>
            </ul>
            <div className={styles.cardActions}>
              <a className={styles.btnPrimary} href="#/docs/install">Install guide</a>
              <a className={styles.textLink} href="#/docs/costs">See the cost arithmetic</a>
            </div>
          </article>
        </div>
      </section>

    </main>
  );
}

function Fact2({ title, children }) {
  return (
    <div className={styles.fact}>
      <h3>{title}</h3>
      <p>{children}</p>
    </div>
  );
}
