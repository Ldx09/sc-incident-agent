import sqlite3
import json
from datetime import datetime
from utils.database import get_connection, init_db


def init_watchlist():
    """Create watchlist tables if they don't exist."""
    init_db()
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS watchlist (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            supplier     TEXT NOT NULL UNIQUE,
            added_at     TEXT NOT NULL,
            notes        TEXT DEFAULT '',
            risk_score   INTEGER DEFAULT 0,
            incident_count INTEGER DEFAULT 0,
            last_seen    TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS watchlist_hits (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            supplier     TEXT NOT NULL,
            incident_id  TEXT NOT NULL,
            incident_type TEXT,
            severity     TEXT,
            hit_at       TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def add_supplier(supplier: str, notes: str = "") -> bool:
    """Add a supplier to the watchlist. Returns True if added, False if already exists."""
    init_watchlist()
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO watchlist (supplier, added_at, notes) VALUES (?, ?, ?)",
            (supplier.strip(), datetime.now().isoformat(), notes.strip())
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def remove_supplier(supplier: str):
    init_watchlist()
    conn = get_connection()
    conn.execute("DELETE FROM watchlist WHERE supplier = ?", (supplier,))
    conn.execute("DELETE FROM watchlist_hits WHERE supplier = ?", (supplier,))
    conn.commit()
    conn.close()


def get_watchlist() -> list[dict]:
    init_watchlist()
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM watchlist ORDER BY risk_score DESC, supplier ASC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_hits_for_supplier(supplier: str) -> list[dict]:
    init_watchlist()
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM watchlist_hits WHERE supplier = ? ORDER BY hit_at DESC",
        (supplier,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def check_incident_against_watchlist(result) -> list[dict]:
    init_watchlist()

    watchlist = get_watchlist()
    if not watchlist:
        return []

    # Normalize: lowercase, strip spaces/punctuation for fuzzy matching
    def normalize(s: str) -> str:
        import re
        return re.sub(r'[\s\.\-_,]', '', s.lower())

    incident_suppliers_raw  = result.parsed.affected_suppliers
    incident_suppliers_norm = [normalize(s) for s in incident_suppliers_raw]
    title_norm              = normalize(result.parsed.title)

    matches = []
    for entry in watchlist:
        watched_norm = normalize(entry["supplier"])
        hit = (
            any(
                watched_norm in s or s in watched_norm
                for s in incident_suppliers_norm
            )
            or watched_norm in title_norm
        )
        if hit:
            matches.append(entry)
            _record_hit(
                supplier=entry["supplier"],
                incident_id=result.brief.incident_id,
                incident_type=result.parsed.incident_type,
                severity=result.brief.severity_level,
            )

    return matches

def _record_hit(supplier: str, incident_id: str,
                incident_type: str, severity: str):
    """Record a watchlist hit and update the supplier's risk score."""
    severity_points = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1}
    points = severity_points.get(severity, 1)

    conn = get_connection()
    conn.execute("""
        INSERT INTO watchlist_hits (supplier, incident_id, incident_type, severity, hit_at)
        VALUES (?, ?, ?, ?, ?)
    """, (supplier, incident_id, incident_type, severity, datetime.now().isoformat()))

    conn.execute("""
        UPDATE watchlist
        SET risk_score    = MIN(10, risk_score + ?),
            incident_count = incident_count + 1,
            last_seen      = ?
        WHERE supplier = ?
    """, (points, datetime.now().isoformat(), supplier))

    conn.commit()
    conn.close()


def update_notes(supplier: str, notes: str):
    init_watchlist()
    conn = get_connection()
    conn.execute(
        "UPDATE watchlist SET notes = ? WHERE supplier = ?",
        (notes.strip(), supplier)
    )
    conn.commit()
    conn.close()