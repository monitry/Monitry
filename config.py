import os

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
MODEL = "claude-sonnet-4-6"

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

# Managed subscription mode — route analyze() through server/ instead of calling
# Anthropic directly, so the user doesn't need their own API key. See server/README.md.
MANAGED_MODE = False
MANAGED_TOKEN = os.environ.get("ONITRY_MANAGED_TOKEN", "")
MANAGED_API_URL = os.environ.get("ONITRY_MANAGED_API_URL", "https://api.onitry.app")

# Managed edition is always this model — never exposed as a setting, enforced server-side too.
HAIKU_MODEL = "claude-haiku-4-5-20251001"

# Which product this build is: "dev" (everything unlocked, for testing) |
# "byok" ($30 one-time, own API key, no model choice) | "managed" (Google
# sign-in, free 1hr/day or paid 10hr/day, no model or JPEG-quality choice).
EDITION = os.environ.get("ONITRY_EDITION", "dev")

# BYOK edition license — verified once against server/, then cached locally.
BYOK_LICENSE_TOKEN = os.environ.get("ONITRY_LICENSE_TOKEN", "")
BYOK_LICENSE_VERIFIED = False

# Managed edition account state, populated after Google sign-in / each /v1/analyze call.
MANAGED_PLAN = ""                     # "managed_free" | "managed_paid"
MANAGED_EMAIL = ""
MANAGED_DAILY_CAP_SECONDS = 0.0
MANAGED_DAILY_REMAINING_SECONDS = 0.0

# Google OAuth ("Sign in with Google") — desktop-app client, see server/README.md
# for how to create one. The secret isn't confidential for this client type per
# Google's own docs, but a real value is still needed to exchange the auth code.
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "")
