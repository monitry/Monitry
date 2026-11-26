import styles from "./ClassWatch.module.css";
import { ANTHROPIC_CONSOLE_URL, ISSUES_URL } from "../site.js";

function scrollToId(id) {
  document.getElementById(id)?.scrollIntoView({ behavior: "smooth" });
}

function ExampleOutput() {
  return (
    <figure className={styles.example}>
      <div className={styles.window}>
        <div className={styles.titlebar} aria-hidden="true">
          <span className={styles.dot} style={{ background: "#ff5f57" }} />
          <span className={styles.dot} style={{ background: "#febc2e" }} />
          <span className={styles.dot} style={{ background: "#28c840" }} />
          <span className={styles.windowTitle}>terminal</span>
        </div>
        <div className={styles.windowBody}>
          <pre className={styles.log}>
            <span>$ python room_cli.py --task &quot;lab assignment&quot;</span>
            {"\n"}
            <span className={styles.logOn}>[10:14:32] screen-1 (ON TASK): Writing code in an editor</span>
            {"\n"}
            <span className={styles.logOff}>[10:14:32] screen-2 (OFF TASK): Watching a video</span>
            {"\n"}
            <span className={styles.logOn}>[10:14:32] screen-3 (ON TASK): Reading a PDF</span>
          </pre>
        </div>
      </div>
      <figcaption>Example output, written by hand to show the format. Not a real session.</figcaption>
    </figure>
  );
}

