import datetime
import os
import queue
import random
import subprocess
import threading
import tkinter as tk
from tkinter import ttk

import keyring

import config
from alerts import notifier
from core import context as context_log
from core import status as status_file
from core.check import run_check
from core.interval import AdaptiveInterval

KEYCHAIN_SERVICE = "onitry"
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

RESOLUTIONS = {
    "1280px — high detail": 1280,
    "800px  — medium":       800,
    "512px  — low":          512,
    "320px  — minimal":      320,
}

_TYPING_SENTENCES = [
    "I will stop getting distracted and focus on the task I set out to complete today.",
    "Every minute I waste is a minute I cannot get back, so I choose to stay on track.",
    "Distractions are temporary but the work I finish today will matter tomorrow and beyond.",
    "I am capable of deep focus and I recommit right now to the task in front of me.",
    "The sooner I get back to work the sooner I will feel the satisfaction of finishing.",
    "Staying on task is hard but it is the only way to make real progress on my goals.",
    "I acknowledge I lost focus and I am now making the active choice to return to work.",
    "Short breaks are fine but right now it is time to close distractions and get things done.",
    "My future self will thank me for pushing through this moment and staying productive.",
    "Getting back on track now means I will have more free time later when the work is done.",
]

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


class OnitryApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Onitry")
        self.root.resizable(False, False)
        self.root.configure(bg=BG)

        self._stop_event = threading.Event()
        self._paused     = threading.Event()   # set while interrupt popup is open
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

        # ── Resolution ──
        tk.Label(outer, text="Resolution:", **lbl_opts).grid(row=2, column=0, sticky="w", pady=5)
        self.res_var = tk.StringVar(value=list(RESOLUTIONS.keys())[0])
        res_menu = ttk.Combobox(
            outer, textvariable=self.res_var,
            values=list(RESOLUTIONS.keys()),
            state="readonly", width=42,
        )
        res_menu.grid(row=2, column=1, sticky="ew", pady=5, ipady=3)

        # ── API Key ──
        self._key_status_var = tk.StringVar()
        self._refresh_key_status_label()
        tk.Label(outer, text="API Key:", **lbl_opts).grid(row=3, column=0, sticky="w", pady=5)
        key_row = tk.Frame(outer, bg=BG)
        key_row.grid(row=3, column=1, sticky="ew", pady=5)
        tk.Label(key_row, textvariable=self._key_status_var, bg=BG, fg=FG2, anchor="w").pack(side="left")
        _Btn(key_row, text="Set Key", command=self._open_key_dialog,
             bg=BG, fg=BLUE, hover=BG2, font=("Helvetica", 11), padx=6, pady=2,
             ).pack(side="left", padx=(6, 0))

        # ── Divider ──
        tk.Frame(outer, bg=BG3, height=1).grid(row=4, column=0, columnspan=2, sticky="ew", pady=(8, 4))

        # ── Start/Stop button ──
        self.btn = _Btn(outer, text="Start Monitoring", command=self._toggle,
                        bg=GREEN, hover=GREEN_HV)
        self.btn.grid(row=5, column=0, columnspan=2, pady=(6, 4))

        # ── Status ──
        self.status_var = tk.StringVar(value="Idle")
        self.status_label = tk.Label(
            outer, textvariable=self.status_var,
            bg=BG, fg=STATUS_COLORS["idle"],
            font=("Helvetica", 15, "bold"),
        )
        self.status_label.grid(row=6, column=0, columnspan=2, pady=(2, 8))

        # ── Log (Text + dark scrollbar) ──
        log_frame = tk.Frame(outer, bg=BG2, highlightthickness=1, highlightbackground=BG3)
        log_frame.grid(row=7, column=0, columnspan=2, sticky="nsew", pady=(0, 4))

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
        max_width = RESOLUTIONS[self.res_var.get()]

        self._stop_event.clear()
        self._running = True
        self.btn.relabel("Stop Monitoring")
        self.btn.recolor(RED, hover=RED_HV)
        self.task_entry.config(state="disabled")

        thread = threading.Thread(target=self._monitor_loop, args=(task, max_width), daemon=True)
        thread.start()

        self._enqueue_log(f"Started — {task}")
        self._enqueue_log(f"Model: {config.MODEL}  |  Max interval: {MAX_INTERVAL}s")

    def _stop(self):
        self._stop_event.set()
        self._paused.clear()
        self._running = False
        self.btn.relabel("Start Monitoring")
        self.btn.recolor(GREEN, hover=GREEN_HV)
        self.task_entry.config(state="normal")
        self._enqueue_status("Stopped", STATUS_COLORS["stopped"])
        self._enqueue_log("Monitoring stopped.")
        status_file.write(config.STATUS_FILE, "idle")

    # ── Monitor loop (background thread) ─────────────────────────────────────

    def _monitor_loop(self, task: str, max_width: int = 1280):
        import time

        context_log.init_log(config.CONTEXT_FILE, task)

        interval = AdaptiveInterval(MIN_INTERVAL, MAX_INTERVAL, INTERVAL_STEP, JITTER_LO, JITTER_HI)

        self._stop_event.wait(timeout=5)  # brief grace period before first check

        while not self._stop_event.is_set():
            # Wait while an interrupt popup is showing
            while self._paused.is_set() and not self._stop_event.is_set():
                self._stop_event.wait(timeout=0.5)

            if self._stop_event.is_set():
                break

            t0 = time.time()
            try:
                context = context_log.read_tail(config.CONTEXT_FILE)
                result = run_check(task, context, max_width)

                on_task = result.get("onTask", True)
                activity = result.get("activity", "unknown")
                reminder = result.get("reminder", "")
                interrupt = result.get("interrupt", False)

                if on_task:
                    self._enqueue_status("ON TASK", STATUS_COLORS["on_task"])
                    context_log.append(config.CONTEXT_FILE, activity)
                    status_file.write(config.STATUS_FILE, "on_task", task, activity)
                else:
                    self._enqueue_status("OFF TASK", STATUS_COLORS["off_task"])
                    context_log.append(config.CONTEXT_FILE, f"[OFF-TASK] {activity}")
                    status_file.write(config.STATUS_FILE, "off_task", task, activity)
                    interval.snap_down()
                msg = reminder if reminder else ""
                if reminder:
                    self._enqueue_log(f"  → {reminder}")
                    notifier.alert_off_task(task, reminder, interrupt)
                    if interrupt:
                        self._log_queue.put(("popup", msg))

            except Exception as exc:
                self._enqueue_log(f"Error: {exc}")
                activity = "error"
                on_task = True  # don't fire alerts on API errors

            elapsed = time.time() - t0
            sleep_seconds, effective = interval.sample_wait(elapsed)
            self._enqueue_log(f"{'ON TASK' if on_task else 'OFF TASK'}: {activity}  (next in {effective:.0f}s)")
            self._stop_event.wait(timeout=sleep_seconds)

            interval.step_up()

    # ── Helpers ───────────────────────────────────────────────────────────────

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

    def _dismiss_popup(self, pop):
        self._paused.clear()
        if pop.winfo_exists():
            pop.destroy()

    def _show_popup(self, message: str):
        # Close any existing popup first
        if hasattr(self, "_popup") and self._popup and self._popup.winfo_exists():
            self._popup.destroy()

        self._paused.set()   # pause the monitor loop until dismissed

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

        sentence = random.choice(_TYPING_SENTENCES)

        frame = tk.Frame(pop, bg="#2a0a0a", padx=24, pady=20)
        frame.pack(fill="both", expand=True)

        tk.Label(frame, text="⚠  Off Task", bg="#2a0a0a", fg="#f85149",
                 font=("Helvetica", 15, "bold")).pack(anchor="w")

        tk.Label(frame, text=message, bg="#2a0a0a", fg="#e8e8e8",
                 font=("Helvetica", 12), wraplength=360, justify="left",
                 ).pack(anchor="w", pady=(6, 12))

        tk.Label(frame, text="Type this to get back to work:",
                 bg="#2a0a0a", fg="#888888", font=("Helvetica", 10)).pack(anchor="w")

        tk.Label(frame, text=sentence, bg="#1a0505", fg="#f8c8c8",
                 font=("Menlo", 10), wraplength=360, justify="left",
                 padx=8, pady=6, relief="flat",
                 ).pack(fill="x", pady=(4, 8))

        entry_var = tk.StringVar()
        entry = tk.Entry(frame, textvariable=entry_var,
                         bg="#3a0a0a", fg="white", insertbackground="white",
                         font=("Menlo", 10), relief="flat",
                         highlightthickness=1, highlightbackground="#6e1a1a")
        entry.pack(fill="x", ipady=5, pady=(0, 10))
        entry.focus_force()

        btn = _Btn(frame, text="Back to work", command=lambda: self._dismiss_popup(pop),
                   bg="#3a1a1a", fg="#666666", hover="#3a1a1a",
                   font=("Helvetica", 11, "bold"), padx=12, pady=6)
        btn.pack(anchor="w")

        def _on_type(*_):
            typed = entry_var.get()
            if typed == sentence:
                btn.recolor("#6e1a1a", hover="#8b2020")
                btn._lbl.configure(fg="white")
                btn._cmd = lambda: self._dismiss_popup(pop)
            else:
                btn.recolor("#3a1a1a", hover="#3a1a1a")
                btn._lbl.configure(fg="#666666")
                btn._cmd = lambda: None

        entry_var.trace_add("write", _on_type)

        pop.lift()
        pop.focus_force()
        # Auto-dismiss after 90 s if not manually closed
        pop.after(90_000, lambda: self._dismiss_popup(pop) if pop.winfo_exists() else None)


def main():
    import multiprocessing
    multiprocessing.set_start_method("spawn", force=True)
    root = tk.Tk()
    OnitryApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
