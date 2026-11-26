import { useEffect, useRef, useState } from "react";
import {
  ANTHROPIC_CONSOLE_URL,
  ANTHROPIC_PRIVACY_URL,
  APP_DATA_FOLDER,
  CLONE_URL,
  DOWNLOAD_URL,
  ISSUES_URL,
} from "../site.js";
import styles from "./Docs.module.css";

// Folder name git creates when cloning CLONE_URL (e.g. ".../Monitry.git" -> "Monitry").
const REPO_DIR = CLONE_URL.split("/").pop().replace(/\.git$/, "");

// ── Small building blocks ──────────────────────────────────────────────────

function Code({ children, label }) {
  // tabIndex lets keyboard users scroll a long line sideways.
  return (
    <pre className={styles.pre} tabIndex={0} aria-label={label}>
      <code>{children}</code>
    </pre>
  );
}

function Note({ title = "Note", tone = "tip", children }) {
  return (
    <div className={`${styles.note} ${tone === "warn" ? styles.noteWarn : ""}`}>
      <strong>{title}.</strong> {children}
    </div>
  );
}

function TableWrap({ label, children }) {
  return (
    <div className={styles.tableWrap} role="region" aria-label={label} tabIndex={0}>
      <table className={styles.table}>{children}</table>
    </div>
  );
}

function Ext({ href, children }) {
  return (
    <a href={href} target="_blank" rel="noreferrer noopener">
      {children}
    </a>
  );
}

function QA({ q, children }) {
  return (
    <div className={styles.qa}>
      <h4>{q}</h4>
      {children}
    </div>
  );
}

// ── Sections ───────────────────────────────────────────────────────────────

function Requirements() {
  return (
    <>
      <ul>
        <li>
          <strong>A Mac.</strong> Onitry is macOS only. It uses <code>osascript</code> and{" "}
          <code>say</code> for alerts and <code>rumps</code> for the optional menu bar app.
        </li>
        <li>
          <strong>Python 3.11 with Tk, only if you run it from source.</strong> The Mac app has Python inside. 3.11 is what the project&rsquo;s tests and linter
          target. 3.10 is the lowest that can work (the code uses <code>X | None</code> type
          annotations). The window is built with Tk, so your Python needs it: the python.org
          installers and conda&rsquo;s Python include it. Check with{" "}
          <code>python -c &quot;import tkinter&quot;</code>, which should print nothing.
        </li>
        <li>
          <strong>An Anthropic API key.</strong> This is the only paid part. See section 3.
        </li>
        <li>
          <strong>Screen Recording permission</strong> for Onitry (or, if you run it from source, for
          the terminal that runs it). See section 4.
        </li>
        <li>
          <strong>A terminal, only if you run it from source.</strong> The Mac app needs none.
        </li>
      </ul>
      <p>
        No particular macOS version is documented, so none is promised here. If it fails on your
        version, <Ext href={ISSUES_URL}>open an issue</Ext> and say which one.
      </p>
    </>
  );
}

function Install() {
  return (
    <>
      <h3>The easy way: the Mac app</h3>
      <ol>
        <li>
          <Ext href={DOWNLOAD_URL}>Download the latest release</Ext> and pick the file for your Mac:{" "}
          <strong>Apple Silicon</strong> (any Mac with an M-series chip) or <strong>Intel</strong>.
          If you are not sure, the Apple menu, About This Mac, shows the chip.
        </li>
        <li>Open the <code>.dmg</code> and drag <strong>Onitry</strong> onto <strong>Applications</strong>.</li>
        <li>
          Open Onitry from Applications. <strong>macOS will refuse the first time</strong>, because the
          app is not signed by an Apple-registered developer (that costs money, and Onitry is free).
          Control-click the app and choose <strong>Open</strong>, then <strong>Open</strong> again. On
          macOS 15 and later that option may be missing: try to open the app, then go to{" "}
          <strong>System Settings, Privacy &amp; Security</strong>, scroll down and press{" "}
          <strong>Open Anyway</strong>. You only do this once.
        </li>
        <li>
          Set your API key and switch on Screen Recording (sections 3 and 4). After that, open Onitry
          like any other app.
        </li>
      </ol>
      <Note title="What the warning means" tone="warn">
        The app is built from this project&rsquo;s public code by an automated build on GitHub, but it is
        not notarized by Apple, which is why macOS asks you to approve it. If you would rather not
        approve an unnotarized app, run it from source instead (below).
      </Note>
      <p>
        The app keeps its files in <code>{APP_DATA_FOLDER}</code> instead of a project folder. Everything
        else in this guide works the same.
      </p>

      <h2>Or run it from source (terminal)</h2>
      <h3>1. Get the code</h3>
      <Code label="Clone the repository">{`git clone ${CLONE_URL}
cd ${REPO_DIR}`}</Code>

      <h3>2. Create an environment and install the dependencies</h3>
      <p>Pick one. Both end with the same <code>pip install</code>.</p>
      <p><strong>Option A, venv</strong> (needs a Python 3.11 that has Tk):</p>
      <Code label="Create a venv">{`python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt`}</Code>
      <p><strong>Option B, conda:</strong></p>
      <Code label="Create a conda environment">{`conda create -n onitry python=3.11
conda activate onitry
pip install -r requirements.txt`}</Code>
      <p>
        <code>requirements.txt</code> installs <code>anthropic</code>, <code>httpx</code>,{" "}
        <code>keyring</code>, <code>rumps</code>, <code>mss</code>, <code>opencv-python</code>,{" "}
        <code>Pillow</code> and <code>numpy</code>. Nothing else is needed for Full Focus.
      </p>

      <h3>3. Run it</h3>
      <Code label="Start the app window">{`python gui.py`}</Code>
      <p>
        A window titled <strong>Full Focus</strong> opens. Next you need to give it an API key and
        a permission. Every later session starts the same way: open a terminal, go to the folder,
        activate the environment (<code>source .venv/bin/activate</code> or{" "}
        <code>conda activate onitry</code>), run <code>python gui.py</code>.
      </p>

      <h3>Other ways to run it</h3>
      <ul>
        <li>
          <code>python menubar.py</code> starts an optional menu bar app that opens the same window
          on demand and shows your status. It also has an &ldquo;Ask Claude&hellip;&rdquo; chat box
          that makes its own API calls (see the cost section).
        </li>
        <li>
          <code>python cli.py &quot;your task&quot;</code> runs in the terminal with no window. It
          is more limited, see the note at the end of section 5.
        </li>
      </ul>
    </>
  );
}

