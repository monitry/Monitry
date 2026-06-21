"""
Monitry menu bar app.

Run this instead of gui.py — it lives in the menu bar and spawns the
GUI window on demand. The GUI writes status to data/status.json which
this app polls every 2 seconds to update the icon.
"""
import json
import os
import subprocess
import sys

import rumps
import config

PYTHON = sys.executable
GUI_SCRIPT = os.path.join(os.path.dirname(__file__), "gui.py")

ICONS = {
    "idle":     "M",
    "on_task":  "✓",
    "off_task": "⚠",
}


class MonitryBar(rumps.App):
    def __init__(self):
        super().__init__(name="Monitry", title=ICONS["idle"], quit_button=None)

        self._gui_proc = None
        self._last_status = {}

        self._status_item = rumps.MenuItem("Not monitoring")
        self._task_item   = rumps.MenuItem("")
        self._open_item   = rumps.MenuItem("Open Monitry", callback=self.open_window)
        self._quit_item   = rumps.MenuItem("Quit",         callback=self.quit_app)

        self.menu = [
            self._status_item,
            self._task_item,
            None,
            self._open_item,
            None,
            self._quit_item,
        ]

        rumps.Timer(self._poll, 2).start()

    def open_window(self, _=None):
        if self._gui_proc is None or self._gui_proc.poll() is not None:
            self._gui_proc = subprocess.Popen([PYTHON, GUI_SCRIPT])

    def quit_app(self, _):
        if self._gui_proc and self._gui_proc.poll() is None:
            self._gui_proc.terminate()
        rumps.quit_application()

    def _poll(self, _):
        if not os.path.exists(config.STATUS_FILE):
            return
        try:
            with open(config.STATUS_FILE) as f:
                data = json.load(f)
        except Exception:
            return

        if data == self._last_status:
            return
        self._last_status = data

        status   = data.get("status",   "idle")
        task     = data.get("task",     "")
        activity = data.get("activity", "")

        self.title = ICONS.get(status, "M")

        if status == "on_task":
            self._status_item.title = "On task"
        elif status == "off_task":
            self._status_item.title = "Off task ⚠"
        else:
            self._status_item.title = "Not monitoring"

        self._task_item.title = task if task else ""


if __name__ == "__main__":
    MonitryBar().run()
