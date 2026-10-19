import datetime
import sys
import time

import config
from alerts import notifier
from core import context as context_log
from core import idle
from core.check import run_check
from core.interval import AdaptiveInterval

IDLE_THRESHOLD_SECONDS = 300  # skip checks (and their API cost) after 5 min with no mouse/keyboard input


def check_api_key():
    if not config.ANTHROPIC_API_KEY:
        print("Error: ANTHROPIC_API_KEY environment variable is not set.")
        print("Export it before running: export ANTHROPIC_API_KEY=your_key_here")
        sys.exit(1)


def run(task: str):
    print("\nFull Focus started.")
    print(f"Task: {task}")
    print(f"Checking every {config.CHECK_INTERVAL}s. Press Ctrl+C to stop.\n")

    context_log.init_log(config.CONTEXT_FILE, task)
    interval = AdaptiveInterval(min_interval=config.CHECK_INTERVAL)
    was_idle = False

    try:
        while True:
            # Idle — skip the check (and its API cost) while away from keyboard/mouse
            if idle.get_idle_seconds() >= IDLE_THRESHOLD_SECONDS:
                if not was_idle:
                    print(f"Away from keyboard — pausing checks (idle {IDLE_THRESHOLD_SECONDS // 60}m+)")
                    was_idle = True
                time.sleep(5.0)
                continue
            if was_idle:
                print("Welcome back — resuming checks.")
                was_idle = False

            t0 = time.time()
            try:
                print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Capturing...")

                context = context_log.read_tail(config.CONTEXT_FILE)
                result = run_check(task, context)

                on_task = result.get("onTask", True)
                activity = result.get("activity", "unknown")
                reminder = result.get("reminder", "")
                interrupt = result.get("interrupt", False)

                status = "ON TASK" if on_task else "OFF TASK"
                print(f"  {status}: {activity}")

                if on_task:
                    context_log.append(config.CONTEXT_FILE, activity)
                else:
                    print(f"  Reminder: {reminder}")
                    notifier.alert_off_task(task, reminder, interrupt)
                    context_log.append(config.CONTEXT_FILE, f"[OFF-TASK] {activity}")
                    interval.snap_down()

            except KeyboardInterrupt:
                raise
            except Exception as e:
                print(f"  Error during check: {e}")

            elapsed = time.time() - t0
            sleep_seconds, _ = interval.sample_wait(elapsed)
            time.sleep(sleep_seconds)
            interval.step_up()

    except KeyboardInterrupt:
        print("\nFull Focus stopped.")


if __name__ == "__main__":
    check_api_key()

    if len(sys.argv) > 1:
        task = " ".join(sys.argv[1:])
    else:
        task = input("What task do you want to work on? ").strip()
        if not task:
            print("No task specified. Exiting.")
            sys.exit(1)

    run(task)