function ApiKey() {
  return (
    <>
      <h3>Create a key</h3>
      <ol>
        <li>
          Create an account at the <Ext href={ANTHROPIC_CONSOLE_URL}>Anthropic Console</Ext> and add
          credit or a payment method.
        </li>
        <li>
          Create an API key on the Console&rsquo;s API keys page. A key used only for Onitry is a
          good idea: you can revoke it without touching anything else.
        </li>
        <li>
          <strong>Set a monthly spend limit</strong> in the Console&rsquo;s limits settings before
          you start. The Console is Anthropic&rsquo;s and its layout changes, so if you cannot find
          the page, search Anthropic&rsquo;s documentation for &ldquo;spend limits&rdquo;. A runaway
          session costs real money on your key, and a limit is the only hard stop.
        </li>
      </ol>

      <h3>Give the key to the app (window)</h3>
      <ol>
        <li>
          In the Full Focus window, find the <strong>API Key:</strong> row. It reads{" "}
          <em>Not set</em>, <em>Saved in Keychain ✓</em> or <em>From environment variable</em>.
        </li>
        <li>
          Click <strong>Set Key</strong>, paste the key (it is shown as dots) and click{" "}
          <strong>Save</strong>. The dialog says &ldquo;Saved to macOS Keychain.&rdquo;
        </li>
      </ol>
      <p>
        The key is stored in the macOS Keychain under the service name <code>onitry</code> (account{" "}
        <code>anthropic_api_key</code>). It is not written to the project folder. If you also have{" "}
        <code>ANTHROPIC_API_KEY</code> set in your shell when you launch, the window will use it,
        but a key saved in the Keychain takes priority.
      </p>

      <h3>Give the key to cli.py</h3>
      <p>
        <code>cli.py</code> and ClassWatch read only the environment variable. They do not look in
        the Keychain.
      </p>
      <Code label="Set the key for this terminal session">{`export ANTHROPIC_API_KEY=your_key_here
python cli.py "write the introduction of my essay"`}</Code>
      <p>
        That <code>export</code> only lasts for the current terminal window. If you put it in your
        shell profile, remember that the key is then sitting in a plain text file.
      </p>
    </>
  );
}

function Permissions() {
  return (
    <>
      <h3>Screen Recording (required)</h3>
      <p>
        Without it, macOS does not let Python capture other apps&rsquo; windows (you typically get
        only the desktop), so there is nothing useful for the AI to look at. Permission goes to the
        app you start: <strong>Onitry</strong> if you use the Mac app, or, if you run it from source,
        the terminal that runs Python (Terminal, iTerm2 and so on).
      </p>
      <ol>
        <li>
          Open <strong>System Settings, Privacy &amp; Security, Screen Recording</strong>. (On older
          macOS versions the app is <em>System Preferences</em> and the page is{" "}
          <em>Security &amp; Privacy, Privacy, Screen Recording</em>.)
        </li>
        <li>Switch on Onitry (or your terminal app). If it is not listed, start monitoring once and look again.</li>
        <li>
          Quit Onitry completely (<kbd>Cmd</kbd>+<kbd>Q</kbd>) and open it again. From source: quit the
          terminal, reopen it, activate your environment and run <code>python gui.py</code>.
        </li>
      </ol>

      <h3>Other prompts you may see</h3>
      <ul>
        <li>
          <strong>Keychain.</strong> macOS may ask whether Python can use the Keychain item when you
          save or read your key. Allowing it is what lets the app find your key again next time.
        </li>
        <li>
          <strong>Automation or System Events.</strong> When a hard-interrupt popup appears, the
          app runs a short AppleScript that asks System Events to bring its window to the front.
          macOS may ask you to allow that. The popup is also marked always-on-top, so it should
          appear either way.
        </li>
        <li>
          <strong>Notifications.</strong> Soft reminders are ordinary macOS notification banners. If
          you never see one, check your notification and Focus settings.
        </li>
        <li>
          <strong>Camera</strong>, only for ClassWatch (section 10).
        </li>
      </ul>
    </>
  );
}

