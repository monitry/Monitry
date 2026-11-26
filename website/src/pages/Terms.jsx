import styles from "./Legal.module.css";
import { ANTHROPIC_CONSOLE_URL, ISSUES_URL, LAST_UPDATED } from "../site.js";

export default function Terms() {
  return (
    <main className={styles.page}>
      <div className={styles.inner}>
        <p className={styles.label}>Legal</p>
        <h1 className={styles.title}>Terms</h1>
        <p className={styles.meta}>Last updated {LAST_UPDATED}</p>

        <p className={styles.notice}>
          This is a plain-language summary of how Onitry is offered. It is not legal advice. If something here
          matters to you legally, ask a lawyer.
        </p>

        <section className={styles.section}>
          <h2>What Onitry is</h2>
          <p>
            Onitry is a free tool for Mac. You run it yourself and you bring your own Anthropic API key. It
            comes as two programs: <strong>Full Focus</strong>, which watches your own screen, and{" "}
            <strong>ClassWatch</strong>, which is experimental and watches screens through a camera. This page
            is what they are offered on.
          </p>
        </section>

        <section className={styles.section}>
          <h2>Provided as is</h2>
          <p>
            Onitry is provided as it is, with no warranty of any kind. It can have bugs. ClassWatch is
            experimental and has not been measured for accuracy on real footage. You use Onitry at your own
            risk. The people who make it are not responsible for losses that come from using it, including
            lost work, missed deadlines or API charges.
          </p>
        </section>

        <section className={styles.section}>
          <h2>Your API key and your costs</h2>
          <ul>
            <li>
              You pay Anthropic directly for what you use. Onitry charges nothing and does not see your bill.
            </li>
            <li>
              Cost figures on this site are estimates, not measurements. Your real cost depends on your
              settings and on how often you drift off task.
            </li>
            <li>
              Set a monthly spending limit in the{" "}
              <a href={ANTHROPIC_CONSOLE_URL} target="_blank" rel="noreferrer">
                Anthropic Console
              </a>{" "}
              before you start. Stop monitoring when you do not need it. A bug or a long-running session can
              cost real money on your key.
            </li>
            <li>
              Keep your key private. You are responsible for everything done with it, and for following
              Anthropic&rsquo;s own terms and usage rules for your account.
            </li>
          </ul>
        </section>

        <section className={styles.section}>
          <h2>The AI can be wrong</h2>
          <p>
            Onitry asks an AI model to look at a screenshot and decide whether you are on task. It will
            sometimes flag real work as off task, and sometimes miss a real distraction. The popup has a
            button for telling it when it got a call wrong. Do not treat its output as proof of anything
            about a person, and do not use it for decisions that matter, such as grades, pay or discipline.
          </p>
          <p>
            Onitry is a nudge, not a lock. The reminder popup closes by itself after 90 seconds, and you can
            stop the app at any time.
          </p>
        </section>

        <section className={styles.section}>
          <h2>Watching other people</h2>
          <ul>
            <li>
              <strong>Full Focus</strong> is meant to watch your own screen. Do not run it on a computer you
              do not own, or on someone else&rsquo;s behalf without telling them.
            </li>
            <li>
              <strong>ClassWatch</strong> observes other people. Do not use it to observe anyone without
              their consent (or their guardian&rsquo;s, where that applies). You are responsible for getting
              consent and for following the laws and the rules of your school, workplace and country,
              including rules on cameras and recording.
            </li>
            <li>
              Screens shown to ClassWatch are sent to Anthropic. Tell the people in the room that this
              happens.
            </li>
          </ul>
        </section>

        <section className={styles.section}>
          <h2>No promise of availability</h2>
          <p>
            Onitry may stop working, change or be removed at any time. It depends on things outside the
            project, including macOS, the Anthropic API and the Python packages it uses. There is no support
            commitment. You can report problems on{" "}
            <a href={ISSUES_URL} target="_blank" rel="noreferrer">
              GitHub Issues
            </a>
            . Reports are read when there is time, with no promise of a reply. This website can also go offline.
          </p>
        </section>

        <section className={styles.section}>
          <h2>Privacy and changes</h2>
          <p>
            What Onitry does with your data is described on the <a href="#/privacy">Privacy</a> page. If
            these terms change, the date at the top changes.
          </p>
          <p className={styles.footerNav}>
            <a href="#/privacy">Privacy</a> &middot; <a href="#/about">About</a> &middot; <a href="#/docs">Docs</a>
          </p>
        </section>
      </div>
    </main>
  );
}
