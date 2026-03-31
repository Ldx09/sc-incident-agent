import json
import sqlite3
from datetime import datetime
from utils.database import get_connection, init_db
from utils.helpers_openai import call_model


def init_playbooks():
    init_db()
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS playbooks (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id         INTEGER NOT NULL DEFAULT 0,
            incident_type   TEXT NOT NULL,
            title           TEXT NOT NULL,
            generated_at    TEXT NOT NULL,
            incident_count  INTEGER DEFAULT 0,
            early_warnings  TEXT DEFAULT '[]',
            first_24h       TEXT DEFAULT '[]',
            root_causes     TEXT DEFAULT '[]',
            what_worked     TEXT DEFAULT '[]',
            what_failed     TEXT DEFAULT '[]',
            key_contacts    TEXT DEFAULT '[]',
            success_metrics TEXT DEFAULT '[]',
            lessons         TEXT DEFAULT '',
            raw_json        TEXT DEFAULT '{}',
            UNIQUE(user_id, incident_type)
        )
    """)
    conn.commit()
    conn.close()


PLAYBOOK_SYSTEM_PROMPT = """
You are a senior supply chain operations director writing a standard operating
procedure (SOP) playbook for your team. You have been given a set of real
supply chain incidents of the same type that your company has experienced.

Your job is to synthesize these incidents into a practical, reusable response
playbook that any operations manager could pick up and follow the next time
this type of incident occurs.

Write like a seasoned operator — direct, specific, and actionable.

Return a single valid JSON object. No markdown, no explanation, no code fences.

Required fields:

- title: e.g. "Port Disruption Response Playbook"
- incident_type_description: 2-3 sentences on what this incident type looks like
- early_warnings: list of 5-8 specific observable signals BEFORE it becomes critical
- first_24h: list of 6-10 prioritized actions. Format each as "Job Title: What to do exactly"
- root_causes: list of 3-6 systemic root causes seen across incidents
- what_worked: list of specific actions that proved effective
- what_failed: list of approaches that didn't work or made things worse
- key_contacts: list of objects with "role" and "why_needed" fields
- success_metrics: list of 4-6 measurable metrics to track resolution
- prevention_recommendations: list of 3-5 structural changes to prevent recurrence
- lessons: single paragraph — the most important insight. Plain direct language.
- confidence: one of [high, medium, low]
""".strip()


def generate_playbook(incident_type: str, user_id: int = 0) -> dict | None:
    init_playbooks()
    conn = get_connection()

    rows = conn.execute("""
        SELECT title, severity_level, affected_region, primary_root_cause,
               executive_summary, vulnerability_type, recovery_timeline,
               affected_suppliers, time_sensitivity, financial_min,
               financial_max, analyst_note
        FROM incidents
        WHERE incident_type = ? AND user_id = ?
        ORDER BY created_at DESC LIMIT 20
    """, (incident_type, user_id)).fetchall()

    audit_rows = conn.execute("""
        SELECT aa.action_text, aa.was_taken, aa.outcome, aa.notes,
               io.overall_outcome, io.resolution_time, io.lessons_learned
        FROM action_audits aa
        LEFT JOIN incident_outcomes io
            ON aa.incident_id = io.incident_id AND io.user_id = aa.user_id
        WHERE aa.user_id = ? AND aa.incident_id IN (
            SELECT incident_id FROM incidents
            WHERE incident_type = ? AND user_id = ?
        )
    """, (user_id, incident_type, user_id)).fetchall()

    conn.close()

    if not rows:
        return None

    incidents_text = []
    for i, r in enumerate(rows, 1):
        fin_min = r['financial_min'] or 0
        fin_max = r['financial_max'] or 0
        incidents_text.append(f"""