function StartMonitoring() {
  return (
    <>
      <ol>
        <li>
          Type what you are working on in the <strong>Task:</strong> field. Be specific: &ldquo;write
          the methods section of my lab report&rdquo; gives the AI more to judge against than
          &ldquo;work&rdquo;. The <strong>recents</strong> button lists your last eight tasks. An empty
          task turns the field&rsquo;s border red and nothing starts.
        </li>
        <li>
          Click <strong>Start Monitoring</strong>. The button becomes <strong>Stop Monitoring</strong>{" "}
          and the task field is locked. The first check happens about 5 seconds later. The log shows
          the model and resolution in use.
        </li>
        <li>
          Work. Each check adds a line to the log, such as{" "}
          <code>ON TASK: editing a Python file (next in 40s)</code>.
        </li>
        <li>
          Click <strong>Pause 10m</strong> for a break. Checks stop for ten minutes, then resume by
          themselves. The button turns into <strong>Resume</strong> with the minutes left, and you can
          click it to end the break early. Pause only works while monitoring is running.
        </li>
        <li>
          Click <strong>Stop Monitoring</strong> when you are done. A session summary appears (see
          section 6).
        </li>
      </ol>

      <h3>What the status colours mean</h3>
      <TableWrap label="Status colours">
        <thead>
          <tr>
            <th>Status</th>
            <th>Colour</th>
            <th>Meaning</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>Idle / Stopped</td>
            <td><span className={`${styles.dot} ${styles.dotGrey}`} aria-hidden="true" />Grey</td>
            <td>Not monitoring.</td>
          </tr>
          <tr>
            <td>ON TASK</td>
            <td><span className={`${styles.dot} ${styles.dotGreen}`} aria-hidden="true" />Green</td>
            <td>The latest check judged you on task.</td>
          </tr>
          <tr>
            <td>OFF TASK</td>
            <td><span className={`${styles.dot} ${styles.dotRed}`} aria-hidden="true" />Red</td>
            <td>The latest check judged you off task. Checks speed up.</td>
          </tr>
          <tr>
            <td>Paused</td>
            <td><span className={`${styles.dot} ${styles.dotAmber}`} aria-hidden="true" />Yellow</td>
            <td>You pressed Pause 10m, or the browser extension paused it.</td>
          </tr>
          <tr>
            <td>AWAY</td>
            <td><span className={`${styles.dot} ${styles.dotAmber}`} aria-hidden="true" />Yellow</td>
            <td>No mouse or keyboard for 5 minutes. Checks are skipped until you return.</td>
          </tr>
          <tr>
            <td>Resuming&hellip;</td>
            <td><span className={`${styles.dot} ${styles.dotGrey}`} aria-hidden="true" />Grey</td>
            <td>A pause just ended; the next check is coming.</td>
          </tr>
        </tbody>
      </TableWrap>
      <p>
        If a check fails (bad key, no network, no credit), the log shows <code>Error: &hellip;</code>{" "}
        and the status stays as it was. A failed check does not trigger an alert and is not counted in
        the session summary.
      </p>

      <h3>A wrong call</h3>
      <p>
        The AI will sometimes get it wrong. Click <strong>Flag last as wrong</strong> in the main
        window (or <strong>Not actually off task?</strong> on a popup) and write what you were really
        doing. That text goes into the activity log as a correction the AI reads on later checks.
      </p>

      <Note title="cli.py is more limited" tone="warn">
        <code>python cli.py &quot;task&quot;</code> checks the same way and skips checks when you are
        idle, but it has no window: no typing challenge, no pause button, no flagging, no session
        summary. A hard interrupt is spoken aloud and a soft one is a banner. It also does not use
        Haiku: it runs on <code>claude-sonnet-4-6</code> (the default in <code>config.py</code>),
        which costs roughly three times as much per check as the window does. Its startup message
        says it checks every 10 seconds; it actually uses the same 10 to 120 second ramp as the
        window.
      </Note>
    </>
  );
}

function HowItWorks() {
  return (
    <>
      <h3>The checking loop</h3>
      <ol>
        <li>
          Onitry takes a screenshot of your <strong>primary display</strong> and shrinks it to fit
          the resolution setting (1280 pixels wide by default).
        </li>
        <li>
          It sends the image, your task, the last 10 lines of the activity log and the AI&rsquo;s own
          running notes to Claude (Haiku 4.5) with your API key.
        </li>
        <li>
          Claude replies with a small JSON object: on task or not, whether to interrupt, a short
          description of what you are doing, a reminder, and updated notes.
        </li>
        <li>
          Onitry updates the status, appends the description to the log, shows or speaks the reminder
          if there is one, then waits for the next check.
        </li>
      </ol>

      <h3>Adaptive intervals</h3>
      <p>
        The wait starts at 10 seconds and grows by 10 seconds after every check, up to 120 seconds,
        while you stay on task. Each wait is multiplied by a random factor between 0.4 and 1.6 (and
        never goes below 10 seconds), so checks are not on a fixed beat. The moment a check finds you
        off task, the base wait snaps back to 10 seconds and starts climbing again.
      </p>

      <h3>Idle skipping</h3>
      <p>
        If there has been no mouse or keyboard input for 5 minutes, Onitry takes no screenshot and
        makes no API call. The status reads AWAY. Checks resume when you move the mouse or press a
        key. Idle time is measured by macOS (<code>ioreg</code>), not by watching what you type. Note
        what this means: watching a long video without touching anything counts as idle after 5
        minutes. If the idle check ever fails, checking continues rather than stopping.
      </p>

      <h3>Hard and soft interrupts</h3>
      <p>
        The AI decides which kind of reminder to use. It is not a fixed rule.
      </p>
      <div className={styles.twoCol}>
        <div className={styles.card}>
          <h4>Hard interrupt</h4>
          <p>
            The reminder is spoken aloud (macOS <code>say</code>) and a red popup appears on top of
            other windows. New checks are paused while it is open.
          </p>
        </div>
        <div className={styles.card}>
          <h4>Soft reminder</h4>
          <p>
            A silent macOS notification banner. No sound, no popup, monitoring carries on as normal.
          </p>
        </div>
      </div>

      <h3>The typing challenge</h3>
      <p>
        The popup shows one of ten fixed sentences, each 14 to 18 words. Type it exactly and the{" "}
        <strong>Back to work</strong> button becomes active. It is friction, not a lock:
      </p>
      <ul>
        <li>The popup closes by itself after 90 seconds if you do nothing.</li>
        <li>
          <strong>Not actually off task?</strong> closes it straight away and opens a box where you
          explain what you were doing. Your explanation is fed back to the AI.
        </li>
        <li>
          After the popup closes, there is a grace period with no new checks. It defaults to 60
          seconds and you can set it from 0 to 300 seconds in <strong>Configure</strong>.
        </li>
      </ul>

      <h3>Session memory</h3>
      <p>Two things carry context from one check to the next, and both reset every time you press Start:</p>
      <ul>
        <li>
          The <strong>activity log</strong>, a text file of one-line descriptions. Only the last 10
          lines go to the AI. Off-task lines are marked, and your corrections are added to it.
        </li>
        <li>
          The AI&rsquo;s <strong>notes</strong>, a short scratchpad it rewrites on each check (for
          example &ldquo;has been reading docs for 10 minutes&rdquo;). It is kept in memory only and
          is never written to disk.
        </li>
      </ul>

      <h3>Session summary</h3>
      <p>
        When you stop, a window shows the time monitored, a coloured timeline bar, the percentage of
        time on task, the number of interruptions and the estimated cost of the session. The
        percentage is built from the waits between checks, so it is an approximation. Stopping from
        the browser extension skips the summary.
      </p>
    </>
  );
}

