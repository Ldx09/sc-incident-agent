import sqlite3
import json
import re
from datetime import datetime
from utils.database import get_connection, init_db


def init_watchlist():
    init_db()
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS watchlist (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id        INTEGER NOT NULL DEFAULT 0,
            supplier       TEXT NOT NULL,
            added_at       TEXT NOT NULL,
            notes          TEXT DEFAULT '',
            risk_score     INTEGER DEFAULT 0,
            incident_count INTEGER DEFAULT 0,
            last_seen      TEXT,
            UNIQUE(user_id, supplier)
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS watchlist_hits (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id       INTEGER NOT NULL DEFAULT 0,
            supplier      TEXT NOT NULL,
            incident_id   TEXT NOT NULL,
            incident_type TEXT,
            severity      TEXT,
            hit_at        TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def add_supplier(supplier: str, notes: str = "", user_id: int = 0) -> bool:
    init_watchlist()
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO watchlist (user_id, supplier, added_at, notes) VALUES (?, ?, ?, ?)",
            (user_id, supplier.strip(), datetime.now().isoformat(), notes.strip())
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def remove_supplier(supplier: str, user_id: int = 0):
    init_watchlist()
    conn = get_connection()
    conn.execute(
        "DELETE FROM watchlist WHERE supplier = ? AND user_id = ?",
        (supplier, user_id)
    )
    conn.execute(
        "DELETE FROM watchlist_hits WHERE supplier = ? AND user_id = ?",
        (supplier, user_id)
    )
    conn.commit()
    conn.close()


def get_watchlist(user_id: int = 0) -> list[dict]:
    init_watchlist()
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM watchlist WHERE user_id = ? ORDER BY risk_score DESC, supplier ASC",
        (user_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_hits_for_supplier(supplier: str, user_id: int = 0) -> list[dict]:
    init_watchlist()
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM watchlist_hits WHERE supplier = ? AND user_id = ? ORDER BY hit_at DESC",
        (supplier, user_id)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def normalize(s: str) -> str:
    return re.sub(r'[\s\.\-_,]', '', s.lower())


def check_incident_against_watchlist(result, user_id: int = 0) -> list[dict]:
    init_watchlist()
    watchlist = get_watchlist(user_id)
    if not watchlist:
        return []

    incident_suppliers_norm = [normalize(s) for s in result.parsed.affected_suppliers]
    title_norm = normalize(result.parsed.title)

    matches = []
    for entry in watchlist:
        watched_norm = normalize(entry["supplier"])
        hit = (
            any(watched_norm in s or s in watched_norm for s in incident_suppliers_norm)
            or watched_norm in title_norm
        )
        if hit:
            matches.append(entry)
            _record_hit(
                supplier=entry["supplier"],
                incident_id=result.brief.incident_id,
                incident_type=result.parsed.incident_type,
                severity=result.brief.severity_level,
                user_id=user_id,
            )
    return matches


def _record_hit(supplier: str, incident_id: str,
                incident_type: str, severity: str, user_id: int = 0):
    severity_points = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1}
    points = severity_points.get(severity, 1)
    conn = get_connection()
    conn.execute("""
        INSERT INTO watchlist_hits (user_id, supplier, incident_id, incident_type, severity, hit_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (user_id, supplier, incident_id, incident_type, severity, datetime.now().isoformat()))
    conn.execute("""
        UPDATE watchlist
        SET risk_score     = MIN(10, risk_score + ?),
            incident_count = incident_count + 1,
            last_seen      = ?
        WHERE supplier = ? AND user_id = ?
    """, (points, datetime.now().isoformat(), supplier, user_id))
    conn.commit()
    conn.close()


def update_notes(supplier: str, notes: str, user_id: int = 0):
    init_watchlist()
    conn = get_connection()
    conn.execute(
        "UPDATE watchlist SET notes = ? WHERE supplier = ? AND user_id = ?",
        (notes.strip(), supplier, user_id)
    )
    conn.commit()
    conn.close()