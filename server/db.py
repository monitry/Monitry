"""SQLite-backed subscriber store for the managed-API proxy + BYOK licensing.

Kept deliberately simple (stdlib sqlite3, no ORM) since this is a solo-dev
MVP — swap for Postgres if usage ever outgrows a single SQLite file.

`plan` values: "managed_free" | "managed_paid" | "byok". Daily usage caps
only apply to the two "managed_*" plans — "byok" rows exist purely so the
one-time-purchase app has something to verify against once.

Daily usage resets on the UTC calendar date (see check_and_consume_daily_usage) —
not the subscriber's local timezone. Simpler to reason about server-side;
worth revisiting if that ever confuses users near midnight.
"""
import contextlib
import datetime
import os
import secrets
import sqlite3
import time

DB_PATH = os.environ.get("ONITRY_DB_PATH", "onitry_server.db")

PLAN_FREE = "managed_free"
PLAN_PAID = "managed_paid"
PLAN_BYOK = "byok"


@contextlib.contextmanager
def _connect():
    """`sqlite3.Connection` as a context manager only commits/rolls back —
    it does NOT close the connection. Wrap it so callers get both."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        with conn:
            yield conn
    finally:
        conn.close()


def init_db() -> None:
    with _connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS subscribers (
                token TEXT PRIMARY KEY,
                plan TEXT NOT NULL DEFAULT 'managed_free',
                email TEXT,
                google_sub TEXT UNIQUE,
                stripe_customer_id TEXT,
                stripe_subscription_id TEXT,
                active INTEGER NOT NULL DEFAULT 1,
                created_at REAL NOT NULL,
                daily_usage_date TEXT,
                daily_seconds_used REAL NOT NULL DEFAULT 0.0,
                total_input_tokens INTEGER NOT NULL DEFAULT 0,
                total_output_tokens INTEGER NOT NULL DEFAULT 0,
                total_cost REAL NOT NULL DEFAULT 0.0
            )
        """)


def generate_token() -> str:
    return "onitry_" + secrets.token_urlsafe(24)


def utc_today() -> str:
    return datetime.datetime.now(datetime.UTC).date().isoformat()


def remaining_daily_seconds(subscriber: dict, cap_seconds: float) -> float:
    """Read-only view of how much of today's cap is left, without consuming any of it."""
    used = subscriber["daily_seconds_used"] if subscriber["daily_usage_date"] == utc_today() else 0.0
    return max(0.0, cap_seconds - used)


def get_subscriber(token: str) -> dict | None:
    with _connect() as conn:
        row = conn.execute("SELECT * FROM subscribers WHERE token = ?", (token,)).fetchone()
    return dict(row) if row else None


def get_by_google_sub(google_sub: str) -> dict | None:
    with _connect() as conn:
        row = conn.execute("SELECT * FROM subscribers WHERE google_sub = ?", (google_sub,)).fetchone()
    return dict(row) if row else None


def get_or_create_by_google(google_sub: str, email: str | None) -> dict:
    """Log in (or silently sign up, free plan) a Google-authenticated user."""
    existing = get_by_google_sub(google_sub)
    if existing is not None:
        if email and existing["email"] != email:
            with _connect() as conn:
                conn.execute("UPDATE subscribers SET email = ? WHERE google_sub = ?", (email, google_sub))
            existing["email"] = email
        return existing

    token = generate_token()
    with _connect() as conn:
        conn.execute(
            "INSERT INTO subscribers (token, plan, email, google_sub, active, created_at) "
            "VALUES (?, ?, ?, ?, 1, ?)",
            (token, PLAN_FREE, email, google_sub, time.time()),
        )
    return get_subscriber(token)


def create_byok_license(email: str | None, stripe_customer_id: str | None) -> str:
    """One-time-purchase ($30) license — no daily cap, verified once by the app."""
    token = generate_token()
    with _connect() as conn:
        conn.execute(
            "INSERT INTO subscribers (token, plan, email, stripe_customer_id, active, created_at) "
            "VALUES (?, ?, ?, ?, 1, ?)",
            (token, PLAN_BYOK, email, stripe_customer_id, time.time()),
        )
    return token


def create_manual(email: str | None, plan: str, active: bool = True) -> str:
    """Admin-issued token with no Google/Stripe linkage — support/refund edge cases only."""
    token = generate_token()
    with _connect() as conn:
        conn.execute(
            "INSERT INTO subscribers (token, plan, email, active, created_at) VALUES (?, ?, ?, ?, ?)",
            (token, plan, email, int(active), time.time()),
        )
    return token


def verify_byok_license(token: str) -> bool:
    subscriber = get_subscriber(token)
    return bool(subscriber and subscriber["plan"] == PLAN_BYOK and subscriber["active"])


def upgrade_to_paid(token: str, stripe_customer_id: str | None, stripe_subscription_id: str | None) -> bool:
    """Returns True if a matching managed subscriber was found and upgraded."""
    with _connect() as conn:
        cur = conn.execute(
            "UPDATE subscribers SET plan = ?, active = 1, stripe_customer_id = ?, "
            "stripe_subscription_id = ? WHERE token = ?",
            (PLAN_PAID, stripe_customer_id, stripe_subscription_id, token),
        )
        return cur.rowcount > 0


def downgrade_to_free_by_subscription(stripe_subscription_id: str) -> None:
    with _connect() as conn:
        conn.execute(
            "UPDATE subscribers SET plan = ? WHERE stripe_subscription_id = ? AND plan = ?",
            (PLAN_FREE, stripe_subscription_id, PLAN_PAID),
        )


def set_active_by_token(token: str, active: bool) -> bool:
    """Returns True if a matching row was updated."""
    with _connect() as conn:
        cur = conn.execute("UPDATE subscribers SET active = ? WHERE token = ?", (int(active), token))
        return cur.rowcount > 0


def record_usage(token: str, input_tokens: int, output_tokens: int, cost: float) -> None:
    with _connect() as conn:
        conn.execute(
            "UPDATE subscribers SET "
            "total_input_tokens = total_input_tokens + ?, "
            "total_output_tokens = total_output_tokens + ?, "
            "total_cost = total_cost + ? "
            "WHERE token = ?",
            (input_tokens, output_tokens, cost, token),
        )


def check_and_consume_daily_usage(token: str, seconds: float, cap_seconds: float) -> dict:
    """Atomically check the daily cap and, if it fits, consume `seconds` against it.

    Rolls the counter over to 0 if the stored date isn't today (UTC). Always
    persists the rollover even when the request itself is rejected, so a
    long-idle-then-one-huge-request doesn't get stuck comparing against a
    stale date forever.
    """
    today = utc_today()
    with _connect() as conn:
        row = conn.execute(
            "SELECT daily_usage_date, daily_seconds_used FROM subscribers WHERE token = ?", (token,)
        ).fetchone()
        if row is None:
            return {"allowed": False, "remaining": 0.0}

        used = row["daily_seconds_used"] if row["daily_usage_date"] == today else 0.0

        if used + seconds > cap_seconds:
            conn.execute(
                "UPDATE subscribers SET daily_usage_date = ?, daily_seconds_used = ? WHERE token = ?",
                (today, used, token),
            )
            return {"allowed": False, "remaining": max(0.0, cap_seconds - used)}

        new_used = used + seconds
        conn.execute(
            "UPDATE subscribers SET daily_usage_date = ?, daily_seconds_used = ? WHERE token = ?",
            (today, new_used, token),
        )
        return {"allowed": True, "remaining": max(0.0, cap_seconds - new_used)}