Incident {i}:
- Title: {r['title']}
- Severity: {r['severity_level']}
- Region: {r['affected_region']}
- Suppliers affected: {r['affected_suppliers']}
- Root cause: {r['primary_root_cause']}
- Vulnerability: {r['vulnerability_type']}
- Recovery timeline: {r['recovery_timeline']}
- Financial exposure: ${fin_min:,} - ${fin_max:,}
- Executive summary: {r['executive_summary']}
- Analyst note: {r['analyst_note'] or 'None'}
""".strip())

    audit_text = ""
    if audit_rows:
        taken     = [r for r in audit_rows if r['was_taken']]
        not_taken = [r for r in audit_rows if not r['was_taken']]
        outcomes  = {}
        for r in taken:
            o = r['outcome'] or 'not_recorded'
            outcomes[o] = outcomes.get(o, 0) + 1
        lessons_list = [r['lessons_learned'] for r in audit_rows if r['lessons_learned']]
        audit_text = f"""
AUDIT TRAIL DATA ({len(audit_rows)} actions tracked):
- Actions taken: {len(taken)}/{len(audit_rows)} ({round(len(taken)/len(audit_rows)*100)}% follow-through)
- Outcome breakdown: {json.dumps(outcomes)}
- Lessons learned: {' | '.join(lessons_list[:5]) or 'None recorded yet'}
""".strip()

    user_message = f"""
Synthesize these {len(rows)} {incident_type.replace('_', ' ')} incidents into
a response playbook for our operations team.

{chr(10).join(incidents_text)}

{audit_text if audit_text else 'No audit trail data available yet.'}

Return the playbook as JSON.
""".strip()

    raw = call_model(
        system_prompt=PLAYBOOK_SYSTEM_PROMPT,
        user_message=user_message,
        max_tokens=3000
    )

    clean = raw
    if clean.startswith("```"):
        clean = clean.split("\n", 1)[-1]
        clean = clean.rsplit("```", 1)[0]
    clean = clean.strip()

    data = json.loads(clean)

    conn = get_connection()
    conn.execute("""
        INSERT OR REPLACE INTO playbooks (
            user_id, incident_type, title, generated_at, incident_count,
            early_warnings, first_24h, root_causes, what_worked, what_failed,
            key_contacts, success_metrics, lessons, raw_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        user_id,
        incident_type,
        data.get("title", f"{incident_type.replace('_', ' ').title()} Playbook"),
        datetime.now().isoformat(),
        len(rows),
        json.dumps(data.get("early_warnings", [])),
        json.dumps(data.get("first_24h", [])),
        json.dumps(data.get("root_causes", [])),
        json.dumps(data.get("what_worked", [])),
        json.dumps(data.get("what_failed", [])),
        json.dumps(data.get("key_contacts", [])),
        json.dumps(data.get("success_metrics", [])),
        data.get("lessons", ""),
        json.dumps(data)
    ))
    conn.commit()
    conn.close()

    return data


def get_all_playbooks(user_id: int = 0) -> list[dict]:
    init_playbooks()
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM playbooks WHERE user_id = ? ORDER BY generated_at DESC",
        (user_id,)
    ).fetchall()
    conn.close()
    result = []
    for r in rows:
        d = dict(r)
        for field in ["early_warnings", "first_24h", "root_causes",
                      "what_worked", "what_failed", "key_contacts", "success_metrics"]:
            try:
                d[field] = json.loads(d.get(field) or "[]")
            except Exception:
                d[field] = []
        result.append(d)
    return result


def delete_playbook(incident_type: str, user_id: int = 0):
    init_playbooks()
    conn = get_connection()
    conn.execute(
        "DELETE FROM playbooks WHERE incident_type = ? AND user_id = ?",
        (incident_type, user_id)
    )
    conn.commit()
    conn.close()


def get_incident_type_counts(user_id: int = 0) -> dict:
    init_db()
    conn = get_connection()
    rows = conn.execute("""
        SELECT incident_type, COUNT(*) as count
        FROM incidents WHERE user_id = ?
        GROUP BY incident_type ORDER BY count DESC
    """, (user_id,)).fetchall()
    conn.close()
    return {r["incident_type"]: r["count"] for r in rows}