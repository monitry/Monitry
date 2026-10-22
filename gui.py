import datetime
import json
import os
import queue
import random
import subprocess
import threading
import time
import tkinter as tk
import webbrowser
from tkinter import ttk

import httpx
import keyring

import config
from ai import review as review_ai
from ai.client import DailyLimitReached
from alerts import notifier
from core import auth as google_auth
from core import bridge as onitry_bridge
from core import context as context_log
from core import license as byok_license
from core import settings as app_settings
from core import status as status_file
from core.check import reset_session, run_check, session_cost
from core.interval import AdaptiveInterval

KEYCHAIN_SERVICE = "onitry"
KEYCHAIN_USER    = "anthropic_api_key"
KEYCHAIN_MANAGED_USER = "managed_token"

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
    "paused":  "#e3b341",
}

PAUSE_MINUTES = 10


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


class _BrowserBridgeController:
    """What the browser extension can see and do (see core/bridge.py).

    Called from the bridge's HTTP thread, so it never touches tkinter directly:
    reads plain attributes, and hands commands to the GUI thread via the queue.
    """

    def __init__(self, app: "OnitryApp"):
        self.app = app

    def status(self) -> dict:
        app = self.app
        data = {}
        try:
            with open(config.STATUS_FILE) as f:
                data = json.load(f)
        except (OSError, ValueError):
            pass
        timeline = list(app._timeline)
        now = time.time()
        running = app._running
        return {
            "running": running,
            "paused": app._pause_until > now,
            "pause_remaining_seconds": max(0.0, app._pause_until - now),
            "status": data.get("status", "idle") if running else "idle",
            "task": app._current_task if running else "",
            "activity": data.get("activity", "") if running else "",
            "session_seconds": (now - app._session_start_time) if running and app._session_start_time else 0.0,
            "on_task_seconds": sum(d for d, s in timeline if s == "on_task"),
            "off_task_seconds": sum(d for d, s in timeline if s == "off_task"),
            "interrupts": app._interrupt_count,
            "last_error": app._bridge_last_error,
            "edition": config.EDITION,
        }

    def start_task(self, task: str, details: str = "") -> dict:
        self.app._log_queue.put(("bridge_start", task, details))
        return {"accepted": True}

    def stop(self) -> dict:
        self.app._log_queue.put(("bridge_stop",))
        return {"accepted": True}

    def pause(self, minutes: float) -> dict:
        self.app._log_queue.put(("bridge_pause", minutes))
        return {"accepted": True}

    def resume(self) -> dict:
        self.app._log_queue.put(("bridge_resume",))
        return {"accepted": True}

    def review(self, stats: dict) -> dict:
        # Runs on the bridge's own request thread; a single API call, no tkinter.
        try:
            return review_ai.weekly_review(stats)
        except review_ai.ReviewUnavailable as exc:
            return {"error": str(exc)}


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
        self._grace_until = 0.0        # time.time() before which checks are skipped (post-popup)
        self._pause_until = 0.0        # time.time() before which checks are skipped (manual break)
        self._pause_tick_id = None

        # Session tracking (reset at the start of each monitoring run)
        self._timeline = []            # list of (seconds, "on_task" | "off_task")
        self._interrupt_count = 0
        self._session_start_time = None
        self._last_off_task_activity = None

        # Browser-extension bridge state
        self._current_task = ""
        self._task_details = ""          # extra context from the browser planner (due dates etc.)
        self._bridge_last_error = ""
        self._bridge = None
        self.bridge_code = ""

        self._settings = app_settings.load(config.SETTINGS_FILE)
        self.jpeg_quality = self._settings.get("jpeg_quality", 75)
        self.grace_period = self._settings.get("grace_period_seconds", 60)

        model_label = self._settings.get("model_label", list(MODELS.keys())[0])
        self.model_var = tk.StringVar(value=model_label if model_label in MODELS else list(MODELS.keys())[0])

        res_label = self._settings.get("resolution_label", list(RESOLUTIONS.keys())[0])
        self.res_var = tk.StringVar(value=res_label if res_label in RESOLUTIONS else list(RESOLUTIONS.keys())[0])

        self.task_history = self._settings.get("task_history", [])

        _apply_ttk_style()
        self._load_credentials()
        self._build_ui()
        self._start_bridge()
        self._poll_queue()

    # ── Browser bridge ────────────────────────────────────────────────────────

    def _start_bridge(self):
        try:
            self.bridge_code = onitry_bridge.load_or_create_token(config.BRIDGE_TOKEN_FILE)
            self._bridge = onitry_bridge.BridgeServer(
                _BrowserBridgeController(self), self.bridge_code, port=config.BRIDGE_PORT
            )
            self._bridge.start()
        except OSError as exc:
            self._bridge = None
            self._enqueue_log(f"Browser bridge unavailable ({exc}) — is another Onitry window open?")

    def _bridge_start(self, task: str, details: str):
        """GUI thread: the browser planner asked us to monitor a task."""
        if self._running and self._current_task == task:
            return
        if self._running:
            self._stop(show_summary=False)
        self.task_var.set(task)
        self._task_details = details
        self._bridge_last_error = ""
        self._enqueue_log(f"Browser planner started a focus block: {task}")
        self._start()

    def _build_ui(self):
        outer = tk.Frame(self.root, bg=BG, padx=18, pady=14)
        outer.pack(fill="both", expand=True)

        self._lbl_opts = dict(bg=BG, fg=FG, anchor="w", width=8)
        r = 0

        # ── Task ──
        tk.Label(outer, text="Task:", **self._lbl_opts).grid(row=r, column=0, sticky="w", pady=5)
        task_row = tk.Frame(outer, bg=BG)
        task_row.grid(row=r, column=1, sticky="ew", pady=5)
        task_row.columnconfigure(0, weight=1)

        self.task_var = tk.StringVar()
        self.task_entry = tk.Entry(
            task_row, textvariable=self.task_var,
            relief="flat",
            bg=BG2, fg=FG, insertbackground=FG,
            highlightthickness=1, highlightbackground=BG3, highlightcolor=BLUE,
        )
        self.task_entry.grid(row=0, column=0, sticky="ew", ipady=4)
        self.task_entry.focus()

        self._history_btn = _Btn(
            task_row, text="recents", command=self._show_task_history_menu,
            bg=BG2, fg=FG2, hover=BG3, font=("Helvetica", 11), padx=8, pady=4,
        )
        self._history_btn.grid(row=0, column=1, padx=(6, 0))
        r += 1

        # ── Credentials — differ by edition ──
        if config.EDITION in ("dev", "byok"):
            r = self._build_api_key_row(outer, r)
        if config.EDITION == "byok":
            r = self._build_license_row(outer, r)
        if config.EDITION == "managed":
            r = self._build_google_row(outer, r)

        # ── Settings ──
        tk.Label(outer, text="Settings:", **self._lbl_opts).grid(row=r, column=0, sticky="w", pady=5)
        _Btn(outer, text="⚙ Configure", command=self._open_settings_dialog,
             bg=BG, fg=BLUE, hover=BG2, font=("Helvetica", 11), padx=6, pady=2,
             ).grid(row=r, column=1, sticky="w", pady=5)
        r += 1

        # ── Divider ──
        tk.Frame(outer, bg=BG3, height=1).grid(row=r, column=0, columnspan=2, sticky="ew", pady=(8, 4))
        r += 1

        # ── Start/Stop + Pause ──
        control_row = tk.Frame(outer, bg=BG)
        control_row.grid(row=r, column=0, columnspan=2, pady=(6, 4))
        r += 1

        self.btn = _Btn(control_row, text="Start Monitoring", command=self._toggle,
                        bg=GREEN, hover=GREEN_HV)
        self.btn.pack(side="left")

        self.pause_btn = _Btn(control_row, text=f"Pause {PAUSE_MINUTES}m", command=self._toggle_pause,
                              bg=BG3, fg=FG, hover="#444", padx=14, pady=8)
        self.pause_btn.pack(side="left", padx=(8, 0))

        # ── Status ──
        self.status_var = tk.StringVar(value="Idle")
        self.status_label = tk.Label(
            outer, textvariable=self.status_var,
            bg=BG, fg=STATUS_COLORS["idle"],
            font=("Helvetica", 15, "bold"),
        )
        self.status_label.grid(row=r, column=0, columnspan=2, pady=(2, 2))
        r += 1

        # ── Session cost/usage + flag ──
        cost_row = tk.Frame(outer, bg=BG)
        cost_row.grid(row=r, column=0, columnspan=2, sticky="ew", pady=(0, 8))
        r += 1

        self.cost_var = tk.StringVar(value="")
        tk.Label(cost_row, textvariable=self.cost_var, bg=BG, fg=FG2,
                 font=("Helvetica", 11)).pack(side="left")

        _Btn(cost_row, text="🚩 Flag last as wrong", command=self._open_flag_dialog,
             bg=BG, fg=FG2, hover=BG2, font=("Helvetica", 10), padx=4, pady=2,
             ).pack(side="right")

        # ── Log (Text + dark scrollbar) ──
        log_frame = tk.Frame(outer, bg=BG2, highlightthickness=1, highlightbackground=BG3)
        log_frame.grid(row=r, column=0, columnspan=2, sticky="nsew", pady=(0, 4))

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

    def _build_api_key_row(self, outer, r):
        self._key_status_var = tk.StringVar()
        self._refresh_key_status_label()
        tk.Label(outer, text="API Key:", **self._lbl_opts).grid(row=r, column=0, sticky="w", pady=5)
        key_row = tk.Frame(outer, bg=BG)
        key_row.grid(row=r, column=1, sticky="ew", pady=5)
        tk.Label(key_row, textvariable=self._key_status_var, bg=BG, fg=FG2, anchor="w").pack(side="left")
        _Btn(key_row, text="Set Key", command=self._open_key_dialog,
             bg=BG, fg=BLUE, hover=BG2, font=("Helvetica", 11), padx=6, pady=2,
             ).pack(side="left", padx=(6, 0))
        return r + 1

    def _build_license_row(self, outer, r):
        self._license_status_var = tk.StringVar()
        self._refresh_license_status_label()
        tk.Label(outer, text="License:", **self._lbl_opts).grid(row=r, column=0, sticky="w", pady=5)
        license_row = tk.Frame(outer, bg=BG)
        license_row.grid(row=r, column=1, sticky="ew", pady=5)
        tk.Label(license_row, textvariable=self._license_status_var, bg=BG, fg=FG2, anchor="w").pack(side="left")
        _Btn(license_row, text="Enter Key", command=self._open_license_dialog,
             bg=BG, fg=BLUE, hover=BG2, font=("Helvetica", 11), padx=6, pady=2,
             ).pack(side="left", padx=(6, 0))
        return r + 1

    def _build_google_row(self, outer, r):
        self._google_status_var = tk.StringVar()
        self._refresh_google_status_label()
        tk.Label(outer, text="Account:", **self._lbl_opts).grid(row=r, column=0, sticky="w", pady=5)
        google_row = tk.Frame(outer, bg=BG)
        google_row.grid(row=r, column=1, sticky="ew", pady=5)
        tk.Label(google_row, textvariable=self._google_status_var, bg=BG, fg=FG2, anchor="w").pack(side="left")
        self._google_btn = _Btn(google_row, text="Sign in with Google", command=self._start_google_signin,
             bg=BG, fg=BLUE, hover=BG2, font=("Helvetica", 11), padx=6, pady=2)
        self._google_btn.pack(side="left", padx=(6, 0))
        return r + 1

    # ── Credentials (Keychain + server) ──────────────────────────────────────

    def _load_credentials(self):
        stored = keyring.get_password(KEYCHAIN_SERVICE, KEYCHAIN_USER)
        if stored:
            config.ANTHROPIC_API_KEY = stored

        if config.EDITION == "dev":
            config.MANAGED_MODE = self._settings.get("managed_mode", False)
            managed_token = keyring.get_password(KEYCHAIN_SERVICE, KEYCHAIN_MANAGED_USER)
            if managed_token:
                config.MANAGED_TOKEN = managed_token

        if config.EDITION == "byok":
            license_token = keyring.get_password(KEYCHAIN_SERVICE, "byok_license")
            if license_token:
                config.BYOK_LICENSE_TOKEN = license_token
                config.BYOK_LICENSE_VERIFIED = self._settings.get("byok_license_verified", False)

        if config.EDITION == "managed":
            config.MANAGED_MODE = True
            managed_token = keyring.get_password(KEYCHAIN_SERVICE, KEYCHAIN_MANAGED_USER)
            if managed_token:
                config.MANAGED_TOKEN = managed_token
                self._refresh_managed_account()

    def _refresh_managed_account(self) -> bool:
        """Synchronous whoami call — cheap, used at startup and after sign-in.
        Returns True if the stored token is still valid."""
        try:
            resp = httpx.get(
                f"{config.MANAGED_API_URL}/v1/whoami",
                params={"token": config.MANAGED_TOKEN}, timeout=10.0,
            )
            if resp.status_code != 200:
                return False
            body = resp.json()
            config.MANAGED_PLAN = body["plan"]
            config.MANAGED_EMAIL = body["email"] or ""
            config.MANAGED_DAILY_CAP_SECONDS = body["daily_cap_seconds"]
            config.MANAGED_DAILY_REMAINING_SECONDS = body["daily_remaining_seconds"]
            return True
        except httpx.HTTPError:
            return False

    def _refresh_key_status_label(self):
        stored = keyring.get_password(KEYCHAIN_SERVICE, KEYCHAIN_USER)
        env = os.environ.get("ANTHROPIC_API_KEY", "")
        if stored:
            self._key_status_var.set("Saved in Keychain ✓")
        elif env:
            self._key_status_var.set("From environment variable")
        else:
            self._key_status_var.set("Not set")

    def _refresh_license_status_label(self):
        if config.BYOK_LICENSE_TOKEN and config.BYOK_LICENSE_VERIFIED:
            self._license_status_var.set("Verified ✓")
        elif config.BYOK_LICENSE_TOKEN:
            self._license_status_var.set("Saved, not verified")
        else:
            self._license_status_var.set("Not set")

    def _refresh_google_status_label(self):
        if config.MANAGED_TOKEN and config.MANAGED_EMAIL:
            plan_label = "Pro" if config.MANAGED_PLAN == "managed_paid" else "Free"
            self._google_status_var.set(f"{config.MANAGED_EMAIL} ({plan_label})")
            self._google_btn.relabel("Switch Account")
        elif config.MANAGED_TOKEN:
            self._google_status_var.set("Signed in — reconnecting…")
        else:
            self._google_status_var.set("Not signed in")

    # ── BYOK license ──────────────────────────────────────────────────────────

    def _open_license_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Enter License Key")
        dialog.resizable(False, False)
        dialog.configure(bg=BG)
        dialog.minsize(420, 160)

        frame = tk.Frame(dialog, bg=BG, padx=18, pady=14)
        frame.pack(fill="both", expand=True)

        tk.Label(frame, text="License Key (from your $30 purchase):", bg=BG, fg=FG, anchor="w",
                 ).pack(fill="x", pady=(0, 6))
        entry = tk.Entry(
            frame, width=50, relief="flat",
            bg=BG2, fg=FG, insertbackground=FG,
            highlightthickness=1, highlightbackground=BG3, highlightcolor=BLUE,
        )
        entry.pack(fill="x", ipady=4, pady=(0, 4))
        if config.BYOK_LICENSE_TOKEN:
            entry.insert(0, config.BYOK_LICENSE_TOKEN)

        status_lbl = tk.Label(frame, text="", bg=BG, fg=FG2, anchor="w")
        status_lbl.pack(fill="x")

        btn_frame = tk.Frame(frame, bg=BG)
        btn_frame.pack(pady=(10, 0))

        def verify():
            key = entry.get().strip()
            if not key:
                status_lbl.config(text="Key cannot be empty.", fg="#f85149")
                return
            status_lbl.config(text="Verifying…", fg=FG2)
            result_queue: queue.Queue = queue.Queue()
            threading.Thread(target=self._verify_license_bg, args=(key, result_queue), daemon=True).start()
            self._poll_license_result(dialog, status_lbl, result_queue)

        _Btn(btn_frame, text="Verify & Save", command=verify,
             bg=GREEN, hover=GREEN_HV, padx=12, pady=5).pack(side="left", padx=(0, 8))
        _Btn(btn_frame, text="Cancel", command=dialog.destroy,
             bg=BG3, fg=FG, hover="#444", padx=12, pady=5).pack(side="left")

        entry.bind("<Return>", lambda _: verify())
        dialog.grab_set()
        entry.focus_force()

    def _verify_license_bg(self, key: str, result_queue: queue.Queue):
        try:
            valid = byok_license.verify(config.MANAGED_API_URL, key)
            result_queue.put(("done", valid, key))
        except byok_license.LicenseCheckFailed as exc:
            result_queue.put(("error", str(exc), key))

    def _poll_license_result(self, dialog, status_lbl, result_queue: queue.Queue):
        if not dialog.winfo_exists():
            return
        try:
            _kind, *rest = result_queue.get_nowait()
        except queue.Empty:
            dialog.after(150, lambda: self._poll_license_result(dialog, status_lbl, result_queue))
            return

        if _kind == "error":
            status_lbl.config(text=f"Couldn't reach server: {rest[0]}", fg="#f85149")
            return

        valid, key = rest
        if valid:
            config.BYOK_LICENSE_TOKEN = key
            config.BYOK_LICENSE_VERIFIED = True
            keyring.set_password(KEYCHAIN_SERVICE, "byok_license", key)
            app_settings.save(config.SETTINGS_FILE, {"byok_license_verified": True})
            self._refresh_license_status_label()
            status_lbl.config(text="Verified ✓", fg="#3fb950")
            dialog.after(800, dialog.destroy)
        else:
            config.BYOK_LICENSE_VERIFIED = False
            status_lbl.config(text="Invalid license key.", fg="#f85149")

    # ── Google sign-in (managed edition) ─────────────────────────────────────

    def _start_google_signin(self):
        self._google_status_var.set("Opening browser…")
        self._google_btn.relabel("Signing in…")
        result_queue: queue.Queue = queue.Queue()
        threading.Thread(target=self._google_signin_bg, args=(result_queue,), daemon=True).start()
        self._poll_google_signin(result_queue)

    def _google_signin_bg(self, result_queue: queue.Queue):
        try:
            id_token = google_auth.login_with_google(config.GOOGLE_CLIENT_ID, config.GOOGLE_CLIENT_SECRET)
            resp = httpx.post(
                f"{config.MANAGED_API_URL}/v1/auth/google", json={"id_token": id_token}, timeout=15.0
            )
            resp.raise_for_status()
            result_queue.put(("done", resp.json()))
        except (google_auth.GoogleLoginError, httpx.HTTPError) as exc:
            result_queue.put(("error", str(exc)))

    def _poll_google_signin(self, result_queue: queue.Queue):
        try:
            kind, payload = result_queue.get_nowait()
        except queue.Empty:
            self.root.after(200, lambda: self._poll_google_signin(result_queue))
            return

        if kind == "error":
            self._google_status_var.set("Sign-in failed")
            self._google_btn.relabel("Sign in with Google")
            self._enqueue_log(f"Google sign-in failed: {payload}")
            return

        config.MANAGED_TOKEN = payload["token"]
        config.MANAGED_PLAN = payload["plan"]
        config.MANAGED_EMAIL = payload["email"] or ""
        config.MANAGED_DAILY_CAP_SECONDS = payload["daily_cap_seconds"]
        keyring.set_password(KEYCHAIN_SERVICE, KEYCHAIN_MANAGED_USER, config.MANAGED_TOKEN)
        self._refresh_google_status_label()
        self._enqueue_log(f"Signed in as {config.MANAGED_EMAIL} ({config.MANAGED_PLAN})")

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

    # ── Settings ─────────────────────────────────────────────────────────────

    def _open_settings_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Settings")
        dialog.resizable(False, False)
        dialog.configure(bg=BG)
        dialog.minsize(380, 460)

        frame = tk.Frame(dialog, bg=BG, padx=18, pady=14)
        frame.pack(fill="both", expand=True)

        # Local copies so Cancel discards changes — committed to self.* only on Save.
        model_var = tk.StringVar(value=self.model_var.get())
        if config.EDITION == "dev":
            tk.Label(frame, text="Model:", bg=BG, fg=FG, anchor="w").pack(fill="x", pady=(0, 4))
            ttk.Combobox(
                frame, textvariable=model_var, values=list(MODELS.keys()), state="readonly",
            ).pack(fill="x", pady=(0, 12), ipady=3)

        res_var = tk.StringVar(value=self.res_var.get())
        if config.EDITION in ("dev", "byok"):
            tk.Label(frame, text="Resolution:", bg=BG, fg=FG, anchor="w").pack(fill="x", pady=(0, 4))
            ttk.Combobox(
                frame, textvariable=res_var, values=list(RESOLUTIONS.keys()), state="readonly",
            ).pack(fill="x", pady=(0, 12), ipady=3)
        elif config.EDITION == "managed" and config.MANAGED_PLAN == "managed_paid":
            tk.Label(frame, text="Detail level:", bg=BG, fg=FG, anchor="w").pack(fill="x", pady=(0, 4))
            paid_choices = ["800px  — medium", "1280px — high detail"]
            if res_var.get() not in paid_choices:
                res_var.set(paid_choices[0])
            ttk.Combobox(
                frame, textvariable=res_var, values=paid_choices, state="readonly",
            ).pack(fill="x", pady=(0, 12), ipady=3)
        elif config.EDITION == "managed":
            tk.Label(frame, text="Detail level:", bg=BG, fg=FG, anchor="w").pack(fill="x", pady=(0, 4))
            tk.Label(frame, text="Medium (free plan — upgrade below for High)",
                     bg=BG, fg=FG2, anchor="w").pack(fill="x", pady=(0, 12))

        if config.EDITION in ("dev", "byok"):
            tk.Frame(frame, bg=BG3, height=1).pack(fill="x", pady=(0, 14))

            tk.Label(frame, text="Screenshot quality (JPEG):", bg=BG, fg=FG, anchor="w",
                     ).pack(fill="x", pady=(0, 4))

            quality_var = tk.IntVar(value=self.jpeg_quality)
            quality_lbl = tk.Label(frame, text=str(self.jpeg_quality), bg=BG, fg=FG2, anchor="w")
            quality_lbl.pack(fill="x")

            def on_slide(val):
                quality_lbl.config(text=str(int(float(val))))

            tk.Scale(
                frame, from_=20, to=100, orient="horizontal",
                variable=quality_var, command=on_slide, showvalue=False,
                bg=BG, fg=FG, troughcolor=BG2, activebackground=GREEN,
                highlightthickness=0, sliderrelief="flat",
            ).pack(fill="x", pady=(0, 4))

            tk.Label(
                frame,
                text="Lower = cheaper API calls, less detail. Higher = sharper text, more tokens.",
                bg=BG, fg=FG2, font=("Helvetica", 10), wraplength=340, justify="left",
            ).pack(fill="x", pady=(0, 14))
        else:
            quality_var = tk.IntVar(value=self.jpeg_quality)  # unused by UI, kept for save() below

        tk.Frame(frame, bg=BG3, height=1).pack(fill="x", pady=(0, 14))

        tk.Label(frame, text="Grace period after dismissing a popup:", bg=BG, fg=FG, anchor="w",
                 ).pack(fill="x", pady=(0, 4))

        grace_var = tk.IntVar(value=self.grace_period)
        grace_lbl = tk.Label(frame, text=f"{self.grace_period}s", bg=BG, fg=FG2, anchor="w")
        grace_lbl.pack(fill="x")

        def on_grace_slide(val):
            grace_lbl.config(text=f"{int(float(val))}s")

        tk.Scale(
            frame, from_=0, to=300, resolution=10, orient="horizontal",
            variable=grace_var, command=on_grace_slide, showvalue=False,
            bg=BG, fg=FG, troughcolor=BG2, activebackground=GREEN,
            highlightthickness=0, sliderrelief="flat",
        ).pack(fill="x", pady=(0, 4))

        tk.Label(
            frame,
            text="No new checks run for this long after you dismiss an off-task popup — gives you time to actually switch tasks. 0 disables it.",
            bg=BG, fg=FG2, font=("Helvetica", 10), wraplength=340, justify="left",
        ).pack(fill="x", pady=(0, 14))

        tk.Frame(frame, bg=BG3, height=1).pack(fill="x", pady=(0, 14))

        # Dev-only: a way to test the managed proxy path without a real Google account.
        managed_var = tk.BooleanVar(value=config.MANAGED_MODE)
        managed_token_var = tk.StringVar(value=config.MANAGED_TOKEN)
        if config.EDITION == "dev":
            tk.Label(frame, text="Managed proxy (dev testing):", bg=BG, fg=FG, anchor="w",
                     ).pack(fill="x", pady=(0, 4))
            tk.Checkbutton(
                frame, text="Route analyze() through server/ instead of my own API key",
                variable=managed_var, bg=BG, fg=FG, selectcolor=BG2,
                activebackground=BG, activeforeground=FG,
                highlightthickness=0, anchor="w",
            ).pack(fill="x", pady=(0, 6))
            tk.Entry(
                frame, textvariable=managed_token_var, show="•",
                relief="flat", bg=BG2, fg=FG, insertbackground=FG,
                highlightthickness=1, highlightbackground=BG3, highlightcolor=BLUE,
            ).pack(fill="x", ipady=4, pady=(0, 14))

        elif config.EDITION == "managed" and config.MANAGED_PLAN == "managed_free":
            tk.Label(frame, text="Onitry Pro — $19/mo:", bg=BG, fg=FG, anchor="w",
                     ).pack(fill="x", pady=(0, 4))
            tk.Label(
                frame, text="10 hours/day instead of 1, and High detail mode.",
                bg=BG, fg=FG2, font=("Helvetica", 10), wraplength=340, justify="left",
            ).pack(fill="x", pady=(0, 6))
            _Btn(frame, text="Upgrade", command=self._open_upgrade_checkout,
                 bg=GREEN, hover=GREEN_HV, font=("Helvetica", 11), padx=10, pady=4,
                 ).pack(anchor="w", pady=(0, 14))

        tk.Frame(frame, bg=BG3, height=1).pack(fill="x", pady=(0, 14))

        if config.EDITION == "managed":
            remaining_min = int(config.MANAGED_DAILY_REMAINING_SECONDS // 60)
            cap_min = int(config.MANAGED_DAILY_CAP_SECONDS // 60)
            tk.Label(frame, text=f"Today's remaining time: {remaining_min}m / {cap_min}m",
                     bg=BG, fg=FG2, anchor="w").pack(fill="x", pady=(0, 14))
        else:
            tk.Label(frame, text=f"Session cost so far: ${session_cost():.3f}",
                     bg=BG, fg=FG2, anchor="w").pack(fill="x", pady=(0, 14))

        # ── Browser extension pairing ──
        tk.Label(frame, text="Browser planner pairing code:", bg=BG, fg=FG, anchor="w").pack(fill="x", pady=(0, 4))
        code_row = tk.Frame(frame, bg=BG)
        code_row.pack(fill="x", pady=(0, 4))
        code_text = self.bridge_code if self._bridge else "unavailable"
        tk.Label(code_row, text=code_text, bg=BG2, fg=FG, font=("Menlo", 14, "bold"), padx=10, pady=4).pack(side="left")

        def copy_code():
            self.root.clipboard_clear()
            self.root.clipboard_append(self.bridge_code)

        if self._bridge:
            _Btn(code_row, text="Copy", command=copy_code, bg=BG3, fg=FG, hover="#444",
                 font=("Helvetica", 11), padx=10, pady=4).pack(side="left", padx=(8, 0))
        tk.Label(
            frame,
            text=f"Paste this into the browser extension (Today → Settings → Onitry) so starting a focus block there "
                 f"starts monitoring here. Listening on 127.0.0.1:{config.BRIDGE_PORT} only.",
            bg=BG, fg=FG2, font=("Helvetica", 10), wraplength=340, justify="left",
        ).pack(fill="x", pady=(0, 14))

        btn_frame = tk.Frame(frame, bg=BG)
        btn_frame.pack(anchor="w")

        def save():
            if config.EDITION == "dev":
                self.model_var.set(model_var.get())
            self.res_var.set(res_var.get())
            self.jpeg_quality = quality_var.get()
            self.grace_period = grace_var.get()

            settings_to_save = {
                "jpeg_quality": self.jpeg_quality,
                "resolution_label": res_var.get(),
                "grace_period_seconds": self.grace_period,
            }
            if config.EDITION == "dev":
                settings_to_save["model_label"] = model_var.get()
                config.MANAGED_MODE = managed_var.get()
                token = managed_token_var.get().strip()
                if token:
                    config.MANAGED_TOKEN = token
                    keyring.set_password(KEYCHAIN_SERVICE, KEYCHAIN_MANAGED_USER, token)
                settings_to_save["managed_mode"] = config.MANAGED_MODE

            app_settings.save(config.SETTINGS_FILE, settings_to_save)
            dialog.destroy()

        _Btn(btn_frame, text="Save", command=save,
             bg=GREEN, hover=GREEN_HV, padx=12, pady=5).pack(side="left", padx=(0, 8))
        _Btn(btn_frame, text="Cancel", command=dialog.destroy,
             bg=BG3, fg=FG, hover="#444", padx=12, pady=5).pack(side="left")

        dialog.grab_set()

    def _open_upgrade_checkout(self):
        try:
            resp = httpx.post(
                f"{config.MANAGED_API_URL}/v1/checkout/upgrade",
                json={
                    "success_url": "https://onitry.app/upgrade-success",
                    "cancel_url": "https://onitry.app/upgrade-cancelled",
                    "subscriber_token": config.MANAGED_TOKEN,
                },
                timeout=15.0,
            )
            resp.raise_for_status()
            webbrowser.open(resp.json()["url"])
        except httpx.HTTPError as exc:
            self._enqueue_log(f"Couldn't start checkout: {exc}")

    # ── Task history ─────────────────────────────────────────────────────────

    def _remember_task(self, task: str):
        history = [t for t in self.task_history if t != task]
        history.insert(0, task)
        self.task_history = history[:8]
        app_settings.save(config.SETTINGS_FILE, {"task_history": self.task_history})

    def _show_task_history_menu(self):
        menu = tk.Menu(
            self.root, tearoff=0,
            bg=BG2, fg=FG, activebackground=BG3, activeforeground=FG,
            relief="flat", bd=0,
        )
        if not self.task_history:
            menu.add_command(label="No recent tasks", state="disabled")
        else:
            for t in self.task_history:
                label = t if len(t) <= 50 else t[:47] + "..."
                menu.add_command(label=label, command=lambda t=t: self.task_var.set(t))

        x = self._history_btn.winfo_rootx()
        y = self._history_btn.winfo_rooty() + self._history_btn.winfo_height()
        try:
            menu.tk_popup(x, y)
        finally:
            menu.grab_release()

    # ── Toggle ────────────────────────────────────────────────────────────────

    def _toggle(self):
        if self._running:
            self._stop()
        else:
            self._start()

    def _resolve_start_settings(self) -> int | None:
        """Applies per-edition gating + forces model/resolution. Returns max_width, or
        None (having already logged why) if a credential check failed."""
        if config.EDITION == "dev":
            using_managed = config.MANAGED_MODE and config.MANAGED_TOKEN
            if not using_managed and not config.ANTHROPIC_API_KEY:
                self._enqueue_log(
                    "ERROR: No API key set — click 'Set Key', or enable a managed subscription in Settings."
                )
                return None
            config.MODEL = MODELS[self.model_var.get()]
            return RESOLUTIONS[self.res_var.get()]

        if config.EDITION == "byok":
            if not config.ANTHROPIC_API_KEY:
                self._enqueue_log("ERROR: No API key set — click 'Set Key'.")
                return None
            if not config.BYOK_LICENSE_VERIFIED:
                self._enqueue_log("ERROR: License not verified — click 'Enter Key' under License.")
                return None
            config.MANAGED_MODE = False
            config.MODEL = config.HAIKU_MODEL
            return RESOLUTIONS[self.res_var.get()]

        # managed
        if not config.MANAGED_TOKEN:
            self._enqueue_log("ERROR: Sign in with Google first.")
            return None
        if not self._refresh_managed_account():
            self._enqueue_log("ERROR: Couldn't verify your account — check your connection and try again.")
            return None
        self._refresh_google_status_label()
        config.MANAGED_MODE = True
        config.MODEL = config.HAIKU_MODEL
        if config.MANAGED_PLAN == "managed_paid":
            return RESOLUTIONS.get(self.res_var.get(), 800)
        return 800  # free plan — always medium, never the picker's current value

    def _start(self):
        task = self.task_var.get().strip()
        details, self._task_details = self._task_details, ""
        if not task:
            self.task_entry.config(highlightbackground="#f85149")
            return
        self.task_entry.config(highlightbackground=BG3)

        max_width = self._resolve_start_settings()
        if max_width is None:
            return  # a gating check already logged why

        reset_session()
        self._timeline = []
        self._interrupt_count = 0
        self._session_start_time = time.time()
        self._grace_until = 0.0
        self._last_off_task_activity = None
        if config.EDITION == "managed":
            remaining_min = int(config.MANAGED_DAILY_REMAINING_SECONDS // 60)
            self.cost_var.set(f"Time remaining today: {remaining_min}m")
        else:
            self.cost_var.set("Session cost: $0.000")

        self._remember_task(task)
        self._current_task = task
        # The AI sees the planner's context too (e.g. what's due), not just the title.
        ai_task = f"{task} (context from the user's planner: {details})" if details else task

        self._stop_event.clear()
        self._running = True
        self.btn.relabel("Stop Monitoring")
        self.btn.recolor(RED, hover=RED_HV)
        self.task_entry.config(state="disabled")
        self._resume_from_pause()  # clear any leftover pause state from a prior session

        thread = threading.Thread(
            target=self._monitor_loop, args=(ai_task, max_width, self.jpeg_quality), daemon=True
        )
        thread.start()

        self._enqueue_log(f"Started — {task}")
        self._enqueue_log(f"Model: {config.MODEL}  |  Resolution: {max_width}px  |  Max interval: {MAX_INTERVAL}s")

    def _stop(self, show_summary: bool = True):
        self._stop_event.set()
        self._paused.clear()
        self._running = False
        self._cancel_pause_tick()
        self._pause_until = 0.0
        self.btn.relabel("Start Monitoring")
        self.btn.recolor(GREEN, hover=GREEN_HV)
        self.task_entry.config(state="normal")
        self._enqueue_status("Stopped", STATUS_COLORS["stopped"])
        self._enqueue_log("Monitoring stopped.")
        status_file.write(config.STATUS_FILE, "idle")

        if self._timeline and show_summary:
            self._show_session_summary()

    # ── Pause (short break) ──────────────────────────────────────────────────

    def _toggle_pause(self):
        if self._pause_until > time.time():
            self._resume_from_pause()
        elif self._running:
            self._start_pause()

    def _start_pause(self, minutes: float = PAUSE_MINUTES):
        self._cancel_pause_tick()
        self._pause_until = time.time() + minutes * 60
        self._enqueue_status("Paused", STATUS_COLORS["paused"])
        self._enqueue_log(f"Paused — taking a break, resuming automatically in {round(minutes)}m")
        status_file.write(config.STATUS_FILE, "paused", self.task_var.get(), "", session_cost())
        self._tick_pause_label()

    def _tick_pause_label(self):
        remaining = self._pause_until - time.time()
        if remaining <= 0:
            self._resume_from_pause()
            return
        self.pause_btn.relabel(f"Resume ({int(remaining // 60) + 1}m left)")
        self._pause_tick_id = self.root.after(1000, self._tick_pause_label)

    def _resume_from_pause(self):
        was_paused = self._pause_until > time.time()
        self._pause_until = 0.0
        self._cancel_pause_tick()
        self.pause_btn.relabel(f"Pause {PAUSE_MINUTES}m")
        if was_paused:
            self._enqueue_log("Resumed monitoring.")
            if self._running:
                self._enqueue_status("Resuming…", STATUS_COLORS["idle"])

    def _cancel_pause_tick(self):
        if self._pause_tick_id is not None:
            self.root.after_cancel(self._pause_tick_id)
            self._pause_tick_id = None

    # ── Monitor loop (background thread) ─────────────────────────────────────

    def _monitor_loop(self, task: str, max_width: int = 1280, quality: int = 75):
        context_log.init_log(config.CONTEXT_FILE, task)

        interval = AdaptiveInterval(MIN_INTERVAL, MAX_INTERVAL, INTERVAL_STEP, JITTER_LO, JITTER_HI)

        self._stop_event.wait(timeout=5)  # brief grace period before first check
        last_report_time = time.time()  # managed edition only — for elapsed_seconds reporting

        while not self._stop_event.is_set():
            # Wait while an interrupt popup is showing
            while self._paused.is_set() and not self._stop_event.is_set():
                self._stop_event.wait(timeout=0.5)

            if self._stop_event.is_set():
                break

            # Manual pause ("taking a break") — poll every second so Resume Now lands promptly
            if self._pause_until > time.time():
                self._stop_event.wait(timeout=1.0)
                continue

            # Grace period after a popup dismissal — give the user time to actually switch tasks
            remaining = self._grace_until - time.time()
            if remaining > 0:
                self._stop_event.wait(timeout=remaining)
                continue

            t0 = time.time()
            elapsed_since_report = t0 - last_report_time
            last_report_time = t0
            try:
                context = context_log.read_tail(config.CONTEXT_FILE)
                result = run_check(task, context, max_width, quality, elapsed_since_report)
                cost = session_cost()
                self._log_queue.put(("cost", cost))
                self._bridge_last_error = ""

                on_task = result.get("onTask", True)
                activity = result.get("activity", "unknown")
                reminder = result.get("reminder", "")
                interrupt = result.get("interrupt", False)

                if on_task:
                    self._enqueue_status("ON TASK", STATUS_COLORS["on_task"])
                    context_log.append(config.CONTEXT_FILE, activity)
                    status_file.write(config.STATUS_FILE, "on_task", task, activity, cost)
                else:
                    self._enqueue_status("OFF TASK", STATUS_COLORS["off_task"])
                    context_log.append(config.CONTEXT_FILE, f"[OFF-TASK] {activity}")
                    status_file.write(config.STATUS_FILE, "off_task", task, activity, cost)
                    interval.snap_down()
                    self._last_off_task_activity = activity
                msg = reminder if reminder else ""
                if reminder:
                    self._enqueue_log(f"  → {reminder}")
                    notifier.alert_off_task(task, reminder, interrupt)
                    if interrupt:
                        self._log_queue.put(("popup", msg))
                        self._interrupt_count += 1

            except DailyLimitReached as exc:
                self._log_queue.put(("daily_limit", str(exc)))
                break

            except Exception as exc:
                self._enqueue_log(f"Error: {exc}")
                activity = "error"
                on_task = None  # don't fire alerts on API errors, don't count toward the timeline

            elapsed = time.time() - t0
            sleep_seconds, effective = interval.sample_wait(elapsed)
            if on_task is None:
                status_label = "ERROR"
            else:
                status_label = "ON TASK" if on_task else "OFF TASK"
                self._timeline.append((effective, "on_task" if on_task else "off_task"))
            self._enqueue_log(f"{status_label}: {activity}  (next in {effective:.0f}s)")
            self._stop_event.wait(timeout=sleep_seconds)

            interval.step_up()

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _enqueue_log(self, msg: str):
        # Surface real failures to the browser planner (not the per-check "ERROR: error" summary line).
        if msg.startswith("Error: ") or (msg.startswith("ERROR:") and "(next in" not in msg):
            self._bridge_last_error = msg
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
                elif item[0] == "cost":
                    if config.EDITION == "managed":
                        remaining_min = int(config.MANAGED_DAILY_REMAINING_SECONDS // 60)
                        self.cost_var.set(f"Time remaining today: {remaining_min}m")
                    else:
                        self.cost_var.set(f"Session cost: ${item[1]:.3f}")
                elif item[0] == "popup":
                    self._show_popup(item[1])
                elif item[0] == "daily_limit":
                    self._on_daily_limit_reached(item[1])
                elif item[0] == "bridge_start":
                    self._bridge_start(item[1], item[2])
                elif item[0] == "bridge_stop":
                    if self._running:
                        self._stop(show_summary=False)
                elif item[0] == "bridge_pause":
                    if self._running:
                        self._start_pause(item[1])
                elif item[0] == "bridge_resume":
                    self._resume_from_pause()
        except queue.Empty:
            pass
        self.root.after(200, self._poll_queue)

    def _on_daily_limit_reached(self, message: str):
        self._stop()
        self._enqueue_log(f"Daily limit reached: {message}")

        dialog = tk.Toplevel(self.root)
        dialog.title("Daily Limit Reached")
        dialog.resizable(False, False)
        dialog.configure(bg=BG)
        dialog.minsize(360, 160)

        frame = tk.Frame(dialog, bg=BG, padx=20, pady=16)
        frame.pack(fill="both", expand=True)

        tk.Label(frame, text="⏱  Daily limit reached", bg=BG, fg="#e3b341",
                 font=("Helvetica", 14, "bold")).pack(anchor="w", pady=(0, 10))

        if config.MANAGED_PLAN == "managed_free":
            tk.Label(
                frame, text="You've used your free hour for today. Upgrade for 10 hours/day, "
                            "or come back tomorrow.",
                bg=BG, fg=FG, wraplength=320, justify="left",
            ).pack(anchor="w", pady=(0, 14))
            _Btn(frame, text="Upgrade — $19/mo", command=lambda: (dialog.destroy(), self._open_upgrade_checkout()),
                 bg=GREEN, hover=GREEN_HV, padx=12, pady=6).pack(anchor="w")
        else:
            tk.Label(
                frame, text="You've used all 10 hours for today. Come back tomorrow.",
                bg=BG, fg=FG, wraplength=320, justify="left",
            ).pack(anchor="w", pady=(0, 14))
            _Btn(frame, text="OK", command=dialog.destroy,
                 bg=BG3, fg=FG, hover="#444", padx=12, pady=6).pack(anchor="w")

        dialog.grab_set()

    # ── False-positive flagging ──────────────────────────────────────────────

    def _open_flag_dialog(self):
        if not self._last_off_task_activity:
            self._enqueue_log("Nothing to flag — no off-task detections yet this session.")
            return

        dialog = tk.Toplevel(self.root)
        dialog.title("Flag False Positive")
        dialog.resizable(False, False)
        dialog.configure(bg=BG)
        dialog.minsize(420, 240)

        frame = tk.Frame(dialog, bg=BG, padx=18, pady=14)
        frame.pack(fill="both", expand=True)

        tk.Label(frame, text="You were flagged off task for:", bg=BG, fg=FG2, anchor="w",
                 font=("Helvetica", 10)).pack(fill="x", pady=(0, 2))
        tk.Label(frame, text=self._last_off_task_activity, bg=BG, fg=FG, anchor="w",
                 font=("Helvetica", 12, "bold"), wraplength=380, justify="left",
                 ).pack(fill="x", pady=(0, 12))

        tk.Label(frame, text="What were you actually doing?", bg=BG, fg=FG, anchor="w",
                 ).pack(fill="x", pady=(0, 4))
        text_box = tk.Text(
            frame, height=3, relief="flat",
            bg=BG2, fg=FG, insertbackground=FG,
            wrap="word", padx=6, pady=6,
            highlightthickness=1, highlightbackground=BG3, highlightcolor=BLUE,
        )
        text_box.pack(fill="x", pady=(0, 4))
        text_box.focus_force()

        status_lbl = tk.Label(frame, text="", bg=BG, fg=FG2, anchor="w")
        status_lbl.pack(fill="x", pady=(4, 0))

        btn_frame = tk.Frame(frame, bg=BG)
        btn_frame.pack(anchor="w", pady=(10, 0))

        def submit():
            explanation = text_box.get("1.0", "end").strip()
            if not explanation:
                status_lbl.config(text="Add a quick explanation first.", fg="#f85149")
                return
            context_log.append(
                config.CONTEXT_FILE,
                f'[USER CORRECTION] You flagged "{self._last_off_task_activity}" as off-task, '
                f"but the user says they were actually: {explanation}",
            )
            self._enqueue_log(f"🚩 Flagged as wrong: {explanation}")
            dialog.destroy()

        _Btn(btn_frame, text="Submit", command=submit,
             bg=GREEN, hover=GREEN_HV, padx=12, pady=5).pack(side="left", padx=(0, 8))
        _Btn(btn_frame, text="Cancel", command=dialog.destroy,
             bg=BG3, fg=FG, hover="#444", padx=12, pady=5).pack(side="left")

        dialog.grab_set()

    def _dismiss_popup(self, pop):
        self._paused.clear()
        if self.grace_period > 0:
            self._grace_until = time.time() + self.grace_period
            self._enqueue_log(f"Grace period — next check in {self.grace_period}s")
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

        def _flag_and_dismiss():
            self._dismiss_popup(pop)
            self._open_flag_dialog()

        _Btn(frame, text="Not actually off task?", command=_flag_and_dismiss,
             bg="#2a0a0a", fg="#888888", hover="#3a1010",
             font=("Helvetica", 10), padx=4, pady=4).pack(anchor="w", pady=(8, 0))

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

    # ── Session summary ──────────────────────────────────────────────────────

    def _show_session_summary(self):
        total = sum(duration for duration, _ in self._timeline)
        on_seconds = sum(duration for duration, status in self._timeline if status == "on_task")
        pct_on = (on_seconds / total * 100) if total else 0.0

        elapsed = time.time() - self._session_start_time if self._session_start_time else 0
        hours, rem = divmod(int(elapsed), 3600)
        minutes, seconds = divmod(rem, 60)
        if hours:
            duration_str = f"{hours}h {minutes}m"
        elif minutes:
            duration_str = f"{minutes}m {seconds}s"
        else:
            duration_str = f"{seconds}s"

        win = tk.Toplevel(self.root)
        win.title("Session Summary")
        win.resizable(False, False)
        win.configure(bg=BG)

        frame = tk.Frame(win, bg=BG, padx=24, pady=20)
        frame.pack(fill="both", expand=True)

        tk.Label(frame, text="Session Summary", bg=BG, fg=FG,
                 font=("Helvetica", 14, "bold")).pack(anchor="w", pady=(0, 16))

        tk.Label(frame, text=duration_str, bg=BG, fg=FG,
                 font=("Helvetica", 30, "bold")).pack(anchor="w")
        tk.Label(frame, text="monitored", bg=BG, fg=FG2,
                 font=("Helvetica", 11)).pack(anchor="w", pady=(0, 16))

        # Timeline bar — proportional on-task/off-task segments in chronological order
        bar_width = 360
        canvas = tk.Canvas(frame, width=bar_width, height=16, bg=BG2, highlightthickness=0)
        canvas.pack(fill="x")
        x = 0.0
        for duration, status in self._timeline:
            w = (duration / total * bar_width) if total else 0
            color = "#3fb950" if status == "on_task" else "#f85149"
            canvas.create_rectangle(x, 0, x + w, 16, fill=color, width=0)
            x += w

        tk.Label(frame, text=f"{pct_on:.0f}% on task", bg=BG, fg="#3fb950",
                 font=("Helvetica", 13, "bold")).pack(anchor="w", pady=(8, 16))

        stats_row = tk.Frame(frame, bg=BG)
        stats_row.pack(fill="x", pady=(0, 4))
        tk.Label(stats_row, text=f"{self._interrupt_count} interruptions", bg=BG, fg=FG2,
                 font=("Helvetica", 12)).pack(side="left")
        if config.EDITION == "managed":
            remaining_min = int(config.MANAGED_DAILY_REMAINING_SECONDS // 60)
            secondary_stat = f"{remaining_min}m left today"
        else:
            secondary_stat = f"${session_cost():.3f} spent"
        tk.Label(stats_row, text=secondary_stat, bg=BG, fg=FG2,
                 font=("Helvetica", 12)).pack(side="right")

        _Btn(frame, text="Close", command=win.destroy,
             bg=BG3, fg=FG, hover="#444", padx=16, pady=6).pack(anchor="w", pady=(20, 0))

        win.grab_set()


def main():
    import multiprocessing
    multiprocessing.set_start_method("spawn", force=True)
    root = tk.Tk()
    OnitryApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
