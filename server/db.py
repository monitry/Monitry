"""SQLite-backed subscriber store for the managed-API proxy.

Kept deliberately simple (stdlib sqlite3, no ORM) since this is a solo-dev
MVP — swap for Postgres if usage ever outgrows a single SQLite file.
"""
import contextlib
import os
import secrets
import sqlite3
import time

DB_PATH = os.environ.get("ONITRY_DB_PATH", "onitry_server.db")


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
                email TEXT,
                stripe_customer_id TEXT,
                stripe_subscription_id TEXT,
                active INTEGER NOT NULL DEFAULT 0,
                created_at REAL NOT NULL,
                total_input_tokens INTEGER NOT NULL DEFAULT 0,
                total_output_tokens INTEGER NOT NULL DEFAULT 0,
                total_cost REAL NOT NULL DEFAULT 0.0
            )
        """)


def generate_token() -> str:
    return "onitry_" + secrets.token_urlsafe(24)


def create_subscriber(
    email: str | None,
    stripe_customer_id: str | None,
    stripe_subscription_id: str | None,
    active: bool = True,
) -> str:
    token = generate_token()
    with _connect() as conn:
        conn.execute(
            "INSERT INTO subscribers "
            "(token, email, stripe_customer_id, stripe_subscription_id, active, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (token, email, stripe_customer_id, stripe_subscription_id, int(active), time.time()),
        )
    return token


def get_subscriber(token: str) -> dict | None:
    with _connect() as conn:
        row = conn.execute("SELECT * FROM subscribers WHERE token = ?", (token,)).fetchone()
    return dict(row) if row else None


def set_active_by_subscription(stripe_subscription_id: str, active: bool) -> None:
    with _connect() as conn:
        conn.execute(
            "UPDATE subscribers SET active = ? WHERE stripe_subscription_id = ?",
            (int(active), stripe_subscription_id),
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
