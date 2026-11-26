import os

from core import edition as _edition  # pure helper, does not import config

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
MODEL = "claude-sonnet-4-6"

# Weekly review for the Timecheck extension (ai/review.py) — one call a week.
REVIEW_MODEL = os.environ.get("ONITRY_REVIEW_MODEL", "claude-opus-5-5")

# How often to run a monitoring check (seconds)
CHECK_INTERVAL = 10


MAX_TOKENS_PER_RESPONSE = 512

# Path to the running context log
CONTEXT_FILE = os.path.join(os.path.dirname(__file__), "data", "context.txt")

# Max chars from context log to send to Claude (keep tokens reasonable)
CONTEXT_MAX_CHARS = 2000

# Shared status file read by the menu bar app
STATUS_FILE = os.path.join(os.path.dirname(__file__), "data", "status.json")

# Browser-extension bridge (core/bridge.py): localhost port + pairing code file
BRIDGE_PORT = int(os.environ.get("ONITRY_BRIDGE_PORT", "47323"))
BRIDGE_TOKEN_FILE = os.path.join(os.path.dirname(__file__), "data", "bridge_token")

# Persisted app settings (e.g. JPEG quality)
SETTINGS_FILE = os.path.join(os.path.dirname(__file__), "data", "settings.json")

# ---------------------------------------------------------------------------
# Product model: Onitry is FREE. The user brings their own Anthropic API key
# (Keychain or ANTHROPIC_API_KEY). No license, subscription, account, sign-in
# or backend — the app never contacts any Onitry server.
#
# Everything below the "LEGACY" marker is the old paid design (one-time BYOK
# license + Google-sign-in managed subscription, backed by server/). It was
# never deployed and is NOT OFFERED. It is kept only so it can be revived or
# deleted later; it is unreachable unless ONITRY_ENABLE_LEGACY_EDITIONS=1.
# ---------------------------------------------------------------------------

# Which build this is:
#   "free"    (default) own Anthropic key, Haiku, no gates, no network besides Anthropic
#   "dev"     everything unlocked for testing (model picker, etc.)
#   "byok" / "managed"  LEGACY paid editions — only honored when the flag below is on;
#             otherwise they fall back to "free" so a stale env var can't resurrect them.
LEGACY_EDITIONS_ENABLED = os.environ.get("ONITRY_ENABLE_LEGACY_EDITIONS", "") == "1"
EDITION = _edition.resolve(os.environ.get("ONITRY_EDITION", ""), LEGACY_EDITIONS_ENABLED)

# The free edition always uses this model (same as the old byok edition did).
HAIKU_MODEL = "claude-haiku-4-5-20251001"

# ── LEGACY (not offered; see above) ─────────────────────────────────────────

# Managed subscription mode — route analyze() through server/ instead of calling
# Anthropic directly. Ignored by ai/client.py unless LEGACY_EDITIONS_ENABLED. See server/README.md.
MANAGED_MODE = False
MANAGED_TOKEN = os.environ.get("ONITRY_MANAGED_TOKEN", "")
MANAGED_API_URL = os.environ.get("ONITRY_MANAGED_API_URL", "https://api.onitry.app")

# Legacy paid-BYOK license — verified once against server/, then cached locally.
BYOK_LICENSE_TOKEN = os.environ.get("ONITRY_LICENSE_TOKEN", "")
BYOK_LICENSE_VERIFIED = False

# Legacy managed account state, populated after Google sign-in / each /v1/analyze call.
MANAGED_PLAN = ""                     # "managed_free" | "managed_paid"
MANAGED_EMAIL = ""
MANAGED_DAILY_CAP_SECONDS = 0.0
MANAGED_DAILY_REMAINING_SECONDS = 0.0

# Legacy Google OAuth ("Sign in with Google") — desktop-app client, see server/README.md.
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "")
