"""Which Onitry "edition" is running, and what each one requires to start.

Onitry is free: the default edition is ``free`` (the user's own Anthropic key,
Haiku, no license, no account, no Onitry server). ``dev`` is the unlocked
testing build. ``byok`` (paid one-time license) and ``managed`` (Google
sign-in + subscription) are LEGACY editions from an undeployed paid design;
they are only honored when explicitly enabled, and resolve to ``free`` otherwise.

Pure functions, no imports from config, so config.py can use them.
"""

FREE = "free"
DEV = "dev"
LEGACY_BYOK = "byok"
LEGACY_MANAGED = "managed"
LEGACY = (LEGACY_BYOK, LEGACY_MANAGED)
KNOWN = (FREE, DEV) + LEGACY


def resolve(raw: str, legacy_enabled: bool = False) -> str:
    """Map the ONITRY_EDITION env value to the edition actually used.

    Empty/unknown -> free. Legacy paid editions fall back to free unless
    ``legacy_enabled``.
    """
    value = (raw or "").strip().lower()
    if value == DEV:
        return DEV
    if value in LEGACY and legacy_enabled:
        return value
    return FREE


def uses_own_api_key(edition: str) -> bool:
    """Editions that call Anthropic directly with the user's own key."""
    return edition in (FREE, DEV, LEGACY_BYOK)


def requires_license(edition: str) -> bool:
    """Only the legacy paid BYOK edition ever needs a license (and thus a server call)."""
    return edition == LEGACY_BYOK


def start_error(edition: str, api_key: str, license_verified: bool = False) -> str | None:
    """User-facing reason monitoring can't start for free/legacy-byok, else None.

    Never touches the network — a license, if one is required, is judged from
    the previously cached verification flag only.
    """
    if not api_key:
        return "ERROR: No API key set — click 'Set Key'."
    if requires_license(edition) and not license_verified:
        return "ERROR: License not verified — click 'Enter Key' under License."
    return None