function Costs() {
  return (
    <>
      <p>
        Onitry itself is free. What you pay is Anthropic&rsquo;s charge for the checks on your key.
        The numbers below are an <strong>estimate</strong> worked out from the code and Anthropic&rsquo;s
        published image sizing. Onitry does not log token usage, so these are not measurements from
        a real bill. Your Console usage page is the source of truth.
      </p>

      <h3>One check, on Haiku 4.5</h3>
      <p>
        Haiku 4.5 costs $1 per million input tokens and $5 per million output tokens (the same
        figures are in the app&rsquo;s own price table). An image costs about width &times; height
        &divide; 750 tokens.
      </p>
      <TableWrap label="Estimated cost of one check">
        <thead>
          <tr>
            <th>Part</th>
            <th>Tokens</th>
            <th>Cost</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>Screenshot, 1280 &times; 800</td>
            <td>about 1,370</td>
            <td>$0.0014</td>
          </tr>
          <tr>
            <td>Text: instructions, task, 10 log lines, notes</td>
            <td>about 500</td>
            <td>$0.0005</td>
          </tr>
          <tr>
            <td>Reply (limited to 512 tokens)</td>
            <td>about 100 to 150</td>
            <td>$0.0005 to $0.0008</td>
          </tr>
          <tr>
            <td><strong>One check</strong></td>
            <td></td>
            <td><strong>about $0.0025</strong></td>
          </tr>
        </tbody>
      </TableWrap>

      <h3>One hour</h3>
      <ul>
        <li>
          <strong>A calm hour:</strong> the wait ramps 10, 20, 30 &hellip; 120 seconds. That is 12
          checks in the first 13 minutes (10 + 20 + &hellip; + 120 = 780 seconds), then about 24 more
          at roughly 2 minutes each. About <strong>36 checks</strong>. 36 &times; $0.0025 ={" "}
          <strong>about $0.09</strong>.
        </li>
        <li>
          <strong>A distracted hour:</strong> every off-task check sends the wait back to 10 seconds,
          so you get more checks. 80 checks would be about <strong>$0.20</strong>.
        </li>
        <li>
          <strong>Away from the keyboard:</strong> no checks, no cost.
        </li>
      </ul>
      <p>
        So a rough range is <strong>$0.06 to $0.20 per hour</strong>. For scale, 4 hours a day for
        20 days is 80 hours, or about $5 to $16 across those 20 days at that range. The theoretical ceiling is a
        check roughly every 10 seconds (about 300 an hour, about $0.75), but popups pause checking and
        the grace period adds a gap, so you are unlikely to get near it.
      </p>

      <h3>What the app shows</h3>
      <p>
        The window shows <em>Session cost</em> while you work, and the summary shows what was spent.
        Onitry computes that from the token counts Anthropic returns and a price table inside the
        app. It is in memory only: it resets at each Start and is not saved. If Anthropic changes
        its prices, the app will not know.
      </p>

      <h3>Settings that change the cost</h3>
      <p>
        <strong>Configure</strong> in the window has two of them (both are saved in{" "}
        <code>data/settings.json</code> and apply the next time you press Start):
      </p>
      <ul>
        <li>
          <strong>Resolution:</strong> 1280px (default), 800px, 512px or 320px wide. Lower means
          fewer image tokens. Only the image part of the cost shrinks. For example an 800 &times; 500
          screenshot is about 530 tokens instead of about 1,370, which takes a check from about
          $0.0025 to about $0.0016. Smaller images also make small text harder for the AI to read.
        </li>
        <li>
          <strong>Screenshot quality (JPEG):</strong> a slider from 20 to 100, default 75. This
          changes how compressed the picture is. As far as Anthropic&rsquo;s image sizing goes, tokens
          follow the pixel dimensions, so quality mostly affects the upload size and how crisp text
          looks, not the bill. Resolution is the setting to use for cost.
        </li>
      </ul>

      <h3>Other things that use your key</h3>
      <ul>
        <li>
          <code>cli.py</code> runs on <code>claude-sonnet-4-6</code> ($3 and $15 per million tokens),
          so about three times the figures above.
        </li>
        <li>
          The menu bar app&rsquo;s <em>Ask Claude&hellip;</em> box also uses{" "}
          <code>claude-sonnet-4-6</code>.
        </li>
        <li>
          The browser extension&rsquo;s weekly review (section 9) uses a larger model, by default{" "}
          <code>claude-opus-5-5</code>, once per review. Onitry does not estimate that cost.
        </li>
        <li>ClassWatch has its own estimate in section 10.</li>
      </ul>

      <h3>Spending limit</h3>
      <p>
        Set a monthly spend limit in the Anthropic Console (section 3), keep the Console&rsquo;s usage
        page open for your first few sessions, and press Stop when you are not working. If you hit the
        limit or run out of credit, checks fail with an error in the log until you fix it.
      </p>
    </>
  );
}

