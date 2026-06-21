import os
import sys
import time
import datetime

import config
from capture import screen, keylogger
from ai import client as ai_client
from alerts import notifier


def read_context() -> str:
    if not os.path.exists(config.CONTEXT_FILE):
        return ""
    with open(config.CONTEXT_FILE, "r") as f:
        content = f.read()
    # Return only the tail to stay within token budget
    return content[-config.CONTEXT_MAX_CHARS:]


def append_context(activity: str):
    os.makedirs(os.path.dirname(config.CONTEXT_FILE), exist_ok=True)
    ts = datetime.datetime.now().strftime("%H:%M:%S")
    with open(config.CONTEXT_FILE, "a") as f:
        f.write(f"[{ts}] {activity}\n")


def check_api_key():
    if not config.ANTHROPIC_API_KEY:
        print("Error: ANTHROPIC_API_KEY environment variable is not set.")
        print("Export it before running: export ANTHROPIC_API_KEY=your_key_here")
        sys.exit(1)


def run(task: str):
    print(f"\nMonitry started.")
    print(f"Task: {task}")
    print(f"Checking every {config.CHECK_INTERVAL}s. Press Ctrl+C to stop.\n")

    keylogger.start()

    # Clear/create context file for this session
    os.makedirs(os.path.dirname(config.CONTEXT_FILE), exist_ok=True)
    with open(config.CONTEXT_FILE, "w") as f:
        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"Session started: {ts}\nTask: {task}\n\n")

    try:
        while True:
            loop_start = time.time()
            try:
                print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Capturing...")

                screenshot_b64 = screen.grab_screenshot()
                keylog = keylogger.get_recent(config.KEYLOG_WINDOW)
                context = read_context()

                result = ai_client.analyze(task, screenshot_b64, keylog, context)

                on_task = result.get("onTask", True)
                activity = result.get("activity", "unknown")
                reminder = result.get("reminder", "")

                status = "ON TASK" if on_task else "OFF TASK"
                print(f"  {status}: {activity}")

                if on_task:
                    append_context(activity)
                else:
                    print(f"  Reminder: {reminder}")
                    notifier.alert_off_task(task, activity, reminder)
                    append_context(f"[OFF-TASK] {activity}")

            except KeyboardInterrupt:
                raise
            except Exception as e:
                print(f"  Error during check: {e}")

            elapsed = time.time() - loop_start
            sleep_time = max(0, config.CHECK_INTERVAL - elapsed)
            time.sleep(sleep_time)

    except KeyboardInterrupt:
        print("\nMonitry stopped.")
        keylogger.stop()


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
