# core/database.py
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List

from core.config import DATABASE_PATH


def _conn() -> sqlite3.Connection:
    Path(DATABASE_PATH).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with _conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                bot_user_id INTEGER PRIMARY KEY,
                phone TEXT,
                session_file TEXT,
                account_id INTEGER,
                account_name TEXT,
                status TEXT DEFAULT 'pending',
                created_at TEXT,
                last_login TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS login_state (
                bot_user_id INTEGER PRIMARY KEY,
                step TEXT,
                phone TEXT,
                transaction_hash TEXT,
                updated_at TEXT
            )
            """
        )
        conn.commit()


def get_user(bot_user_id: int) -> Optional[Dict[str, Any]]:
    with _conn() as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE bot_user_id = ?", (bot_user_id,)
        ).fetchone()
        return dict(row) if row else None


def upsert_user(
    bot_user_id: int,
    phone: str = None,
    session_file: str = None,
    account_id: int = None,
    account_name: str = None,
    status: str = "active",
) -> None:
    now = datetime.now().isoformat()
    existing = get_user(bot_user_id)
    with _conn() as conn:
        if existing:
            conn.execute(
                """
                UPDATE users SET
                    phone = COALESCE(?, phone),
                    session_file = COALESCE(?, session_file),
                    account_id = COALESCE(?, account_id),
                    account_name = COALESCE(?, account_name),
                    status = COALESCE(?, status),
                    last_login = ?
                WHERE bot_user_id = ?
                """,
                (phone, session_file, account_id, account_name, status, now, bot_user_id),
            )
        else:
            conn.execute(
                """
                INSERT INTO users
                (bot_user_id, phone, session_file, account_id, account_name, status, created_at, last_login)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (bot_user_id, phone, session_file, account_id, account_name, status, now, now),
            )
        conn.commit()


def count_users() -> int:
    with _conn() as conn:
        row = conn.execute("SELECT COUNT(*) AS c FROM users WHERE status = 'active'").fetchone()
        return int(row["c"]) if row else 0


def list_active_sessions() -> List[Dict[str, Any]]:
    with _conn() as conn:
        rows = conn.execute(
            "SELECT * FROM users WHERE status = 'active' AND session_file IS NOT NULL"
        ).fetchall()
        return [dict(r) for r in rows]


def set_login_state(
    bot_user_id: int,
    step: str,
    phone: str = None,
    transaction_hash: str = None,
) -> None:
    now = datetime.now().isoformat()
    with _conn() as conn:
        conn.execute(
            """
            INSERT INTO login_state (bot_user_id, step, phone, transaction_hash, updated_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(bot_user_id) DO UPDATE SET
                step = excluded.step,
                phone = COALESCE(excluded.phone, login_state.phone),
                transaction_hash = COALESCE(excluded.transaction_hash, login_state.transaction_hash),
                updated_at = excluded.updated_at
            """,
            (bot_user_id, step, phone, transaction_hash, now),
        )
        conn.commit()


def get_login_state(bot_user_id: int) -> Optional[Dict[str, Any]]:
    with _conn() as conn:
        row = conn.execute(
            "SELECT * FROM login_state WHERE bot_user_id = ?", (bot_user_id,)
        ).fetchone()
        return dict(row) if row else None


def clear_login_state(bot_user_id: int) -> None:
    with _conn() as conn:
        conn.execute("DELETE FROM login_state WHERE bot_user_id = ?", (bot_user_id,))
        conn.commit()