export default function ClassWatch() {
  return (
    <main className={styles.page}>
      {/* Hero */}
      <section className={styles.hero}>
        <div className={styles.badges}>
          <span className={styles.badgeWarn}>Experimental</span>
          <span className={styles.badge}>macOS &middot; camera &middot; terminal only</span>
        </div>
        <h1>ClassWatch</h1>
        <p className={styles.lead}>
          Point a camera at a room. ClassWatch finds the laptop and monitor screens it can see, asks Claude
          what each one is showing, and keeps a log and a report. Free, with your own Anthropic API key.
        </p>
        <div className={styles.cta}>
          <button type="button" className={styles.btnPrimary} onClick={() => scrollToId("requirements")}>
            What you need
          </button>
          <a className={styles.btnOutline} href="#/docs">
            Setup basics in the docs
          </a>
        </div>
      </section>

      {/* Experimental + consent */}
      <section className={styles.section}>
        <div className={styles.inner}>
          <p className={styles.sectionLabel}>Read this first</p>
          <h2 className={styles.sectionTitle}>Experimental, and it watches people</h2>

          <div className={styles.callout}>
            <h3>It is experimental</h3>
            <p>
              ClassWatch is unfinished. Its automated tests use stand-ins for the camera and the AI. We have
              not measured how accurate it is on real classroom footage, so we make no claim about that. It
              will miss screens, mix them up and misread them. Do not use it as evidence about anyone.
            </p>
          </div>

          <div className={styles.callout}>
            <h3>Get consent before you point it at people</h3>
            <p>
              Screens show what people are doing, and ClassWatch sends cropped photos of them to Anthropic.
              Only use it where the people in the room know and agree, and where your school, workplace and
              local rules allow cameras and this kind of monitoring. You are responsible for that. It keeps
              notes and a report about each screen in <code>data/room</code> on your Mac. See the{" "}
              <a href="#/privacy">Privacy</a> and <a href="#/terms">Terms</a> pages.
            </p>
          </div>
        </div>
      </section>

      {/* What it does */}
      <section className={`${styles.section} ${styles.alt}`}>
        <div className={styles.inner}>
          <p className={styles.sectionLabel}>What it does</p>
          <h2 className={styles.sectionTitle}>One camera, every screen it can find</h2>
          <ol className={styles.steps}>
            <li className={styles.step}>
              <span className={styles.stepNum}>01</span>
              <h3>Find screens</h3>
              <p>
                A detection model running on your Mac looks for laptops and monitors in each camera frame. A
                screen it does not detect is not logged.
              </p>
            </li>
            <li className={styles.step}>
              <span className={styles.stepNum}>02</span>
              <h3>Keep track of them</h3>
              <p>
                Each screen gets an ID such as <code>screen-1</code>, matched between captures by where it
                sits in the frame. If a laptop moves a lot or is swapped, IDs can get mixed up.
              </p>
            </li>
            <li className={styles.step}>
              <span className={styles.stepNum}>03</span>
              <h3>Describe each one</h3>
              <p>
                Claude Haiku 4.5 describes each screen from a cropped photo. With <code>--task</code> it also
                says whether the screen looks on or off task, using one shared task for every screen.
              </p>
            </li>
          </ol>
          <ul className={styles.plainList}>
            <li>It is passive: no popups, no spoken reminders, nothing shown on the watched computers.</li>
            <li>
              Nothing is installed on the watched computers. Everything runs from the machine with the
              camera.
            </li>
            <li>Press Ctrl+C to stop. It then writes a Markdown report with a timeline for each screen.</li>
            <li>It is a terminal tool only. There is no window and no live view.</li>
          </ul>
          <ExampleOutput />
        </div>
      </section>

      {/* Requirements */}
      <section className={styles.section} id="requirements">
        <div className={styles.inner}>
          <p className={styles.sectionLabel}>Requirements</p>
          <h2 className={styles.sectionTitle}>What you need first</h2>
          <ul className={styles.plainList}>
            <li>
              <strong>A Mac, set up for Full Focus.</strong> ClassWatch uses the same base setup (see the{" "}
              <a href="#/docs">docs</a>).
            </li>
            <li>
              <strong>A camera</strong>, and macOS Camera permission for the terminal you run it from.
            </li>
            <li>
              <strong>The extra packages.</strong> <code>requirements-room.txt</code> adds{" "}
              <code>ultralytics</code>, which pulls in PyTorch. It is a large install.
            </li>
            <li>
              <strong>An internet connection on first run.</strong> The detection model weights are
              downloaded the first time you start it.
            </li>
            <li>
              <strong>
                Your key in the <code>ANTHROPIC_API_KEY</code> environment variable.
              </strong>{" "}
              ClassWatch does not read the key you saved in the Keychain for Full Focus, and it exits at
              once if the variable is missing.
            </li>
          </ul>

          <h3 className={styles.subTitle}>Run it</h3>
          <pre className={styles.cmd}>
{`pip install -r requirements-room.txt
export ANTHROPIC_API_KEY=your_key_here
python room_cli.py --task "working on the lab assignment" --interval 20`}
          </pre>
          <p className={styles.muted}>All options are optional:</p>
          <ul className={styles.plainList}>
            <li>
              <code>--camera N</code>: camera index (default 0)
            </li>
            <li>
              <code>--interval S</code>: seconds between captures (default 15)
            </li>
            <li>
              <code>--conf X</code>: detection confidence threshold (default 0.25)
            </li>
            <li>
              <code>--task &quot;...&quot;</code>: one shared task for every screen. Leave it out to log
              activity only, with no on or off task judgment.
            </li>
            <li>
              <code>--report-path FILE</code>: where the report goes (default{" "}
              <code>data/room/report.md</code>)
            </li>
            <li>
              <code>--max-cycles N</code>: stop after N captures (default: run until Ctrl+C)
            </li>
          </ul>
        </div>
      </section>

      {/* Cost */}
      <section className={`${styles.section} ${styles.alt}`}>
        <div className={styles.inner}>
          <p className={styles.sectionLabel}>Cost</p>
          <h2 className={styles.sectionTitle}>Roughly $0.25 to $0.40 per screen per hour</h2>
          <p className={styles.sectionSub}>
            This is an estimate, not a measurement. At the default 15 seconds that is about 240 checks per
            screen per hour, each a small image plus a little text sent to Haiku 4.5 on your key. More
            screens or a shorter interval cost proportionally more. A longer interval costs less. ClassWatch
            prints the session total when it stops.
          </p>
          <p className={styles.sectionSub}>
            You pay Anthropic directly. Set a monthly spending limit in the{" "}
            <a href={ANTHROPIC_CONSOLE_URL} target="_blank" rel="noreferrer">
              Anthropic Console
            </a>{" "}
            before you start.
          </p>
        </div>
      </section>

      {/* Sent and kept */}
      <section className={styles.section}>
        <div className={styles.inner}>
          <p className={styles.sectionLabel}>Data</p>
          <h2 className={styles.sectionTitle}>What is sent and what is kept</h2>
          <ul className={styles.plainList}>
            <li>
              Camera frames are held in memory and are not saved. A cropped image of each detected screen
              goes to Anthropic, with the task, that screen&rsquo;s recent log lines and its notes.
            </li>
            <li>
              Your Mac keeps one text log per screen and the report, in <code>data/room</code>. They stay
              between runs. Delete that folder to start clean.
            </li>
            <li>
              What Anthropic does with the images is covered by Anthropic&rsquo;s policy. Details are on the{" "}
              <a href="#/privacy">Privacy</a> page.
            </li>
          </ul>
          <p className={styles.muted}>
            Found a problem? Open an issue on{" "}
            <a href={ISSUES_URL} target="_blank" rel="noreferrer">
              GitHub
            </a>
            . Leave out images of people.
          </p>
        </div>
      </section>

      <footer className={styles.footer}>
        <div className={styles.footerInner}>
          <span className={styles.footerLogo}>
            Onit<span>ry</span>
          </span>
          <span>Free. Bring your own Anthropic API key.</span>
          <span>
            <a href="#/privacy">Privacy</a> &middot; <a href="#/terms">Terms</a> &middot;{" "}
            <a href="#/about">About</a>
          </span>
        </div>
      </footer>
    </main>
  );
}
