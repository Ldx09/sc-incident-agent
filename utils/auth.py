import sqlite3
import hashlib
import os
import re
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "incidents.db"


def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_users():
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            username    TEXT NOT NULL UNIQUE,
            email       TEXT NOT NULL UNIQUE,
            password    TEXT NOT NULL,
            created_at  TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def validate_email(email: str) -> bool:
    return bool(re.match(r"[^@]+@[^@]+\.[^@]+", email))


def validate_password(password: str) -> tuple[bool, str]:
    if len(password) < 8:
        return False, "Password must be at least 8 characters."
    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one number."
    return True, ""


def register_user(username: str, email: str, password: str) -> tuple[bool, str]:
    init_users()

    username = username.strip().lower()
    email    = email.strip().lower()

    if not username or len(username) < 3:
        return False, "Username must be at least 3 characters."
    if not validate_email(email):
        return False, "Please enter a valid email address."

    valid, msg = validate_password(password)
    if not valid:
        return False, msg

    conn = get_connection()
    try:
        conn.execute("""
            INSERT INTO users (username, email, password, created_at)
            VALUES (?, ?, ?, ?)
        """, (username, email, hash_password(password), datetime.now().isoformat()))
        conn.commit()
        return True, "Account created successfully."
    except sqlite3.IntegrityError as e:
        if "username" in str(e):
            return False, "Username already taken. Choose another."
        if "email" in str(e):
            return False, "An account with that email already exists."
        return False, "Registration failed. Try again."
    finally:
        conn.close()


def login_user(username: str, password: str) -> tuple[bool, dict | None, str]:
    init_users()

    username = username.strip().lower()
    conn     = get_connection()

    row = conn.execute(
        "SELECT * FROM users WHERE username = ?", (username,)
    ).fetchone()
    conn.close()

    if not row:
        return False, None, "Username not found."

    if row["password"] != hash_password(password):
        return False, None, "Incorrect password."

    return True, {
        "id":       row["id"],
        "username": row["username"],
        "email":    row["email"],
    }, "Login successful."


def get_user_by_id(user_id: int) -> dict | None:
    init_users()
    conn = get_connection()
    row  = conn.execute(
        "SELECT id, username, email, created_at FROM users WHERE id = ?",
        (user_id,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None