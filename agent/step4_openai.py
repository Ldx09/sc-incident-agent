import json
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pydantic import BaseModel
from typing import Literal
from utils.helpers_openai import call_model
from agent.step1_openai import ParsedIncident
from agent.step2_openai import EnrichedContext
from agent.step3_openai import RootCauseAnalysis


BRIEF_SYSTEM_PROMPT = """
You are a senior supply chain operations manager writing an incident brief
for company leadership. You have received a full analysis from your team.

Your job is to synthesize everything into a clear, actionable incident brief
that a VP or C-suite executive can read in 3 minutes and immediately know
what to do.

Write like a senior operator — direct, specific, no fluff, no jargon.
Every sentence must earn its place.

Return a single valid JSON object. No markdown, no explanation, no code fences.

The JSON must contain these fields:

- incident_id: a generated ID in format INC-YYYYMMDD-XXX (use today's date,
  XXX is a random 3-digit number)

- executive_summary: exactly 3 sentences.
  Sentence 1: what happened and where.
  Sentence 2: why it matters (business impact).
  Sentence 3: what decision is needed right now.

- severity_level: one of [LOW, MEDIUM, HIGH, CRITICAL]

- status: always "ACTIVE" for a new incident

- immediate_actions: list of exactly 5 actions, priority ordered (most urgent
  first). Each action must be an object with:
    - priority: integer 1-5
    - action: what to do (one clear sentence starting with a verb)
    - owner: who should do this (job title, not name)
    - deadline: when (e.g. "Within 2 hours", "By end of day", "Within 48 hours")
    - why: one sentence explaining the consequence of not doing this

- risk_score: object with:
    - overall: integer 1-10
    - operational: integer 1-10
    - financial: integer 1-10
    - reputational: integer 1-10
    - reasoning: one sentence explaining the overall score

- financial_exposure: object with:
    - minimum_usd: conservative low estimate as integer (no $ sign, no commas)
    - maximum_usd: conservative high estimate as integer
    - confidence: one of [low, medium, high]
    - notes: one sentence on what drives the range

- alternative_options: list of 2-4 concrete alternatives the company can
  pursue right now. Each must be an object with:
    - option: what to do
    - pros: list of 2-3 advantages
    - cons: list of 2-3 disadvantages
    - estimated_cost_impact: e.g. "+15% freight cost", "No additional cost"
    - feasibility: one of [immediate, short_term, medium_term]

- stakeholder_email: a complete ready-to-send email. Object with:
    - to: who receives it (job title)
    - subject: email subject line
    - body: the full email body — professional, direct, 150-200 words.
      Include: what happened, current status, what you need from them,
      and next update time. Sign off as "Supply Chain Operations Team"

- key_decisions_required: list of 2-3 specific decisions that leadership
  must make, with a deadline for each. Each is an object with:
    - decision: what needs to be decided
    - deadline: when
    - consequence_of_delay: what happens if this isn't decided in time

- monitoring_plan: list of 3-5 specific things to track over the next 72
  hours — what to watch, how often to check, and what threshold triggers
  escalation. Each is an object with "metric", "frequency", and "escalation_trigger"

- next_update: when the next situation report should be issued
  (e.g. "6 hours", "24 hours", "48 hours")
""".strip()


class ImmediateAction(BaseModel):
    priority: int
    action: str
    owner: str
    deadline: str
    why: str


class RiskScore(BaseModel):
    overall: int
    operational: int
    financial: int
    reputational: int
    reasoning: str


class FinancialExposure(BaseModel):
    minimum_usd: int
    maximum_usd: int
    confidence: Literal["low", "medium", "high"]
    notes: str


class AlternativeOption(BaseModel):
    option: str
    pros: list[str]
    cons: list[str]
    estimated_cost_impact: str
    feasibility: Literal["immediate", "short_term", "medium_term"]


class StakeholderEmail(BaseModel):
    to: str
    subject: str
    body: str


class KeyDecision(BaseModel):
    decision: str
    deadline: str
    consequence_of_delay: str


class MonitoringItem(BaseModel):
    metric: str
    frequency: str
    escalation_trigger: str


class IncidentBrief(BaseModel):
    incident_id: str
    executive_summary: str
    severity_level: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    status: str
    immediate_actions: list[ImmediateAction]
    risk_score: RiskScore
    financial_exposure: FinancialExposure
    alternative_options: list[AlternativeOption]
    stakeholder_email: StakeholderEmail
    key_decisions_required: list[KeyDecision]
    monitoring_plan: list[MonitoringItem]
    next_update: str


