import json
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pydantic import BaseModel
from typing import Literal
from utils.helpers_openai import call_model
from agent.step1_openai import ParsedIncident
from agent.step2_openai import EnrichedContext


ANALYZER_SYSTEM_PROMPT = """
You are a senior supply chain risk analyst with 20 years of experience
across manufacturing, logistics, and procurement. You think in systems —
supply chain incidents rarely have a single cause, and the visible
disruption is often a symptom of deeper structural vulnerabilities.

You have been given two inputs:
1. A parsed incident report (structured data)
2. An enriched context brief (research findings)

Perform a rigorous root cause analysis and return a single valid JSON
object. No markdown, no explanation, no code fences. Raw JSON only.

The JSON must contain these fields:

- primary_root_cause: one clear sentence naming the single most fundamental
  cause. This is NOT the event — it is WHY the event is causing damage.
  Example: not "the port is congested" but "over-reliance on a single port
  with no pre-approved alternate routing agreements"

- contributing_factors: list of 3-5 factors that amplified the impact.
  Mix immediate causes with systemic causes.

- vulnerability_type: one of [single_source_dependency,
  geographic_concentration, insufficient_inventory_buffer,
  lack_of_supplier_diversification, poor_visibility, contract_gap,
  no_contingency_plan, financial_exposure, regulatory_non_compliance, other]

- impact_chain: ordered list of 4-6 steps showing how this incident
  propagates from the trigger to the final business impact. Domino effect.

- severity_assessment: object with:
    - operational_impact: one of [minimal, moderate, significant, severe, critical]
    - financial_impact: one of [minimal, moderate, significant, severe, critical]
    - reputational_impact: one of [minimal, moderate, significant, severe, critical]
    - recovery_timeline: realistic estimate e.g. "2-3 weeks", "3-6 months"
    - confidence: one of [high, medium, low]

- immediate_risks: list of 3-5 things that make this significantly worse
  in the next 48-72 hours if no action is taken

- systemic_weaknesses_exposed: list of 2-4 deeper supply chain design flaws
  this incident has revealed

- analogous_incidents: list of 1-3 similar real industry incidents.
  Each must have "company", "year" (integer), and "lesson" fields.

- confidence_level: one of [high, medium, low]

- analyst_note: one paragraph of honest direct commentary — what concerns
  you most, what the numbers miss, what leadership must understand.
  Plain language, not corporate speak.
""".strip()


class SeverityAssessment(BaseModel):
    operational_impact: Literal["minimal", "moderate", "significant", "severe", "critical"]
    financial_impact: Literal["minimal", "moderate", "significant", "severe", "critical"]
    reputational_impact: Literal["minimal", "moderate", "significant", "severe", "critical"]
    recovery_timeline: str
    confidence: Literal["high", "medium", "low"]


class AnalogousIncident(BaseModel):
    company: str
    year: int
    lesson: str


class RootCauseAnalysis(BaseModel):
    primary_root_cause: str
    contributing_factors: list[str]
    vulnerability_type: Literal[
        "single_source_dependency", "geographic_concentration",
        "insufficient_inventory_buffer", "lack_of_supplier_diversification",
        "poor_visibility", "contract_gap", "no_contingency_plan",
        "financial_exposure", "regulatory_non_compliance", "other"
    ]
    impact_chain: list[str]
    severity_assessment: SeverityAssessment
    immediate_risks: list[str]
    systemic_weaknesses_exposed: list[str]
    analogous_incidents: list[AnalogousIncident]
    confidence_level: Literal["high", "medium", "low"]
    analyst_note: str


