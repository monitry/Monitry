import styles from "./Legal.module.css";
import { ANTHROPIC_CONSOLE_URL, ANTHROPIC_PRIVACY_URL, APP_DATA_FOLDER, ISSUES_URL, LAST_UPDATED } from "../site.js";

export default function Privacy() {
  return (
    <main className={styles.page}>
      <div className={styles.inner}>
        <p className={styles.label}>Legal</p>
        <h1 className={styles.title}>Privacy</h1>
        <p className={styles.meta}>Last updated {LAST_UPDATED}</p>

        <p className={styles.notice}>
          This page describes in plain language what Onitry does with your data. It was written from the
          code. It is a description, not a legal document and not legal advice.
        </p>

        <section className={styles.section}>
          <h2>The short version</h2>
          <ul>
            <li>
              Onitry has no accounts and no server of its own. The app never contacts an Onitry server. It
              talks to Anthropic, using your own API key, and to a browser extension on your own computer if
              you use one.
            </li>
            <li>
              Each check sends a screenshot of your main screen to Anthropic. What Anthropic does with it is
              governed by Anthropic&rsquo;s policy, not ours.
            </li>
            <li>
              Onitry keeps a few small text files on your Mac, in a folder called <code>data</code>. No
              screenshot is ever written to disk. Nothing records your keystrokes.
            </li>
            <li>This website has no analytics, no cookies and no accounts.</li>
          </ul>
        </section>

        <section className={styles.section}>
          <h2>Full Focus</h2>

          <h3>What is sent to Anthropic</h3>
          <p>
            While monitoring is running, Onitry makes a check every 10 to 120 seconds. Each check sends this
            to Anthropic, using your API key:
          </p>
          <ul>
            <li>
              One JPEG screenshot of your <strong>primary display</strong> (1280 pixels wide and JPEG quality
              75 by default; both are settings). Other displays are not captured.
            </li>
            <li>The task text you typed.</li>
            <li>The last 10 lines of the session&rsquo;s activity log.</li>
            <li>Onitry&rsquo;s own short running notes from earlier checks in the session.</li>
          </ul>
          <p>
            If a focus block was started from the Timecheck browser extension, the task text also includes
            the context the extension sent (for example, what is due).
          </p>
          <p>
            The screenshot shows everything visible on that display at that moment: other apps, messages,
            names, anything on screen. Pause or stop monitoring before you open something you do not want
            sent. Checks are skipped while you are paused, during the grace period after a popup, and after 5
            minutes without mouse or keyboard input.
          </p>
          <p>
            Two smaller things also use your key. The optional menu bar app has an &ldquo;Ask
            Claude&rdquo; box that sends your question, your current task and the last 10 log lines. And if
            you use the Timecheck extension&rsquo;s weekly review, Onitry forwards the week&rsquo;s numbers
            that the extension sends it to Anthropic.
          </p>

          <h3>What Anthropic does with it</h3>
          <p>
            Once data reaches Anthropic, Anthropic&rsquo;s own policies apply, including how long they keep
            it and what it may be used for. Onitry does not control that and cannot promise anything on
            Anthropic&rsquo;s behalf. Read{" "}
            <a href={ANTHROPIC_PRIVACY_URL} target="_blank" rel="noreferrer">
              Anthropic&rsquo;s privacy policy
            </a>{" "}
            and the terms for your own API account before you start.
          </p>

          <h3>What stays on your Mac</h3>
          <p>
            Onitry writes these files to the <code>data</code> folder inside the Onitry folder you cloned, or,
            in the Mac app, to <code>{APP_DATA_FOLDER}</code>. They are plain text, not encrypted:
          </p>
          <ul>
            <li>
              <code>data/context.txt</code>: the task and start time, then one line per check describing
              what you appeared to be doing (off-task lines are tagged), plus any correction you submit.
              Overwritten each time you start a session.
            </li>
            <li>
              <code>data/status.json</code>: the current status, task, latest activity description and
              session cost. The menu bar app reads it.
            </li>
            <li>
              <code>data/settings.json</code>: your settings (image size, JPEG quality, grace period) and up
              to 8 recent task names.
            </li>
            <li>
              <code>data/bridge_token</code>: the pairing code for the browser extension.
            </li>
          </ul>
          <p>
            Task names and activity descriptions can be sensitive on their own (&ldquo;looking at job
            listings&rdquo;). Anyone who can open that folder can read them. Do not paste them into a public
            bug report without checking.
          </p>

          <h3>What Onitry does not do</h3>
          <ul>
            <li>
              <strong>No screenshot is written to disk.</strong> It is captured, compressed in memory, sent,
              and dropped.
            </li>
            <li>
              <strong>No keylogging.</strong> Idle detection only asks macOS how long it has been since the
              last mouse or keyboard input. It never sees what you typed. The typing challenge reads only the
              text box in its own popup, to compare it with the sentence, and does not save it.
            </li>
            <li>No audio is recorded and Full Focus does not use the camera.</li>
            <li>No analytics, crash reports or telemetry are sent anywhere.</li>
          </ul>

          <h3>Your API key</h3>
          <p>
            When you use the app&rsquo;s Set Key button, your Anthropic key is stored in the macOS Keychain
            (service name <code>onitry</code>). The terminal tools and ClassWatch read it from the{" "}
            <code>ANTHROPIC_API_KEY</code> environment variable instead. It is not written to the{" "}
            <code>data</code> folder. The key is sent to Anthropic with each request, which is how they know
            the request is yours.
          </p>

          <h3>The browser bridge</h3>
          <p>
            While the Full Focus window is open, it runs a small server on your own Mac at{" "}
            <code>127.0.0.1</code>, port 47323. It is not reachable from other computers. Every request
            except a ping needs the pairing code, and requests from web pages are refused; only the Timecheck
            extension is accepted. Through it the extension can start, pause and stop monitoring and read the
            current status: on task or off task, the task, the latest activity description, time on and off
            task, and the interruption count.
          </p>
          <p>
            Timecheck is a separate download with its own behavior. This page covers Onitry only, so check the
            extension&rsquo;s own description for what it stores.
          </p>
        </section>

        <section className={styles.section}>
          <h2>ClassWatch (experimental)</h2>
          <p>
            ClassWatch reads frames from a camera. Frames are held in memory and are not saved. A detection
            model that runs on your Mac finds laptops and monitors in each frame. For each one it found,
            ClassWatch sends Anthropic a cropped JPEG (at most 800 pixels wide), the task, the last 10 lines
            of that screen&rsquo;s log and its running notes, using your key. The crop can include part of
            whatever is beside the screen. Anthropic&rsquo;s policy, linked above, governs what happens next.
          </p>
          <p>
            On your Mac it writes one text log per screen (<code>data/room/screen-1.txt</code> and so on) and
            a Markdown report when you press Ctrl+C (<code>data/room/report.md</code> unless you chose
            another path). The per-screen logs are kept between runs and added to, so delete them to start
            fresh. The first run downloads detection model weights; that download is made by the{" "}
            <code>ultralytics</code> library, not by Onitry&rsquo;s own code.
          </p>
          <p>
            ClassWatch observes other people&rsquo;s screens. See the{" "}
            <a href="#/terms">Terms</a> and the ClassWatch page about consent.
          </p>
        </section>

        <section className={styles.section}>
          <h2>This website</h2>
          <p>
            This site is a set of static pages. Its code sets no cookies, stores nothing in your browser,
            has no accounts or forms, and loads no analytics, ads, third-party scripts or web fonts. The
            company that hosts the files may keep ordinary server logs (such as your IP address and the pages
            requested), as any host does. Links to GitHub and Anthropic leave this site, and their own
            policies apply there.
          </p>
          <p>
            If you open an issue on GitHub, it is public. Leave out screenshots and anything from your{" "}
            <code>data</code> folder that you would not want others to read.
          </p>
        </section>

        <section className={styles.section}>
          <h2>Deleting your data</h2>
          <ol>
            <li>
              <strong>Files on your Mac.</strong> Delete the <code>data</code> folder inside the Onitry
              folder, or for the Mac app the folder <code>{APP_DATA_FOLDER}</code>. That removes everything Onitry saved, including ClassWatch&rsquo;s{" "}
              <code>data/room</code>. If you passed <code>--report-path</code>, delete that report too.
            </li>
            <li>
              <strong>Your key in the Keychain.</strong> Open Keychain Access, search for{" "}
              <code>onitry</code> and delete the entry. Or run:
              <pre className={styles.cmd}>security delete-generic-password -s onitry -a anthropic_api_key</pre>
            </li>
            <li>
              <strong>Your key at Anthropic.</strong> Delete or replace it in the{" "}
              <a href={ANTHROPIC_CONSOLE_URL} target="_blank" rel="noreferrer">
                Anthropic Console
              </a>
              .
            </li>
            <li>
              <strong>The extension launcher, if you installed it.</strong> From the Onitry folder, run{" "}
              <code>python native_host/install.py --uninstall</code>.
            </li>
            <li>
              <strong>The app.</strong> Delete the Onitry folder.
            </li>
          </ol>
          <p>
            Onitry cannot delete anything Anthropic received. For that, follow the process in Anthropic&rsquo;s
            privacy policy.
          </p>
        </section>

        <section className={styles.section}>
          <h2>Questions and changes</h2>
          <p>
            Ask on{" "}
            <a href={ISSUES_URL} target="_blank" rel="noreferrer">
              GitHub Issues
            </a>
            . If this page changes, the date at the top changes.
          </p>
        </section>
      </div>
    </main>
  );
}