function PrivacyInPractice() {
  return (
    <>
      <h3>What leaves your computer</h3>
      <p>
        Each check sends the following to Anthropic, using your API key:
      </p>
      <ul>
        <li>One JPEG of your <strong>primary display</strong>. Other monitors are not captured.</li>
        <li>Your task text.</li>
        <li>The last 10 lines of the activity log (short descriptions of what you were doing).</li>
        <li>The AI&rsquo;s running notes.</li>
        <li>
          If the Timecheck extension started the session, the context it sent along (for example what
          is due).
        </li>
      </ul>
      <p>
        The screenshot is whatever is on that display: messages, email, a password manager if it is
        open. If you would rather it not be seen, press Pause or Stop first.
      </p>
      <p>
        Full Focus in its free setup sends nothing to any Onitry server, and there is no Onitry server
        to send it to. The only outside host it talks to is Anthropic&rsquo;s API.
      </p>

      <h3>What Anthropic does with it</h3>
      <p>
        Anthropic&rsquo;s own retention and privacy policy applies to what they receive. Onitry does not
        control it and does not summarise it here. Read it:{" "}
        <Ext href={ANTHROPIC_PRIVACY_URL}>Anthropic&rsquo;s privacy policy</Ext>.
      </p>

      <h3>What is stored on your Mac</h3>
      <p>
        <strong>No screenshot is ever written to disk.</strong> It is captured, encoded and sent from
        memory. There is no keylogger: the only input-related code asks macOS how long since your last
        input, nothing more. Everything Onitry does keep is in the <code>data/</code> folder inside the
        project (or <code>{APP_DATA_FOLDER}</code> in the Mac app), as plain, unencrypted text:
      </p>
      <TableWrap label="Files in the data folder">
        <thead>
          <tr>
            <th>File</th>
            <th>Contents</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td><code>context.txt</code></td>
            <td>The activity log: your task and one-line descriptions of what you were doing. Overwritten at each Start.</td>
          </tr>
          <tr>
            <td><code>status.json</code></td>
            <td>Current status, task, latest description and session cost.</td>
          </tr>
          <tr>
            <td><code>settings.json</code></td>
            <td>Resolution, JPEG quality, grace period and your last eight task names.</td>
          </tr>
          <tr>
            <td><code>bridge_token</code></td>
            <td>The pairing code for the browser extension.</td>
          </tr>
        </tbody>
      </TableWrap>
      <p>
        If you install the extension launcher it adds <code>onitry-native-host</code> and{" "}
        <code>native_launch.log</code> there too. ClassWatch adds a <code>room</code> folder with
        per-screen logs and its report. Your API key is not in this folder; it is in the Keychain
        (or, for <code>cli.py</code>, your environment).
      </p>
      <p>
        More on the legal side is on the <a href="#/privacy">Privacy page</a>.
      </p>
    </>
  );
}

function Bridge() {
  return (
    <>
      <p>
        <strong>Timecheck</strong> is a separate Chrome extension (a planner with focus blocks, a
        distraction gate and a journal). It is not part of this repository and is not covered here
        beyond how it connects to Onitry. The connection is a small local web server that runs inside
        the Full Focus window.
      </p>

      <h3>Pair it</h3>
      <ol>
        <li>Start <code>python gui.py</code>. The bridge starts with the window.</li>
        <li>
          Click <strong>Configure</strong>. The <strong>Browser planner pairing code</strong> is shown
          near the bottom (it looks like <code>K7QM-29XD</code>), with a <strong>Copy</strong> button.
        </li>
        <li>
          In the extension, open its settings, find the Onitry section, paste the code and use{" "}
          <strong>Test connection</strong>.
        </li>
      </ol>
      <p>
        The code lives in <code>data/bridge_token</code>. To get a new one, quit Onitry, delete that
        file and start Onitry again.
      </p>

      <h3>What it can do</h3>
      <ul>
        <li>Start monitoring a task (a focus block) and stop it. Starting a different task stops the old one first.</li>
        <li>Pause (up to 240 minutes) and resume.</li>
        <li>
          Read your status: on or off task, the task, the latest activity description, seconds on and
          off task, interruption count and the last error.
        </li>
        <li>
          Ask for a <strong>weekly review</strong>. The extension sends its weekly numbers to Onitry,
          which sends them to Anthropic on your key and returns the text. The extension never holds a
          key. This needs a key set in Onitry.
        </li>
      </ul>

      <h3>How it is locked down</h3>
      <p>
        It listens on <code>127.0.0.1:47323</code> only, so nothing else on your network can reach it.
        Every request except a ping needs the pairing code. It rejects requests that carry a web page&rsquo;s origin,
        and any request with an unexpected Host header. The port can be changed
        with the <code>ONITRY_BRIDGE_PORT</code> environment variable. If another Onitry window already
        holds the port, the log says &ldquo;Browser bridge unavailable.&rdquo;
      </p>

      <h3>Let the extension launch Onitry</h3>
      <p>
        Optional. This registers a native-messaging launcher so the extension&rsquo;s Launch Onitry
        button can start the window. Run it with the same Python you use for Onitry, from the project
        folder:
      </p>
      <Code label="Install the native launcher">{`source .venv/bin/activate     # or: conda activate onitry
python native_host/install.py`}</Code>
      <p>
        It registers <code>com.onitry.host</code> for Chrome, Chromium, Brave, Edge and Arc (the
        ones it finds), only for the Timecheck extension&rsquo;s ID, and writes a launcher that points at
        your Python and this folder. Restart the browser afterwards. It understands two commands:{" "}
        <code>ping</code>, and <code>launch</code>, which starts <code>gui.py</code> unless the bridge
        is already listening. If you move the folder or rebuild the environment, run the installer
        again. To remove it:
      </p>
      <Code label="Remove the native launcher">{`python native_host/install.py --uninstall`}</Code>
    </>
  );
}

