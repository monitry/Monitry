"""ClassWatch — points a camera at a room, finds every laptop/monitor screen
in view, and builds a per-screen activity log over time.

Unlike gui.py/cli.py (which watch the user's OWN screen and nag them about
it), this is a passive observer: no popups, no TTS, no interrupts — it just
logs what's visible on each tracked screen and writes a report.

Needs the room/ extra dependencies (ultralytics — pulls in torch):
    pip install -r requirements-room.txt

Usage:
    python room_cli.py
    python room_cli.py --task "working on the lab assignment" --interval 20
    python room_cli.py --camera 1 --conf 0.3 --max-cycles 5
"""
import argparse
import os
import sys
import time

import cv2

import config
from room.analyzer import session_cost
from room.session import RoomSession


def check_api_key():
    if not config.ANTHROPIC_API_KEY:
        print("Error: ANTHROPIC_API_KEY environment variable is not set.")
        print("Export it before running: export ANTHROPIC_API_KEY=your_key_here")
        sys.exit(1)


def run(camera_index: int, interval: float, conf: float, task: str, report_path: str, max_cycles: int | None):
    print("\nClassWatch started.")
    print(f"Watching camera {camera_index} every {interval:.0f}s. Press Ctrl+C to stop.\n")
    if task:
        print(f"Shared task for every detected screen: {task}\n")
    else:
        print("No task given — logging activity only, no on/off-task judgment.\n")

    cap = cv2.VideoCapture(camera_index)
    if not cap.isOpened():
        sys.exit(f"Could not open camera {camera_index}")

    session = RoomSession(conf=conf)
    cycle = 0

    try:
        while max_cycles is None or cycle < max_cycles:
            cycle += 1
            t0 = time.time()

            ok, frame = cap.read()
            if not ok:
                print("  Camera read failed, retrying...")
                time.sleep(1)
                continue

            # A shared task applies to every screen currently tracked this cycle.
            session.tasks = dict.fromkeys(session.tracker.active_ids, task) if task else {}
            results = session.run_cycle(frame)

            # New screens that just appeared this cycle won't be in tasks yet — backfill
            # so the *next* cycle judges them too (this cycle described them without one).
            if task:
                session.tasks = dict.fromkeys(session.tracker.active_ids, task)

            ts = time.strftime("%H:%M:%S")
            if not results:
                print(f"[{ts}] No screens detected this cycle.")
            for screen_id, result in results.items():
                on_task = result.get("onTask")
                tag = "ON TASK" if on_task else "OFF TASK" if on_task is False else "—"
                print(f"[{ts}] {screen_id} ({tag}): {result.get('activity', 'unknown')}")

            elapsed = time.time() - t0
            time.sleep(max(0.0, interval - elapsed))

    except KeyboardInterrupt:
        print("\nClassWatch stopped.")
    finally:
        cap.release()
        report_dir = os.path.dirname(report_path)
        if report_dir:
            os.makedirs(report_dir, exist_ok=True)
        with open(report_path, "w") as f:
            f.write(session.report.to_markdown())
        print(f"\nReport written to {report_path}")
        print(f"Total spend this session: ${session_cost():.3f}")


if __name__ == "__main__":
    check_api_key()

    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--camera", type=int, default=0, help="camera index (default: 0)")
    parser.add_argument("--interval", type=float, default=15.0, help="seconds between capture cycles (default: 15)")
    parser.add_argument("--conf", type=float, default=0.25, help="YOLO detection confidence threshold")
    parser.add_argument("--task", default="", help="shared task for every screen — omit to just log activity")
    parser.add_argument("--report-path", default="data/room/report.md", help="where to write the final report")
    parser.add_argument("--max-cycles", type=int, default=None, help="stop after N cycles (default: run forever)")
    args = parser.parse_args()

    run(args.camera, args.interval, args.conf, args.task, args.report_path, args.max_cycles)
