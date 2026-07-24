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

# Persisted app settings (e.g. JPEG quality)
SETTINGS_FILE = os.path.join(os.path.dirname(__file__), "data", "settings.json")