function ClassWatchDocs() {
  return (
    <>
      <Note title="Experimental" tone="warn">
        ClassWatch is only unit-tested with mocked camera and API calls. There is no evidence of how
        accurate it is on real classroom footage. Treat it as a prototype, not a finished product.
      </Note>
      <p>
        ClassWatch is a command-line tool. It points a camera at a room, finds laptop and monitor
        screens with a vision model, tracks each one, asks Haiku to describe what is on it, and writes a
        Markdown report when you press <kbd>Ctrl</kbd>+<kbd>C</kbd>. It does not interrupt anyone. See
        the <a href="#/classwatch">ClassWatch page</a> for the overview.
      </p>

      <h3>Install</h3>
      <p>Do sections 1 and 2 first, then add the heavier dependencies:</p>
      <Code label="Install ClassWatch dependencies">{`pip install -r requirements-room.txt`}</Code>
      <p>
        This adds <code>ultralytics</code>, which pulls in PyTorch, so expect a large download. The
        detection model weights are downloaded automatically the first time you run it.
      </p>

      <h3>Permissions and key</h3>
      <ul>
        <li>
          <strong>Camera:</strong> macOS should ask to let your terminal use the camera the first
          time. If you said no, enable it under <strong>System Settings, Privacy &amp; Security,
          Camera</strong>. If the camera cannot be opened, the tool exits with &ldquo;Could not open
          camera&rdquo;.
        </li>
        <li>
          <strong>API key:</strong> ClassWatch reads <code>ANTHROPIC_API_KEY</code> from the
          environment only, not the Keychain.
        </li>
      </ul>

      <h3>Run it</h3>
      <Code label="Run ClassWatch">{`export ANTHROPIC_API_KEY=your_key_here
python room_cli.py
python room_cli.py --task "working on the lab assignment" --interval 20
python room_cli.py --camera 1 --conf 0.3 --max-cycles 5`}</Code>
      <p>
        The key has to be set before you run it, even for <code>--help</code>, because the script
        checks for it first.
      </p>
      <TableWrap label="room_cli.py options">
        <thead>
          <tr>
            <th>Option</th>
            <th>Default</th>
            <th>Meaning</th>
          </tr>
        </thead>
        <tbody>
          <tr><td><code>--camera</code></td><td>0</td><td>Camera index.</td></tr>
          <tr><td><code>--interval</code></td><td>15</td><td>Seconds between capture cycles.</td></tr>
          <tr><td><code>--conf</code></td><td>0.25</td><td>Detection confidence threshold.</td></tr>
          <tr>
            <td><code>--task</code></td>
            <td>none</td>
            <td>One task, applied to every screen. Without it, screens are described but not judged.</td>
          </tr>
          <tr>
            <td><code>--report-path</code></td>
            <td><code>data/room/report.md</code></td>
            <td>Where the report is written when you stop.</td>
          </tr>
          <tr>
            <td><code>--max-cycles</code></td>
            <td>none</td>
            <td>Stop after this many cycles instead of running until Ctrl+C.</td>
          </tr>
        </tbody>
      </TableWrap>
      <p>
        When you stop it prints the report path and the estimated total spend. Per-screen logs are
        written to <code>data/room/</code>. The images sent to Anthropic are crops of each detected
        screen, at most 800 pixels wide, not the whole camera frame. They are not saved to disk.
      </p>

      <h3>Cost estimate</h3>
      <p>
        Each cycle sends one crop per detected screen to Haiku 4.5. At the default 15 seconds that is
        240 analyses per screen per hour. A crop of up to 800 pixels is a few hundred to roughly a
        thousand image tokens, plus text and a short reply, so about $0.001 to $0.0017 each. That gives{" "}
        <strong>roughly $0.25 to $0.40 per screen per hour</strong>. It is an estimate, it scales with
        the number of screens, and doubling <code>--interval</code> roughly halves it.
      </p>

      <h3>Consent and local rules</h3>
      <Note title="Read this" tone="warn">
        ClassWatch looks at other people&rsquo;s screens. Only use it where the people being observed
        know and agree, and where your school, workplace and local law allow it. Onitry does not check
        any of that for you.
      </Note>
    </>
  );
}

function Advanced() {
  return (
    <>
      <p>
        Only settings that take effect are listed. Where a setting lives only in code, it says so.
      </p>

      <h3>In the window (Configure)</h3>
      <ul>
        <li>Resolution (1280, 800, 512 or 320 pixels wide).</li>
        <li>Screenshot quality (JPEG, 20 to 100).</li>
        <li>Grace period after dismissing a popup (0 to 300 seconds, steps of 10).</li>
        <li>The browser pairing code and the session cost so far (read only).</li>
      </ul>
      <p>
        They are saved to <code>data/settings.json</code>. Resolution and quality apply when you next
        press Start; the grace period applies immediately.
      </p>

      <h3>Environment variables</h3>
      <TableWrap label="Environment variables">
        <thead>
          <tr>
            <th>Variable</th>
            <th>Effect</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td><code>ANTHROPIC_API_KEY</code></td>
            <td>Your key for <code>cli.py</code> and ClassWatch. The window uses it too if nothing is saved in the Keychain.</td>
          </tr>
          <tr>
            <td><code>ONITRY_BRIDGE_PORT</code></td>
            <td>Port for the browser bridge (default 47323). The extension is not part of this repository, so check there how it is told which port to use.</td>
          </tr>
          <tr>
            <td><code>ONITRY_REVIEW_MODEL</code></td>
            <td>Model for the extension&rsquo;s weekly review (default <code>claude-opus-5-5</code>).</td>
          </tr>
          <tr>
            <td><code>ONITRY_EDITION=dev</code></td>
            <td>
              A testing mode that adds a model picker (Haiku 4.5, Sonnet 4.6, Opus 4.8) to Configure.
              Sonnet and Opus cost more per check.
            </td>
          </tr>
        </tbody>
      </TableWrap>
      <Code label="Run with the model picker">{`ONITRY_EDITION=dev python gui.py`}</Code>

      <h3>Constants in the code</h3>
      <p>
        These are not settings screens. Edit the file and restart if you want to change them.
      </p>
      <ul>
        <li>
          <code>gui.py</code>: <code>MIN_INTERVAL</code> (10), <code>MAX_INTERVAL</code> (120),{" "}
          <code>INTERVAL_STEP</code> (10), <code>JITTER_LO</code> and <code>JITTER_HI</code> (0.4 and
          1.6), <code>PAUSE_MINUTES</code> (10) and <code>IDLE_THRESHOLD_SECONDS</code> (300).
        </li>
        <li>
          <code>config.py</code>: <code>MAX_TOKENS_PER_RESPONSE</code> (512), the cap on the
          AI&rsquo;s reply length.
        </li>
        <li>
          <code>config.py</code>: <code>CHECK_INTERVAL</code> (10) is the minimum wait for{" "}
          <code>cli.py</code> only. The window ignores it.
        </li>
      </ul>
      <p>
        <code>CONTEXT_MAX_CHARS</code> also appears in <code>config.py</code> but nothing reads it.
        The app always sends the last 10 log lines.
      </p>
    </>
  );
}

