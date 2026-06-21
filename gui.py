import tkinter as tk
from tkinter import ttk
import threading
import queue
import datetime
import os
import random
import subprocess

import keyring
import config
from capture import screen
from capture import keylogger_proc as keylogger
from ai import client as ai_client
from alerts import notifier

KEYCHAIN_SERVICE = "monitry"
KEYCHAIN_USER    = "anthropic_api_key"

# ── Adaptive interval ─────────────────────────────────────────────────────────
MAX_INTERVAL  = 120   # seconds — normal cruising speed
MIN_INTERVAL  = 10    # seconds — snapped to on off-task detection
INTERVAL_STEP = 10    # seconds added per check when stepping back up
JITTER_LO     = 0.4   # multiplier range low
JITTER_HI     = 1.6   # multiplier range high

# ── Colour palette ────────────────────────────────────────────────────────────
BG       = "#1e1e1e"   # window / outer background
BG2      = "#2a2a2a"   # widget background (entries, log)
BG3      = "#333333"   # hover / border
FG       = "#e8e8e8"   # primary text
FG2      = "#888888"   # secondary / muted
GREEN    = "#2ea043"   # start button
GREEN_HV = "#238636"   # start hover
RED      = "#b91c1c"   # stop button
RED_HV   = "#991b1b"   # stop hover
BLUE     = "#4493f8"   # "Set Key" link

class _Btn(tk.Frame):
    """Label-based button — tk.Button ignores bg on macOS, this doesn't."""
    def __init__(self, parent, text, command, bg, fg="white", hover=None,
                 font=("Helvetica", 12, "bold"), padx=18, pady=8):
        super().__init__(parent, bg=bg, cursor="hand2")
        self._bg    = bg
        self._hover = hover or bg
        self._cmd   = command
        self._lbl   = tk.Label(self, text=text, bg=bg, fg=fg,
                               padx=padx, pady=pady, font=font, cursor="hand2")
        self._lbl.pack()
        for w in (self, self._lbl):
            w.bind("<Enter>",    self._enter)
            w.bind("<Leave>",    self._leave)
            w.bind("<Button-1>", self._click)

    def _enter(self, _): self._set_bg(self._hover)
    def _leave(self, _): self._set_bg(self._bg)
    def _click(self, _): self._cmd()

    def _set_bg(self, c):
        tk.Frame.configure(self, bg=c)
        self._lbl.configure(bg=c)

    def recolor(self, bg, hover=None):
        self._bg    = bg
        self._hover = hover or bg
        self._set_bg(bg)

    def relabel(self, text):
        self._lbl.configure(text=text)


MODELS = {
    "Haiku 4.5  — ~$0.09/hr": "claude-haiku-4-5-20251001",
    "Sonnet 4.6 — ~$0.28/hr": "claude-sonnet-4-6",
    "Opus 4.8   — ~$0.47/hr": "claude-opus-4-8",
}

STATUS_COLORS = {
    "idle":    FG2,
    "on_task": "#3fb950",
    "off_task":"#f85149",
    "stopped": FG2,
}


def _apply_ttk_style():
    style = ttk.Style()
    style.theme_use("default")

    # Combobox
    style.configure("TCombobox",
        fieldbackground=BG2, background=BG2,
        foreground=FG, selectbackground=BG3,
        selectforeground=FG, bordercolor=BG3,
        arrowcolor=FG, relief="flat",
    )
    style.map("TCombobox",
        fieldbackground=[("readonly", BG2)],
        foreground=[("readonly", FG)],
    )

    # Scrollbar — thin, dark
    style.configure("Dark.Vertical.TScrollbar",
        gripcount=0, background=BG3,
        darkcolor=BG, lightcolor=BG,
        troughcolor=BG2, bordercolor=BG2,
        arrowcolor=FG2, relief="flat",
        width=8,
    )
    style.map("Dark.Vertical.TScrollbar",
        background=[("active", "#555555")],
    )


class MonitryApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Monitry")
        self.root.resizable(False, False)
        self.root.configure(bg=BG)

        self._stop_event = threading.Event()
        self._log_queue: queue.Queue = queue.Queue()
        self._running = False

        _apply_ttk_style()
        self._load_api_key()
        self._build_ui()
        self._poll_queue()

    def _build_ui(self):
        outer = tk.Frame(self.root, bg=BG, padx=18, pady=14)
        outer.pack(fill="both", expand=True)

        lbl_opts = dict(bg=BG, fg=FG, anchor="w", width=8)

        # ── Task ──
        tk.Label(outer, text="Task:", **lbl_opts).grid(row=0, column=0, sticky="w", pady=5)
        self.task_var = tk.StringVar()
        self.task_entry = tk.Entry(
            outer, textvariable=self.task_var,
            width=44, relief="flat",
            bg=BG2, fg=FG, insertbackground=FG,
            highlightthickness=1, highlightbackground=BG3, highlightcolor=BLUE,
        )
        self.task_entry.grid(row=0, column=1, sticky="ew", pady=5, ipady=4)
        self.task_entry.focus()

        # ── Model ──
        tk.Label(outer, text="Model:", **lbl_opts).grid(row=1, column=0, sticky="w", pady=5)
        self.model_var = tk.StringVar(value=list(MODELS.keys())[0])
        model_menu = ttk.Combobox(
            outer, textvariable=self.model_var,
            values=list(MODELS.keys()),
            state="readonly", width=42,
        )
        model_menu.grid(row=1, column=1, sticky="ew", pady=5, ipady=3)

        # ── API Key ──
        self._key_status_var = tk.StringVar()
        self._refresh_key_status_label()
        tk.Label(outer, text="API Key:", **lbl_opts).grid(row=2, column=0, sticky="w", pady=5)
        key_row = tk.Frame(outer, bg=BG)
        key_row.grid(row=2, column=1, sticky="ew", pady=5)
        tk.Label(key_row, textvariable=self._key_status_var, bg=BG, fg=FG2, anchor="w").pack(side="left")
        _Btn(key_row, text="Set Key", command=self._open_key_dialog,
             bg=BG, fg=BLUE, hover=BG2, font=("Helvetica", 11), padx=6, pady=2,
             ).pack(side="left", padx=(6, 0))

        # ── Divider ──
        tk.Frame(outer, bg=BG3, height=1).grid(row=3, column=0, columnspan=2, sticky="ew", pady=(8, 4))

        # ── Start/Stop button ──
        self.btn = _Btn(outer, text="Start Monitoring", command=self._toggle,
                        bg=GREEN, hover=GREEN_HV)
        self.btn.grid(row=4, column=0, columnspan=2, pady=(6, 4))

        # ── Status ──
        self.status_var = tk.StringVar(value="Idle")
        self.status_label = tk.Label(
            outer, textvariable=self.status_var,
            bg=BG, fg=STATUS_COLORS["idle"],
            font=("Helvetica", 15, "bold"),
        )
        self.status_label.grid(row=5, column=0, columnspan=2, pady=(2, 8))

        # ── Log (Text + dark scrollbar) ──
        log_frame = tk.Frame(outer, bg=BG2, highlightthickness=1, highlightbackground=BG3)
        log_frame.grid(row=6, column=0, columnspan=2, sticky="nsew", pady=(0, 4))

        self.log = tk.Text(
            log_frame, width=56, height=13,
            state="disabled", font=("Menlo", 10),
            bg=BG2, fg="#cccccc", insertbackground=FG,
            relief="flat", bd=0,
            wrap="word", padx=6, pady=4,
        )
        scrollbar = ttk.Scrollbar(log_frame, orient="vertical",
                                   command=self.log.yview,
                                   style="Dark.Vertical.TScrollbar")
        self.log.configure(yscrollcommand=scrollbar.set)

        self.log.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        outer.columnconfigure(1, weight=1)

    # ── API Key (Keychain) ────────────────────────────────────────────────────

    def _load_api_key(self):
        stored = keyring.get_password(KEYCHAIN_SERVICE, KEYCHAIN_USER)
        if stored:
            config.ANTHROPIC_API_KEY = stored

    def _refresh_key_status_label(self):
        stored = keyring.get_password(KEYCHAIN_SERVICE, KEYCHAIN_USER)
        env = os.environ.get("ANTHROPIC_API_KEY", "")
        if stored:
            self._key_status_var.set("Saved in Keychain ✓")
        elif env:
            self._key_status_var.set("From environment variable")
        else:
            self._key_status_var.set("Not set")

    def _open_key_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Set API Key")
        dialog.resizable(False, False)
        dialog.configure(bg=BG)
        dialog.minsize(420, 160)

        frame = tk.Frame(dialog, bg=BG, padx=18, pady=14)
        frame.pack(fill="both", expand=True)

        tk.Label(frame, text="Anthropic API Key:", bg=BG, fg=FG, anchor="w").pack(fill="x", pady=(0, 6))
        entry = tk.Entry(
            frame, show="•", width=50,
            bg=BG2, fg=FG, insertbackground=FG,
            relief="flat",
            highlightthickness=1, highlightbackground=BG3, highlightcolor=BLUE,
        )
        entry.pack(fill="x", ipady=4, pady=(0, 4))

        existing = keyring.get_password(KEYCHAIN_SERVICE, KEYCHAIN_USER) or ""
        if existing:
            entry.insert(0, existing)

        status_lbl = tk.Label(frame, text="", bg=BG, fg=FG2, anchor="w")
        status_lbl.pack(fill="x")

        btn_frame = tk.Frame(frame, bg=BG)
        btn_frame.pack(pady=(10, 0))

        def save():
            key = entry.get().strip()
            if not key:
                status_lbl.config(text="Key cannot be empty.", fg="#f85149")
                return
            keyring.set_password(KEYCHAIN_SERVICE, KEYCHAIN_USER, key)
            config.ANTHROPIC_API_KEY = key
            self._refresh_key_status_label()
            status_lbl.config(text="Saved to macOS Keychain.", fg="#3fb950")
            dialog.after(800, dialog.destroy)

        _Btn(btn_frame, text="Save", command=save,
             bg=GREEN, hover=GREEN_HV, padx=12, pady=5).pack(side="left", padx=(0, 8))
        _Btn(btn_frame, text="Cancel", command=dialog.destroy,
             bg=BG3, fg=FG, hover="#444", padx=12, pady=5).pack(side="left")

        entry.bind("<Return>", lambda _: save())
        dialog.grab_set()
        entry.focus_force()

    # ── Toggle ────────────────────────────────────────────────────────────────

    def _toggle(self):
        if self._running:
            self._stop()
        else:
            self._start()

    def _start(self):
        task = self.task_var.get().strip()
        if not task:
            self.task_entry.config(highlightbackground="#f85149")
            return
        self.task_entry.config(highlightbackground=BG3)

        if not config.ANTHROPIC_API_KEY:
            self._enqueue_log("ERROR: ANTHROPIC_API_KEY is not set — click 'Set Key'.")
            return

        config.MODEL = MODELS[self.model_var.get()]

        self._stop_event.clear()
        self._running = True
        self.btn.relabel("Stop Monitoring")
        self.btn.recolor(RED, hover=RED_HV)
        self.task_entry.config(state="disabled")

        keylogger.start()  # must be on the main thread on macOS

        thread = threading.Thread(target=self._monitor_loop, args=(task,), daemon=True)
        thread.start()

        self._enqueue_log(f"Started — {task}")
        self._enqueue_log(f"Model: {config.MODEL}  |  Max interval: {MAX_INTERVAL}s")

    def _stop(self):
        self._stop_event.set()
        self._running = False
        keylogger.stop()
        self.btn.relabel("Start Monitoring")
        self.btn.recolor(GREEN, hover=GREEN_HV)
        self.task_entry.config(state="normal")
        self._enqueue_status("Stopped", STATUS_COLORS["stopped"])
        self._enqueue_log("Monitoring stopped.")
        self._write_status("idle")

    # ── Monitor loop (background thread) ─────────────────────────────────────

    def _monitor_loop(self, task: str):
        import time

        os.makedirs(os.path.dirname(config.CONTEXT_FILE), exist_ok=True)
        with open(config.CONTEXT_FILE, "w") as f:
            ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"Session started: {ts}\nTask: {task}\n\n")

        interval = MIN_INTERVAL  # ramp up to MAX_INTERVAL over time

        while not self._stop_event.is_set():
            t0 = time.time()
            try:
                screenshot_b64 = screen.grab_screenshot()
                keylog = keylogger.get_recent(config.KEYLOG_WINDOW)
                context = self._read_context()

                result = ai_client.analyze(task, screenshot_b64, keylog, context)

                on_task = result.get("onTask", True)
                activity = result.get("activity", "unknown")
                reminder = result.get("reminder", "")

                if on_task:
                    self._enqueue_status("ON TASK", STATUS_COLORS["on_task"])
                    self._append_context(activity)
                    self._write_status("on_task", task, activity)
                else:
                    self._enqueue_status("OFF TASK", STATUS_COLORS["off_task"])
                    msg = reminder if reminder else f"Get back to: {task}"
                    if reminder:
                        self._enqueue_log(f"  → {reminder}")
                    notifier.alert_off_task(task, activity, reminder)
                    self._log_queue.put(("popup", msg))
                    self._append_context(f"[OFF-TASK] {activity}")
                    self._write_status("off_task", task, activity)
                    interval = MIN_INTERVAL  # snap down; will step back up each loop

            except Exception as exc:
                self._enqueue_log(f"Error: {exc}")
                activity = "error"
                on_task = True  # don't fire alerts on API errors

            # Jittered sleep: multiply base interval by 0.4–1.6, floor at 10s
            effective = max(MIN_INTERVAL, interval * random.uniform(JITTER_LO, JITTER_HI))
            elapsed = time.time() - t0
            self._enqueue_log(f"{'ON TASK' if on_task else 'OFF TASK'}: {activity}  (next in {effective:.0f}s)")
            self._stop_event.wait(timeout=max(0, effective - elapsed))

            # Step interval back toward max after every check
            interval = min(interval + INTERVAL_STEP, MAX_INTERVAL)

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _read_context(self) -> str:
        if not os.path.exists(config.CONTEXT_FILE):
            return ""
        with open(config.CONTEXT_FILE) as f:
            lines = [l.rstrip() for l in f if l.strip()]
        return "\n".join(lines[-10:])

    def _append_context(self, activity: str):
        os.makedirs(os.path.dirname(config.CONTEXT_FILE), exist_ok=True)
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        with open(config.CONTEXT_FILE, "a") as f:
            f.write(f"[{ts}] {activity}\n")

    def _write_status(self, status: str, task: str = "", activity: str = ""):
        import json
        os.makedirs(os.path.dirname(config.STATUS_FILE), exist_ok=True)
        with open(config.STATUS_FILE, "w") as f:
            json.dump({"status": status, "task": task, "activity": activity}, f)

    def _enqueue_log(self, msg: str):
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        self._log_queue.put(("log", f"[{ts}] {msg}"))

    def _enqueue_status(self, text: str, color: str):
        self._log_queue.put(("status", text, color))

    def _poll_queue(self):
        try:
            while True:
                item = self._log_queue.get_nowait()
                if item[0] == "log":
                    self.log.config(state="normal")
                    self.log.insert("end", item[1] + "\n")
                    self.log.see("end")
                    self.log.config(state="disabled")
                elif item[0] == "status":
                    self.status_var.set(item[1])
                    self.status_label.config(fg=item[2])
                elif item[0] == "popup":
                    self._show_popup(item[1])
        except queue.Empty:
            pass
        self.root.after(200, self._poll_queue)

    def _show_popup(self, message: str):
        # Close any existing popup first
        if hasattr(self, "_popup") and self._popup and self._popup.winfo_exists():
            self._popup.destroy()

        # Force this process to the front so the popup appears above other apps
        subprocess.Popen([
            "osascript", "-e",
            f"tell application \"System Events\" to set frontmost of first process"
            f" whose unix id is {os.getpid()} to true"
        ])

        pop = tk.Toplevel(self.root)
        pop.title("")
        pop.configure(bg="#2a0a0a")
        pop.resizable(False, False)
        pop.wm_attributes("-topmost", True)
        self._popup = pop

        frame = tk.Frame(pop, bg="#2a0a0a", padx=24, pady=20)
        frame.pack(fill="both", expand=True)

        tk.Label(frame, text="⚠  Off Task", bg="#2a0a0a", fg="#f85149",
                 font=("Helvetica", 15, "bold")).pack(anchor="w")

        tk.Label(frame, text=message, bg="#2a0a0a", fg="#e8e8e8",
                 font=("Helvetica", 12), wraplength=300, justify="left",
                 ).pack(anchor="w", pady=(6, 14))

        _Btn(frame, text="Back to work", command=pop.destroy,
             bg="#6e1a1a", fg="white", hover="#8b2020",
             font=("Helvetica", 11, "bold"), padx=12, pady=6,
             ).pack(anchor="w")

        pop.lift()
        pop.focus_force()
        # Auto-dismiss after 30 s if not manually closed
        pop.after(30_000, lambda: pop.destroy() if pop.winfo_exists() else None)


def main():
    import multiprocessing
    multiprocessing.set_start_method("spawn", force=True)
    root = tk.Tk()
    MonitryApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
