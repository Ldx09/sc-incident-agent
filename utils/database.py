import sqlite3
import json
import os
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "incidents.db"


def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS incidents (
            id                   INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id              INTEGER NOT NULL DEFAULT 0,
            incident_id          TEXT NOT NULL,
            created_at           TEXT NOT NULL,
            incident_type        TEXT,
            title                TEXT,
            severity_level       TEXT,
            severity_score       INTEGER,
            vulnerability_type   TEXT,
            recovery_timeline    TEXT,
            financial_min        INTEGER,
            financial_max        INTEGER,
            financial_confidence TEXT,
            affected_region      TEXT,
            affected_suppliers   TEXT,
            time_sensitivity     TEXT,
            primary_root_cause   TEXT,
            executive_summary    TEXT,
            risk_score_overall   INTEGER,
            analyst_note         TEXT,
            raw_json             TEXT
        )
    """)
    conn.commit()
    conn.close()


def save_incident(result, user_id: int = 0) -> int:
    init_db()
    raw = {
        "incident_id":        result.brief.incident_id,
        "severity_level":     result.brief.severity_level,
        "executive_summary":  result.brief.executive_summary,
        "incident_type":      result.parsed.incident_type,
        "title":              result.parsed.title,
        "affected_suppliers": result.parsed.affected_suppliers,
        "affected_region":    result.parsed.affected_region,
        "vulnerability_type": result.analysis.vulnerability_type,
        "primary_root_cause": result.analysis.primary_root_cause,
        "analyst_note":       result.analysis.analyst_note,
        "recovery_timeline":  result.analysis.severity_assessment.recovery_timeline,
        "risk_score_overall": result.brief.risk_score.overall,
        "financial_min":      result.brief.financial_exposure.minimum_usd,
        "financial_max":      result.brief.financial_exposure.maximum_usd,
        "financial_confidence": result.brief.financial_exposure.confidence,
        "time_sensitivity":   result.parsed.time_sensitivity,
        "severity_score":     result.parsed.severity,
    }
    conn = get_connection()
    cursor = conn.execute("""
        INSERT INTO incidents (
            user_id, incident_id, created_at, incident_type, title,
            severity_level, severity_score, vulnerability_type,
            recovery_timeline, financial_min, financial_max,
            financial_confidence, affected_region, affected_suppliers,
            time_sensitivity, primary_root_cause, executive_summary,
            risk_score_overall, analyst_note, raw_json
        ) VALUES (
            :user_id, :incident_id, :created_at, :incident_type, :title,
            :severity_level, :severity_score, :vulnerability_type,
            :recovery_timeline, :financial_min, :financial_max,
            :financial_confidence, :affected_region, :affected_suppliers,
            :time_sensitivity, :primary_root_cause, :executive_summary,
            :risk_score_overall, :analyst_note, :raw_json
        )
    """, {
        **raw,
        "user_id":            user_id,
        "created_at":         datetime.now().isoformat(),
        "affected_suppliers": json.dumps(result.parsed.affected_suppliers),
        "raw_json":           json.dumps(raw),
    })
    conn.commit()
    row_id = cursor.lastrowid
    conn.close()
    return row_id


def get_all_incidents(user_id: int = 0) -> list[dict]:
    init_db()
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM incidents WHERE user_id = ? ORDER BY created_at DESC",
        (user_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_stats(user_id: int = 0) -> dict:
    init_db()
    conn = get_connection()

    total = conn.execute(
        "SELECT COUNT(*) FROM incidents WHERE user_id = ?", (user_id,)
    ).fetchone()[0]

    severity_rows = conn.execute("""
        SELECT severity_level, COUNT(*) as count
        FROM incidents WHERE user_id = ?
        GROUP BY severity_level
    """, (user_id,)).fetchall()

    vuln_rows = conn.execute("""
        SELECT vulnerability_type, COUNT(*) as count
        FROM incidents WHERE user_id = ?
        GROUP BY vulnerability_type ORDER BY count DESC LIMIT 8
    """, (user_id,)).fetchall()

    type_rows = conn.execute("""
        SELECT incident_type, COUNT(*) as count
        FROM incidents WHERE user_id = ?
        GROUP BY incident_type ORDER BY count DESC
    """, (user_id,)).fetchall()

    avg_risk = conn.execute(
        "SELECT AVG(risk_score_overall) FROM incidents WHERE user_id = ?",
        (user_id,)
    ).fetchone()[0]

    avg_financial_max = conn.execute(
        "SELECT AVG(financial_max) FROM incidents WHERE user_id = ?",
        (user_id,)
    ).fetchone()[0]

    recent = conn.execute("""
        SELECT incident_id, created_at, title, severity_level,
               incident_type, vulnerability_type, recovery_timeline,
               risk_score_overall, financial_min, financial_max,
               affected_region
        FROM incidents WHERE user_id = ?
        ORDER BY created_at DESC LIMIT 20
    """, (user_id,)).fetchall()

    conn.close()
    return {
        "total":             total,
        "severity_counts":   {r["severity_level"]: r["count"] for r in severity_rows},
        "vuln_counts":       {r["vulnerability_type"]: r["count"] for r in vuln_rows},
        "type_counts":       {r["incident_type"]: r["count"] for r in type_rows},
        "avg_risk":          round(avg_risk, 1) if avg_risk else 0,
        "avg_financial_max": int(avg_financial_max) if avg_financial_max else 0,
        "recent":            [dict(r) for r in recent],
    }


def delete_incident(incident_id: str, user_id: int = 0):
    init_db()
    conn = get_connection()
    conn.execute(
        "DELETE FROM incidents WHERE incident_id = ? AND user_id = ?",
        (incident_id, user_id)
    )
    conn.commit()
    conn.close()