function Troubleshooting() {
  return (
    <>
      <h3>Troubleshooting</h3>

      <QA q="Nothing happens, or the AI describes things that are not on my screen">
        <p>
          Almost always Screen Recording. Check that Onitry (or, from source, your terminal) is switched on under System
          Settings, Privacy &amp; Security, Screen Recording (section 4), then quit it
          completely, reopen it and start again. Without the permission macOS does not hand over other
          apps&rsquo; windows, so the AI sees an empty desktop.
        </p>
      </QA>

      <QA q="“ERROR: No API key set — click 'Set Key'.”">
        <p>
          You pressed Start with no key. Click <strong>Set Key</strong> in the window, or set{" "}
          <code>ANTHROPIC_API_KEY</code> before launching.
        </p>
      </QA>

      <QA q="The log shows “Error: …” on every check">
        <p>
          The message is Anthropic&rsquo;s or the network&rsquo;s. Usual causes: a mistyped or revoked key,
          no credit, a spend limit reached, rate limiting, or no internet. Onitry retries a couple of
          times for temporary errors, logs the failure and tries again at the next interval. Check the
          Console.
        </p>
      </QA>

      <QA q="“No module named _tkinter” (or tkinter)">
        <p>
          Your Python was built without Tk. Use the python.org installer or conda&rsquo;s Python, create
          the environment again and reinstall the requirements.
        </p>
      </QA>

      <QA q="The Keychain asks for my password">
        <p>
          Saving and reading your key goes through the macOS Keychain, so macOS asks whether Python may
          use the item. Allow it. Choosing the option that always allows it should stop the repeats,
          though a different Python (a new environment, say) may be asked about separately.
        </p>
      </QA>

      <QA q="The popup steals focus">
        <p>
          That is what a hard interrupt is for: the popup moves to the front and puts the cursor in its
          text box, so anything you are typing at that moment lands there. Press <strong>Pause 10m</strong>{" "}
          before a meeting or a call, raise the grace period in Configure, or press Stop. If an
          interrupt was wrong, use <strong>Not actually off task?</strong>.
        </p>
      </QA>

      <QA q="I never see the soft reminders">
        <p>
          They are macOS notification banners. Check your notification settings and any Focus mode that
          is silencing them.
        </p>
      </QA>

      <QA q="“Browser bridge unavailable”">
        <p>
          The port is already in use, usually because another Onitry window is open. Close it, or set a
          different <code>ONITRY_BRIDGE_PORT</code>.
        </p>
      </QA>

      <h3>FAQ</h3>

      <QA q="Is it really free?">
        <p>
          Yes. There is no fee, subscription, account or Onitry server. You pay Anthropic for the
          checks, on your own key, at roughly the rates in section 7.
        </p>
      </QA>

      <QA q="How much did this cost me?">
        <p>
          The window&rsquo;s <em>Session cost</em> and the end-of-session summary give an estimate for the
          session. Onitry does not keep a history. For your real bill, look at the usage page in the
          Anthropic Console.
        </p>
      </QA>

      <QA q="Is my screen sent anywhere besides Anthropic?">
        <p>
          No. In Full Focus the only outside host Onitry&rsquo;s own code talks to is Anthropic&rsquo;s API, and
          the browser bridge listens on your own machine only. ClassWatch also uses the third-party{" "}
          <code>ultralytics</code> library, which downloads model weights on first run; what else
          that library does on the network has not been audited here.
        </p>
      </QA>

      <QA q="Does it log my keystrokes?">
        <p>No. It only asks macOS how long it has been since your last input, to skip checks when you are away.</p>
      </QA>

      <QA q="What about more than one monitor?">
        <p>Only the primary display is captured.</p>
      </QA>

      <QA q="Does it work on Windows or Linux?">
        <p>No. It needs macOS.</p>
      </QA>

      <QA q="How do I uninstall it and delete my data?">
        <p>Everything Onitry keeps is in the project folder plus one Keychain entry. In this order:</p>
        <ol>
          <li>
            Quit Onitry. If you installed the extension launcher, remove it with{" "}
            <code>python native_host/install.py --uninstall</code>.
          </li>
          <li>
            Delete the Keychain entry named <code>onitry</code>. From the activated environment:
            <Code label="Delete the stored API key">{`python -c "import keyring; keyring.delete_password('onitry', 'anthropic_api_key')"`}</Code>
            Or open Keychain Access, search for <code>onitry</code> and delete the item.
          </li>
          <li>
            Mac app: drag Onitry from Applications to the Bin and delete the folder{" "}
            <code>{APP_DATA_FOLDER}</code> (your logs and settings).
          </li>
          <li>
            From source: delete the project folder. This removes <code>data/</code> (your logs and settings) and a{" "}
            <code>.venv</code> inside it:
            <Code label="Delete the folder">{`cd ..
rm -rf ${REPO_DIR}`}</Code>
          </li>
          <li>
            If you used conda: <code>conda env remove -n onitry</code>.
          </li>
          <li>
            In the Anthropic Console, delete the API key you made for Onitry. Removing the files does
            not revoke it.
          </li>
        </ol>
        <p>
          What Anthropic holds on their side is covered by their{" "}
          <Ext href={ANTHROPIC_PRIVACY_URL}>privacy policy</Ext>, not by anything you can delete here.
        </p>
      </QA>

      <QA q="Something else is wrong">
        <p>
          <Ext href={ISSUES_URL}>Open an issue on GitHub</Ext>. Say what you ran, what you expected and
          what the window&rsquo;s log said. Remove any API key before pasting.
        </p>
      </QA>
    </>
  );
}

