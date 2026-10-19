"""
Full Focus menu bar app.

Run this instead of gui.py — it lives in the menu bar and spawns the
GUI window on demand. The GUI writes status to data/status.json which
this app polls every 2 seconds to update the icon.
"""
import json
import os
import subprocess
import sys
import threading

import rumps

import config
from core import context as context_log

PYTHON = sys.executable
GUI_SCRIPT = os.path.join(os.path.dirname(__file__), "gui.py")

ICONS = {
    "idle":     "M",
    "on_task":  "✓",
    "off_task": "⚠",
    "paused":   "⏸",
}


class FullFocusBar(rumps.App):
    def __init__(self):
        super().__init__(name="Full Focus", title=ICONS["idle"], quit_button=None)

        self._gui_proc    = None
        self._last_status = {}
        self._reply_pending = None  # set by chat thread, consumed by timer

        self._status_item = rumps.MenuItem("Not monitoring")
        self._task_item   = rumps.MenuItem("")
        self._cost_item   = rumps.MenuItem("")
        self._open_item   = rumps.MenuItem("Open Full Focus",  callback=self.open_window)
        self._quit_item   = rumps.MenuItem("Quit",          callback=self.quit_app)

        self.menu = [
            self._status_item,
            self._task_item,
            self._cost_item,
            None,
        ]

        # Managed-edition users have no direct Anthropic key — this chat feature
        # calls Anthropic directly, so it's only available in dev/byok builds.
        if config.EDITION != "managed":
            self._chat_item = rumps.MenuItem("Ask Claude...", callback=self.open_chat)
            self.menu.append(self._chat_item)
            self.menu.append(None)

        self.menu.append(self._open_item)
        self.menu.append(None)
        self.menu.append(self._quit_item)

        rumps.Timer(self._poll, 2).start()

    # ── Chat ──────────────────────────────────────────────────────────────────

    def open_chat(self, _):
        task = self._last_status.get("task", "")
        subtitle = f"Session task: {task}" if task else "No active session"

        win = rumps.Window(
            message=subtitle,
            title="Ask Claude",
            default_text="",
            ok="Send",
            cancel="Cancel",
            dimensions=(340, 80),
        )
        response = win.run()
        if not response.clicked or not response.text.strip():
            return

        user_msg = response.text.strip()

        # Show loading indicator in menu bar while API call runs
        self._saved_title = self.title
        self.title = "..."
        self._chat_item.title = "Asking Claude..."
        self._chat_item.set_callback(None)

        threading.Thread(
            target=self._call_claude,
            args=(user_msg, task),
            daemon=True,
        ).start()

    def _call_claude(self, user_msg: str, task: str):
        """Background thread — calls API and stores reply for main thread to show."""
        import anthropic
        import keyring
        try:
            api_key = keyring.get_password("onitry", "anthropic_api_key")
            if not api_key:
                self._reply_pending = ("Error", "API key not set.\nOpen Full Focus and click 'Set Key'.")
                return

            context = context_log.read_tail(config.CONTEXT_FILE)

            system = (
                f"You are Full Focus, a productivity assistant embedded in a menu bar app. "
                f"The user is working on: {task or 'an unspecified task'}.\n"
                f"Recent session activity:\n{context or '(none yet)'}\n\n"
                f"Answer concisely. If asked about progress or activity, refer to the session log above."
            )

            client = anthropic.Anthropic(api_key=api_key)
            msg = client.messages.create(
                model=config.MODEL,
                max_tokens=512,
                system=system,
                messages=[{"role": "user", "content": user_msg}],
            )
            reply = msg.content[0].text.strip()
            self._reply_pending = ("Claude", reply)

        except Exception as exc:
            self._reply_pending = ("Error", str(exc))

    def _show_reply(self, timer):
        """Timer callback — runs on main thread, shows reply window when ready."""
        if self._reply_pending is None:
            return
        title, message = self._reply_pending
        self._reply_pending = None
        timer.stop()

        # Restore menu bar state
        self.title = getattr(self, "_saved_title", ICONS["idle"])
        self._chat_item.title = "Ask Claude..."
        self._chat_item.set_callback(self.open_chat)

        rumps.Window(
            message=message,
            title=title,
            ok="OK",
            cancel=None,
            dimensions=(340, 100),
        ).run()

    # ── Status polling ────────────────────────────────────────────────────────

    def open_window(self, _=None):
        if self._gui_proc is None or self._gui_proc.poll() is not None:
            self._gui_proc = subprocess.Popen([PYTHON, GUI_SCRIPT])

    def quit_app(self, _):
        if self._gui_proc and self._gui_proc.poll() is None:
            self._gui_proc.terminate()
        rumps.quit_application()

    def _poll(self, _):
        # Check for pending chat reply
        if self._reply_pending is not None:
            reply_timer = rumps.Timer(self._show_reply, 0.1)
            reply_timer.start()
            return

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

        status = data.get("status", "idle")
        task   = data.get("task",   "")
        cost   = data.get("cost",   0.0)

        self.title = ICONS.get(status, "M")

        if status == "on_task":
            self._status_item.title = "On task"
        elif status == "off_task":
            self._status_item.title = "Off task ⚠"
        elif status == "paused":
            self._status_item.title = "Paused ⏸"
        else:
            self._status_item.title = "Not monitoring"

        self._task_item.title = task if task else ""
        if status == "idle" or config.EDITION == "managed":
            self._cost_item.title = ""  # managed edition shows remaining time in the GUI instead
        else:
            self._cost_item.title = f"${cost:.3f} spent"


if __name__ == "__main__":
    rumps.debug_mode(True)
    FullFocusBar().run()
