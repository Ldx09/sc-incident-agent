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
            incident_type   TEXT NOT NULL UNIQUE,
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
            raw_json        TEXT DEFAULT '{}'
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

Write like a seasoned operator — direct, specific, and actionable. Every line
must be something a team member can actually do, not vague advice.

Return a single valid JSON object. No markdown, no explanation, no code fences.

Fields required:

- title: A clear playbook name e.g. "Port Disruption Response Playbook"

- incident_type_description: 2-3 sentences describing what this category of
  incident looks like and why it keeps happening

- early_warnings: list of 5-8 specific signals that this type of incident
  is developing BEFORE it becomes critical. Each must be a concrete,
  observable signal — not general advice. Example: "Freight forwarder reports
  wait times exceeding 5 days at primary port" not "monitor port conditions".

- first_24h: list of 6-10 prioritized actions to take in the first 24 hours.
  Each action must include WHO does it (job title) and WHAT exactly they do.
  Format each as: "Supply Chain Manager: Contact top 3 freight forwarders
  to assess rerouting capacity and cost delta"

- root_causes: list of 3-6 systemic root causes seen across these incidents.
  Focus on structural vulnerabilities, not one-off events.

- what_worked: list of specific actions, decisions, or responses that proved
  effective across these incidents. Be concrete — name the action and why it
  worked. If no audit data is available, reason from the incident analyses.

- what_failed: list of specific approaches that didn't work or made things
  worse. Be honest and direct.

- key_contacts: list of the types of external contacts to have ready for
  this incident type. Each is an object with "role" and "why_needed" fields.

- success_metrics: list of 4-6 specific metrics to track to know the incident
  is resolving. Each must be measurable. Example: "Port wait times returning
  to baseline of <3 days" not "situation improving".

- prevention_recommendations: list of 3-5 structural changes the company
  should make to reduce frequency or impact of this incident type in future.

- lessons: a single paragraph (4-6 sentences) of the most important insight
  synthesized from all these incidents — the thing your team must never forget.
  Write this in plain, direct language that a new operations manager would
  find immediately useful.

- confidence: one of [high, medium, low] based on how many incidents you had
  to synthesize from (high = 5+, medium = 3-4, low = 1-2)
""".strip()


def generate_playbook(incident_type: str) -> dict | None:
    init_playbooks()
    conn = get_connection()

    rows = conn.execute("""
        SELECT title, severity_level, affected_region, primary_root_cause,
               executive_summary, vulnerability_type, recovery_timeline,
               affected_suppliers, time_sensitivity, financial_min,
               financial_max, analyst_note
        FROM incidents
        WHERE incident_type = ?
        ORDER BY created_at DESC
        LIMIT 20
    """, (incident_type,)).fetchall()

    audit_rows = conn.execute("""
        SELECT aa.action_text, aa.was_taken, aa.outcome, aa.notes,
               io.overall_outcome, io.resolution_time, io.lessons_learned
        FROM action_audits aa
        LEFT JOIN incident_outcomes io ON aa.incident_id = io.incident_id
        WHERE aa.incident_id IN (
            SELECT incident_id FROM incidents WHERE incident_type = ?
        )
    """, (incident_type,)).fetchall()

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
        taken = [r for r in audit_rows if r['was_taken']]
        not_taken = [r for r in audit_rows if not r['was_taken']]
        outcomes = {}
        for r in taken:
            o = r['outcome'] or 'not_recorded'
            outcomes[o] = outcomes.get(o, 0) + 1
        lessons_list = [
            r['lessons_learned'] for r in audit_rows
            if r['lessons_learned']
        ]
        audit_text = f"""
AUDIT TRAIL DATA ({len(audit_rows)} actions tracked):
- Actions taken: {len(taken)}/{len(audit_rows)} ({round(len(taken)/len(audit_rows)*100)}% follow-through)
- Outcome breakdown: {json.dumps(outcomes)}
- Actions most skipped: {', '.join(set(r['action_text'][:60] for r in not_taken[:3])) or 'None recorded'}
- Lessons learned from team: {' | '.join(lessons_list[:5]) or 'None recorded yet'}
""".strip()

    user_message = f"""
Synthesize these {len(rows)} {incident_type.replace('_', ' ')} incidents into a
response playbook for our operations team.

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
            incident_type, title, generated_at, incident_count,
            early_warnings, first_24h, root_causes,
            what_worked, what_failed, key_contacts,
            success_metrics, lessons, raw_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
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


def get_all_playbooks() -> list[dict]:
    init_playbooks()
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM playbooks ORDER BY generated_at DESC"
    ).fetchall()
    conn.close()
    result = []
    for r in rows:
        d = dict(r)
        for field in ["early_warnings", "first_24h", "root_causes",
                      "what_worked", "what_failed", "key_contacts",
                      "success_metrics"]:
            try:
                d[field] = json.loads(d.get(field) or "[]")
            except Exception:
                d[field] = []
        result.append(d)
    return result


def get_playbook(incident_type: str) -> dict | None:
    init_playbooks()
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM playbooks WHERE incident_type = ?",
        (incident_type,)
    ).fetchone()
    conn.close()
    if not row:
        return None
    d = dict(row)
    for field in ["early_warnings", "first_24h", "root_causes",
                  "what_worked", "what_failed", "key_contacts",
                  "success_metrics"]:
        try:
            d[field] = json.loads(d.get(field) or "[]")
        except Exception:
            d[field] = []
    return d


def delete_playbook(incident_type: str):
    init_playbooks()
    conn = get_connection()
    conn.execute(
        "DELETE FROM playbooks WHERE incident_type = ?",
        (incident_type,)
    )
    conn.commit()
    conn.close()


def get_incident_type_counts() -> dict:
    """Return count of incidents per type — used to show which types can generate playbooks."""
    init_db()
    conn = get_connection()
    rows = conn.execute("""
        SELECT incident_type, COUNT(*) as count
        FROM incidents
        GROUP BY incident_type
        ORDER BY count DESC
    """).fetchall()
    conn.close()
    return {r["incident_type"]: r["count"] for r in rows}