def generate_brief(
    parsed: ParsedIncident,
    context: EnrichedContext,
    analysis: RootCauseAnalysis
) -> IncidentBrief:
    """
    Step 4: Take all 3 prior outputs, return a complete IncidentBrief.
    """
    full_context = f"""
=== INCIDENT OVERVIEW ===
Type: {parsed.incident_type}
Title: {parsed.title}
Region: {parsed.affected_region}
Time sensitivity: {parsed.time_sensitivity}
Financial impact estimate: {parsed.estimated_financial_impact}
Affected suppliers: {', '.join(parsed.affected_suppliers) or 'None listed'}
Affected products: {', '.join(parsed.affected_products) or 'None listed'}

Key facts:
{chr(10).join(f'- {f}' for f in parsed.key_facts)}

=== ROOT CAUSE ANALYSIS ===
Primary root cause: {analysis.primary_root_cause}
Vulnerability type: {analysis.vulnerability_type}
Confidence: {analysis.confidence_level}

Contributing factors:
{chr(10).join(f'- {f}' for f in analysis.contributing_factors)}

Impact chain:
{chr(10).join(f'{i+1}. {s}' for i, s in enumerate(analysis.impact_chain))}

Severity assessment:
- Operational: {analysis.severity_assessment.operational_impact}
- Financial: {analysis.severity_assessment.financial_impact}
- Reputational: {analysis.severity_assessment.reputational_impact}
- Recovery timeline: {analysis.severity_assessment.recovery_timeline}

Immediate risks (next 48-72h):
{chr(10).join(f'- {r}' for r in analysis.immediate_risks)}

Systemic weaknesses exposed:
{chr(10).join(f'- {w}' for w in analysis.systemic_weaknesses_exposed)}

Analyst note: {analysis.analyst_note}

=== RESEARCH CONTEXT ===
Current situation: {context.current_situation}
Market context: {context.market_context}

Available alternatives:
{chr(10).join(f'- {a.name}: {a.notes}' for a in context.alternative_suppliers_or_routes) or 'None identified'}

Risk amplifiers:
{chr(10).join(f'- {r}' for r in context.risk_amplifiers)}

Risk mitigators:
{chr(10).join(f'- {r}' for r in context.risk_mitigators)}

Regulatory/legal context: {context.regulatory_or_legal_context or 'None identified'}
""".strip()

    raw = call_model(
        system_prompt=BRIEF_SYSTEM_PROMPT,
        user_message=(
            "Generate a complete incident brief for leadership based on this analysis. "
            "Return as JSON:\n\n"
            f"{full_context}"
        ),
        max_tokens=3000
    )

    clean = raw
    if clean.startswith("```"):
        clean = clean.split("\n", 1)[-1]
        clean = clean.rsplit("```", 1)[0]
    clean = clean.strip()

    try:
        data = json.loads(clean)
    except json.JSONDecodeError as e:
        raise ValueError(f"Model returned invalid JSON: {e}\nRaw:\n{clean}")

    brief = IncidentBrief(**data)
    return brief


if __name__ == "__main__":
    from agent.step1_openai import parse_incident
    from agent.step2_openai import research_incident
    from agent.step3_openai import analyze_incident
    from tests.test_incidents import TEST_INCIDENTS

    incident = TEST_INCIDENTS[0]

    print("=" * 60)
    print("STEP 4 — BRIEF GENERATOR TEST")
    print(f"Incident: {incident['id']} — {incident['label']}")
    print("=" * 60)

    print("\n[Step 1] Parsing incident...")
    parsed = parse_incident(incident["text"])
    print(f"  Done: {parsed.incident_type}, severity {parsed.severity}/5")

    print("[Step 2] Researching context...")
    context = research_incident(parsed)
    print(f"  Done: confidence={context.confidence_level}")

    print("[Step 3] Analyzing root cause...")
    analysis = analyze_incident(parsed, context)
    print(f"  Done: {analysis.vulnerability_type}")

    print("[Step 4] Generating brief...")
    brief = generate_brief(parsed, context, analysis)

    print(f"\n{'=' * 60}")
    print(f"INCIDENT BRIEF — {brief.incident_id}")
    print(f"Severity: {brief.severity_level}  |  Status: {brief.status}")
    print(f"{'=' * 60}")

    print(f"\nEXECUTIVE SUMMARY:")
    print(f"  {brief.executive_summary}")

    print(f"\nRISK SCORES:")
    r = brief.risk_score
    print(f"  Overall: {r.overall}/10  |  Ops: {r.operational}/10  "
          f"|  Financial: {r.financial}/10  |  Reputational: {r.reputational}/10")
    print(f"  {r.reasoning}")

    print(f"\nFINANCIAL EXPOSURE:")
    f = brief.financial_exposure
    print(f"  ${f.minimum_usd:,} — ${f.maximum_usd:,} (confidence: {f.confidence})")
    print(f"  {f.notes}")

    print(f"\nIMMEDIATE ACTIONS:")
    for action in brief.immediate_actions:
        print(f"  [{action.priority}] {action.action}")
        print(f"       Owner: {action.owner}  |  By: {action.deadline}")
        print(f"       Why: {action.why}")

    print(f"\nKEY DECISIONS REQUIRED:")
    for d in brief.key_decisions_required:
        print(f"  • {d.decision}")
        print(f"    Deadline: {d.deadline}")
        print(f"    If delayed: {d.consequence_of_delay}")

    print(f"\nALTERNATIVE OPTIONS:")
    for opt in brief.alternative_options:
        print(f"  • {opt.option} [{opt.feasibility}] — {opt.estimated_cost_impact}")

    print(f"\nSTAKEHOLDER EMAIL:")
    print(f"  To: {brief.stakeholder_email.to}")
    print(f"  Subject: {brief.stakeholder_email.subject}")
    print(f"  ---")
    for line in brief.stakeholder_email.body.split("\n"):
        print(f"  {line}")

    print(f"\nMONITORING PLAN (next 72h):")
    for m in brief.monitoring_plan:
        print(f"  • {m.metric} — check {m.frequency}")
        print(f"    Escalate if: {m.escalation_trigger}")

    print(f"\nNEXT UPDATE: {brief.next_update}")
    print(f"\n{'=' * 60}")
    print("Full pipeline working. All 4 steps complete.")
    print("=" * 60)