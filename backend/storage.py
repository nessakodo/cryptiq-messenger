"""SQLite helpers backing the Cryptiq persistence layer."""

from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional


def _resolve_db_path() -> Path:
    url = os.environ.get("DATABASE_URL")
    if url and url.startswith("sqlite:///"):
        return Path(url.replace("sqlite:///", ""))
    custom = os.environ.get("DATABASE_PATH")
    if custom:
        return Path(custom)
    return Path(__file__).resolve().parent / "instance" / "cryptiq.db"


DB_PATH = _resolve_db_path()


SCHEMA: Iterable[str] = (
    """
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        kyber_public_key TEXT NOT NULL,
        kyber_private_key_enc TEXT NOT NULL,
        dilithium_public_key TEXT NOT NULL,
        dilithium_private_key_enc TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        token TEXT UNIQUE NOT NULL,
        created_at TEXT NOT NULL,
        expires_at TEXT NOT NULL,
        FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sender_id INTEGER NOT NULL,
        signature TEXT NOT NULL,
        plaintext_digest TEXT NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY(sender_id) REFERENCES users(id) ON DELETE CASCADE
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS message_deliveries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        message_id INTEGER NOT NULL,
        recipient_id INTEGER NOT NULL,
        kem_ciphertext TEXT NOT NULL,
        nonce TEXT NOT NULL,
        tag TEXT NOT NULL,
        ciphertext TEXT NOT NULL,
        created_at TEXT NOT NULL,
        UNIQUE(message_id, recipient_id),
        FOREIGN KEY(message_id) REFERENCES messages(id) ON DELETE CASCADE,
        FOREIGN KEY(recipient_id) REFERENCES users(id) ON DELETE CASCADE
    )
    """,
)


def init_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        for statement in SCHEMA:
            conn.execute(statement)
        conn.commit()


@contextmanager
def get_connection() -> Iterable[sqlite3.Connection]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def create_user(**fields: str) -> Dict[str, object]:
    now = fields.get("created_at", datetime.utcnow().isoformat())
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO users (username, password_hash, kyber_public_key, kyber_private_key_enc,
                               dilithium_public_key, dilithium_private_key_enc, created_at)
            VALUES (:username, :password_hash, :kyber_public_key, :kyber_private_key_enc,
                    :dilithium_public_key, :dilithium_private_key_enc, :created_at)
            """,
            {**fields, "created_at": now},
        )
        conn.commit()
        user_id = cursor.lastrowid
    return get_user_by_id(user_id)


def get_user_by_username(username: str) -> Optional[Dict[str, object]]:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    return dict(row) if row else None


def get_user_by_id(user_id: int) -> Optional[Dict[str, object]]:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    return dict(row) if row else None


def list_users() -> List[Dict[str, object]]:
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM users ORDER BY id ASC").fetchall()
    return [dict(row) for row in rows]


def create_session(user_id: int, token: str, created_at: str, expires_at: str) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO sessions (user_id, token, created_at, expires_at)
            VALUES (?, ?, ?, ?)
            """,
            (user_id, token, created_at, expires_at),
        )
        conn.commit()


def delete_session(token: str) -> None:
    with get_connection() as conn:
        conn.execute("DELETE FROM sessions WHERE token = ?", (token,))
        conn.commit()


def get_session(token: str) -> Optional[Dict[str, object]]:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM sessions WHERE token = ?", (token,)).fetchone()
    return dict(row) if row else None


def create_message(sender_id: int, signature: str, plaintext_digest: str, created_at: str) -> int:
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO messages (sender_id, signature, plaintext_digest, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (sender_id, signature, plaintext_digest, created_at),
        )
        conn.commit()
        return cursor.lastrowid


def create_delivery(
    message_id: int,
    recipient_id: int,
    kem_ciphertext: str,
    nonce: str,
    tag: str,
    ciphertext: str,
    created_at: str,
) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO message_deliveries (message_id, recipient_id, kem_ciphertext, nonce, tag, ciphertext, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (message_id, recipient_id, kem_ciphertext, nonce, tag, ciphertext, created_at),
        )
        conn.commit()


def deliveries_for_user(user_id: int) -> List[Dict[str, object]]:
    query = """
        SELECT d.*, m.signature, m.plaintext_digest, m.created_at AS message_created_at,
               m.sender_id, u.username AS sender_username, u.dilithium_public_key
        FROM message_deliveries d
        JOIN messages m ON m.id = d.message_id
        JOIN users u ON u.id = m.sender_id
        WHERE d.recipient_id = ?
        ORDER BY m.created_at ASC
    """
    with get_connection() as conn:
        rows = conn.execute(query, (user_id,)).fetchall()
    return [dict(row) for row in rows]