def analyze_incident(
    parsed: ParsedIncident,
    context: EnrichedContext
) -> RootCauseAnalysis:
    """
    Step 3: Take ParsedIncident + EnrichedContext, return RootCauseAnalysis.
    """
    combined_input = f"""
=== PARSED INCIDENT ===
Type: {parsed.incident_type}
Title: {parsed.title}
Region: {parsed.affected_region}
Severity: {parsed.severity}/5 — {parsed.severity_reasoning}
Time sensitivity: {parsed.time_sensitivity}
Financial impact: {parsed.estimated_financial_impact}
Affected suppliers: {', '.join(parsed.affected_suppliers) or 'None listed'}
Affected products: {', '.join(parsed.affected_products) or 'None listed'}

Key facts:
{chr(10).join(f'- {f}' for f in parsed.key_facts)}

Missing information:
{chr(10).join(f'- {m}' for m in parsed.missing_information)}

=== RESEARCH CONTEXT ===
Confidence level: {context.confidence_level}

Current situation:
{context.current_situation}

Market context:
{context.market_context}

Risk amplifiers:
{chr(10).join(f'- {r}' for r in context.risk_amplifiers)}

Risk mitigators:
{chr(10).join(f'- {r}' for r in context.risk_mitigators)}

Alternatives identified:
{chr(10).join(f'- {a.name}: {a.notes}' for a in context.alternative_suppliers_or_routes) or 'None found'}

Regulatory/legal context:
{context.regulatory_or_legal_context or 'None identified'}

Historical precedents:
{chr(10).join(f'- {p}' for p in context.historical_precedents) or 'None found'}

Research gaps:
{chr(10).join(f'- {g}' for g in context.research_gaps)}
""".strip()

    raw = call_model(
        system_prompt=ANALYZER_SYSTEM_PROMPT,
        user_message=(
            "Perform a root cause analysis on this supply chain incident. "
            "Return your analysis as JSON:\n\n"
            f"{combined_input}"
        ),
        max_tokens=2048
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

    VALID_IMPACTS = {"minimal", "moderate", "significant", "severe", "critical"}
    VALID_CONFIDENCE = {"high", "medium", "low"}
    fallback_map = {
        "unknown": "moderate", "n/a": "minimal", "none": "minimal",
        "high": "severe", "low": "minimal", "medium": "moderate"
    }
    if "severity_assessment" in data and isinstance(data["severity_assessment"], dict):
        sa = data["severity_assessment"]
        for field in ["operational_impact", "financial_impact", "reputational_impact"]:
            if field in sa and sa[field] not in VALID_IMPACTS:
                sa[field] = fallback_map.get(str(sa[field]).lower(), "moderate")
        if "confidence" in sa and sa["confidence"] not in VALID_CONFIDENCE:
            sa["confidence"] = fallback_map.get(str(sa["confidence"]).lower(), "medium")

    if "analogous_incidents" in data:
        normalized = []
        for item in data["analogous_incidents"]:
            if isinstance(item, dict):
                normalized.append({
                    "company": item.get("company", "Unknown"),
                    "year": int(item.get("year", 2020)),
                    "lesson": item.get("lesson", "")
                })
        data["analogous_incidents"] = normalized

    analysis = RootCauseAnalysis(**data)
    return analysis


if __name__ == "__main__":
    from agent.step1_openai import parse_incident
    from agent.step2_openai import research_incident
    from tests.test_incidents import TEST_INCIDENTS

    test_cases = [
        TEST_INCIDENTS[1],
        TEST_INCIDENTS[5],
    ]

    print("=" * 60)
    print("STEP 3 — ROOT CAUSE ANALYZER TEST")
    print("=" * 60)

    for incident in test_cases:
        print(f"\nTesting: {incident['id']} — {incident['label']}")
        print("-" * 40)

        print("  [Step 1] Parsing...")
        parsed = parse_incident(incident["text"])

        print("  [Step 2] Researching...")
        context = research_incident(parsed)

        print("  [Step 3] Analyzing...")
        analysis = analyze_incident(parsed, context)

        print(f"\n  PRIMARY ROOT CAUSE:")
        print(f"    {analysis.primary_root_cause}")
        print(f"\n  VULNERABILITY TYPE:  {analysis.vulnerability_type}")
        print(f"  CONFIDENCE:          {analysis.confidence_level}")
        print(f"\n  SEVERITY ASSESSMENT:")
        s = analysis.severity_assessment
        print(f"    Operational:  {s.operational_impact}")
        print(f"    Financial:    {s.financial_impact}")
        print(f"    Reputational: {s.reputational_impact}")
        print(f"    Recovery:     {s.recovery_timeline}")
        print(f"\n  IMPACT CHAIN:")
        for i, step in enumerate(analysis.impact_chain, 1):
            print(f"    {i}. {step}")
        print(f"\n  CONTRIBUTING FACTORS:")
        for f in analysis.contributing_factors:
            print(f"    • {f}")
        print(f"\n  IMMEDIATE RISKS (next 48-72h):")
        for r in analysis.immediate_risks:
            print(f"    ! {r}")
        print(f"\n  SYSTEMIC WEAKNESSES EXPOSED:")
        for w in analysis.systemic_weaknesses_exposed:
            print(f"    ~ {w}")
        if analysis.analogous_incidents:
            print(f"\n  ANALOGOUS INCIDENTS:")
            for a in analysis.analogous_incidents:
                print(f"    [{a.company}, {a.year}] {a.lesson}")
        print(f"\n  ANALYST NOTE:")
        print(f"    {analysis.analyst_note}")
        print("\n" + "=" * 60)

    print("Step 3 analyzer working.")