// ── Page ───────────────────────────────────────────────────────────────────

const SECTIONS = [
  { id: "requirements", label: "Requirements", Body: Requirements,
    lead: "What you need before you start." },
  { id: "install", label: "Install", Body: Install,
    lead: "Download the Mac app, or run it from source." },
  { id: "api-key", label: "Your API key", Body: ApiKey,
    lead: "Create a key, set a spend limit, store the key." },
  { id: "permissions", label: "Permissions", Body: Permissions,
    lead: "What macOS will ask for, and where to switch it on." },
  { id: "start", label: "Start monitoring", Body: StartMonitoring,
    lead: "The window, start and stop, pause, and what the colours mean." },
  { id: "how-it-works", label: "How it works", Body: HowItWorks,
    lead: "The checking loop, interrupts, memory and the summary." },
  { id: "costs", label: "What it costs", Body: Costs,
    lead: "An estimate with the arithmetic, and how to cap it." },
  { id: "privacy", label: "Privacy in practice", Body: PrivacyInPractice,
    lead: "What is sent, what is stored, what is not." },
  { id: "timecheck", label: "Timecheck extension", Body: Bridge,
    lead: "Pairing the browser extension and the launcher." },
  { id: "classwatch", label: "ClassWatch (experimental)", Body: ClassWatchDocs,
    lead: "The camera-based room monitor." },
  { id: "advanced", label: "Advanced configuration", Body: Advanced,
    lead: "Settings that really exist." },
  { id: "help", label: "Troubleshooting and FAQ", Body: Troubleshooting,
    lead: "Fixes for common problems, and quick answers." },
];

const wideScreen = () =>
  typeof window !== "undefined" && window.matchMedia && window.matchMedia("(min-width: 901px)").matches;

export default function Docs() {
  const [active, setActive] = useState(SECTIONS[0].id);
  const [navOpen, setNavOpen] = useState(wideScreen);
  const headingRefs = useRef({});

  // Highlight the section being read. Purely a convenience: the page works without it.
  useEffect(() => {
    if (typeof IntersectionObserver === "undefined") return undefined;
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) setActive(entry.target.dataset.section);
        });
      },
      { rootMargin: "-80px 0px -65% 0px" }
    );
    SECTIONS.forEach(({ id }) => {
      const el = document.getElementById(`sec-${id}`);
      if (el) observer.observe(el);
    });
    return () => observer.disconnect();
  }, []);

  // Not an <a href="#id">: the site routes on the URL hash, so changing it would leave the docs page.
  const jump = (id) => {
    const section = document.getElementById(`sec-${id}`);
    if (!section) return;
    setActive(id);
    // On small screens the contents list sits above the article and collapses when a section is chosen,
    // which moves everything up. Scroll after that layout change, not before it.
    if (!wideScreen()) setNavOpen(false);
    requestAnimationFrame(() =>
      requestAnimationFrame(() => {
        section.scrollIntoView({ behavior: "instant" });
        const heading = headingRefs.current[id];
        if (heading) heading.focus({ preventScroll: true });
      })
    );
  };

  return (
    <div className={styles.layout}>
      <aside className={styles.sidebar}>
        <details
          className={styles.toc}
          open={navOpen}
          onToggle={(e) => setNavOpen(e.currentTarget.open)}
        >
          <summary>On this page</summary>
          <nav aria-label="Documentation sections">
            <ol className={styles.tocList}>
              {SECTIONS.map((s, i) => (
                <li key={s.id}>
                  <button
                    type="button"
                    className={`${styles.tocLink} ${active === s.id ? styles.tocActive : ""}`}
                    aria-current={active === s.id ? "true" : undefined}
                    onClick={() => jump(s.id)}
                  >
                    <span className={styles.tocNum} aria-hidden="true">{i + 1}</span>
                    {s.label}
                  </button>
                </li>
              ))}
            </ol>
          </nav>
        </details>
      </aside>

      <main className={styles.content}>
        <article className={styles.article}>
          <h1>Documentation</h1>
          <p className={styles.intro}>
            Onitry is free. You bring your own Anthropic API key and pay Anthropic only for what you
            use. This page takes a Mac user who is comfortable with a terminal from nothing to a
            running session. You can download a Mac app, or run it from source if you prefer a terminal.
          </p>

          {SECTIONS.map((s, i) => (
            <section
              key={s.id}
              id={`sec-${s.id}`}
              data-section={s.id}
              className={styles.section}
              aria-labelledby={`h-${s.id}`}
            >
              <h2
                id={`h-${s.id}`}
                tabIndex={-1}
                ref={(el) => {
                  headingRefs.current[s.id] = el;
                }}
              >
                <span className={styles.h2num} aria-hidden="true">{i + 1}</span>
                {s.label}
              </h2>
              <p className={styles.sectionLead}>{s.lead}</p>
              <s.Body />
            </section>
          ))}
        </article>
      </main>
    </div>
  );
}
