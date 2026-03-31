import sqlite3
import json
from datetime import datetime
from utils.database import get_connection, init_db


def init_audit():
    init_db()
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS action_audits (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id         INTEGER NOT NULL DEFAULT 0,
            incident_id     TEXT NOT NULL,
            action_priority INTEGER NOT NULL,
            action_text     TEXT NOT NULL,
            action_owner    TEXT,
            action_deadline TEXT,
            was_taken       INTEGER DEFAULT 0,
            outcome         TEXT DEFAULT 'not_recorded',
            notes           TEXT DEFAULT '',
            recorded_at     TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS incident_outcomes (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id         INTEGER NOT NULL DEFAULT 0,
            incident_id     TEXT NOT NULL,
            overall_outcome TEXT DEFAULT 'ongoing',
            resolution_time TEXT,
            lessons_learned TEXT DEFAULT '',
            recorded_at     TEXT,
            UNIQUE(user_id, incident_id)
        )
    """)
    conn.commit()
    conn.close()


def save_audit(incident_id: str, actions: list[dict],
               overall_outcome: str, resolution_time: str,
               lessons_learned: str, user_id: int = 0):
    init_audit()
    conn = get_connection()
    conn.execute(
        "DELETE FROM action_audits WHERE incident_id = ? AND user_id = ?",
        (incident_id, user_id)
    )
    conn.execute(
        "DELETE FROM incident_outcomes WHERE incident_id = ? AND user_id = ?",
        (incident_id, user_id)
    )
    for a in actions:
        conn.execute("""
            INSERT INTO action_audits (
                user_id, incident_id, action_priority, action_text,
                action_owner, action_deadline, was_taken, outcome, notes, recorded_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id, incident_id, a["priority"], a["action"],
            a.get("owner", ""), a.get("deadline", ""),
            1 if a["was_taken"] else 0,
            a["outcome"], a.get("notes", ""),
            datetime.now().isoformat()
        ))
    conn.execute("""
        INSERT INTO incident_outcomes (
            user_id, incident_id, overall_outcome,
            resolution_time, lessons_learned, recorded_at
        ) VALUES (?, ?, ?, ?, ?, ?)
    """, (
        user_id, incident_id, overall_outcome,
        resolution_time, lessons_learned,
        datetime.now().isoformat()
    ))
    conn.commit()
    conn.close()


def get_audit(incident_id: str, user_id: int = 0) -> dict | None:
    init_audit()
    conn = get_connection()
    actions = conn.execute(
        "SELECT * FROM action_audits WHERE incident_id = ? AND user_id = ? ORDER BY action_priority",
        (incident_id, user_id)
    ).fetchall()
    outcome = conn.execute(
        "SELECT * FROM incident_outcomes WHERE incident_id = ? AND user_id = ?",
        (incident_id, user_id)
    ).fetchone()
    conn.close()
    if not actions and not outcome:
        return None
    return {
        "actions": [dict(a) for a in actions],
        "outcome": dict(outcome) if outcome else None,
    }


def get_audit_stats(user_id: int = 0) -> dict:
    init_audit()
    conn = get_connection()

    total_actions = conn.execute(
        "SELECT COUNT(*) FROM action_audits WHERE user_id = ?", (user_id,)
    ).fetchone()[0]

    taken = conn.execute(
        "SELECT COUNT(*) FROM action_audits WHERE was_taken = 1 AND user_id = ?",
        (user_id,)
    ).fetchone()[0]

    outcome_rows = conn.execute("""
        SELECT outcome, COUNT(*) as count FROM action_audits
        WHERE was_taken = 1 AND user_id = ? GROUP BY outcome
    """, (user_id,)).fetchall()

    overall_rows = conn.execute("""
        SELECT overall_outcome, COUNT(*) as count FROM incident_outcomes
        WHERE user_id = ? GROUP BY overall_outcome
    """, (user_id,)).fetchall()

    priority_rows = conn.execute("""
        SELECT action_priority, SUM(was_taken) as taken, COUNT(*) as total
        FROM action_audits WHERE user_id = ?
        GROUP BY action_priority ORDER BY action_priority
    """, (user_id,)).fetchall()

    incidents_audited = conn.execute(
        "SELECT COUNT(DISTINCT incident_id) FROM incident_outcomes WHERE user_id = ?",
        (user_id,)
    ).fetchone()[0]

    conn.close()
    follow_through = round(taken / total_actions * 100) if total_actions > 0 else 0

    return {
        "total_actions":      total_actions,
        "actions_taken":      taken,
        "follow_through_pct": follow_through,
        "incidents_audited":  incidents_audited,
        "outcome_counts":     {r["outcome"]: r["count"] for r in outcome_rows},
        "overall_counts":     {r["overall_outcome"]: r["count"] for r in overall_rows},
        "priority_rates": [
            {
                "priority": r["action_priority"],
                "taken":    r["taken"],
                "total":    r["total"],
                "rate":     round(r["taken"] / r["total"] * 100) if r["total"] else 0
            }
            for r in priority_rows
        ],
    }