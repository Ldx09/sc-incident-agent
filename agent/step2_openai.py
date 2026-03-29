import json
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pydantic import BaseModel
from utils.helpers_openai import call_model_with_search
from agent.step1_openai import ParsedIncident


RESEARCHER_SYSTEM_PROMPT = """
You are a supply chain intelligence analyst. You have been given a parsed
supply chain incident report and must gather context to support a full
root cause analysis.

Your job is to draw on everything you know about this incident type,
the companies involved, the regions affected, and similar historical events
to compile a structured research brief.

Return a single valid JSON object — nothing else.
No explanation, no markdown, no code fences. Raw JSON only.

The JSON must contain these fields:

- searches_performed: list of the exact search queries you would have run
  if you had live web access (be specific and realistic)

- current_situation: 2-3 sentences on the current state of this type of
  incident based on your knowledge — recent trends, known status

- historical_precedents: list of 2-3 similar real past incidents with what
  happened and how long they lasted. Be specific about companies and years.
  Each item must be a plain string, not an object.

- market_context: relevant market conditions, pricing trends, or industry
  factors that make this incident better or worse than it appears

- alternative_suppliers_or_routes: list of specific real alternatives —
  actual company names, ports, or routes that could substitute.
  Each entry must be an object with "name" and "notes" fields.

- regulatory_or_legal_context: any relevant regulations, trade rules,
  compliance requirements, or legal obligations triggered by this incident.
  Empty string if none.

- risk_amplifiers: list of factors that make this incident MORE serious
  than the raw report suggests

- risk_mitigators: list of factors that make this incident LESS serious
  or easier to manage

- confidence_level: one of [high, medium, low] — how confident you are
  in your analysis given available knowledge

- research_gaps: list of things that would require live data to verify —
  information gaps that matter for a full response
""".strip()


class AlternativeOption(BaseModel):
    name: str
    notes: str


class EnrichedContext(BaseModel):
    searches_performed: list[str]
    current_situation: str
    historical_precedents: list[str]
    market_context: str
    alternative_suppliers_or_routes: list[AlternativeOption]
    regulatory_or_legal_context: str
    risk_amplifiers: list[str]
    risk_mitigators: list[str]
    confidence_level: str
    research_gaps: list[str]


def research_incident(parsed: ParsedIncident) -> EnrichedContext:
    """
    Step 2: Take a ParsedIncident, return an EnrichedContext object.
    """
    incident_summary = f"""
Incident type: {parsed.incident_type}
Title: {parsed.title}
Affected region: {parsed.affected_region}
Affected suppliers: {', '.join(parsed.affected_suppliers) or 'Not specified'}
Affected products: {', '.join(parsed.affected_products) or 'Not specified'}
Severity: {parsed.severity}/5
Time sensitivity: {parsed.time_sensitivity}
Estimated financial impact: {parsed.estimated_financial_impact}

Key facts:
{chr(10).join(f'- {f}' for f in parsed.key_facts)}

Missing information we need:
{chr(10).join(f'- {m}' for m in parsed.missing_information)}
""".strip()

    raw, searches = call_model_with_search(
        system_prompt=RESEARCHER_SYSTEM_PROMPT,
        user_message=(
            "Research this supply chain incident and return your findings as JSON:\n\n"
            f"{incident_summary}"
        ),
        max_tokens=4096
    )

    print(f"    Research complete: {len(searches)} source(s) consulted")

    clean = raw
    if clean.startswith("```"):
        clean = clean.split("\n", 1)[-1]
        clean = clean.rsplit("```", 1)[0]
    clean = clean.strip()

    try:
        data = json.loads(clean)
    except json.JSONDecodeError as e:
        raise ValueError(f"Model returned invalid JSON: {e}\nRaw:\n{clean}")

    if "historical_precedents" in data:
        normalized_hp = []
        for item in data["historical_precedents"]:
            if isinstance(item, str):
                normalized_hp.append(item)
            elif isinstance(item, dict):
                parts = []
                for key in ["incident", "company", "event", "description",
                            "summary", "lesson", "impact", "duration", "year"]:
                    if key in item:
                        parts.append(str(item[key]))
                normalized_hp.append(" — ".join(parts) if parts else str(item))
        data["historical_precedents"] = normalized_hp

    if "alternative_suppliers_or_routes" in data:
        normalized = []
        for item in data["alternative_suppliers_or_routes"]:
            if isinstance(item, str):
                normalized.append({"name": item, "notes": ""})
            elif isinstance(item, dict):
                normalized.append({
                    "name": item.get("name", item.get("option", str(item))),
                    "notes": item.get("notes", item.get("description", ""))
                })
        data["alternative_suppliers_or_routes"] = normalized

    context = EnrichedContext(**data)
    return context


if __name__ == "__main__":
    from agent.step1_openai import parse_incident
    from tests.test_incidents import TEST_INCIDENTS

    test_cases = [
        TEST_INCIDENTS[0],
        TEST_INCIDENTS[2],
        TEST_INCIDENTS[6],
    ]

    print("=" * 60)
    print("STEP 2 — CONTEXT RESEARCHER TEST")
    print("=" * 60)

    for incident in test_cases:
        print(f"\nTesting: {incident['id']} — {incident['label']}")
        print("  [Step 1] Parsing...")
        parsed = parse_incident(incident["text"])
        print(f"  Parsed: {parsed.incident_type} | severity {parsed.severity}/5")

        print("  [Step 2] Researching...")
        context = research_incident(parsed)

        print(f"\n  Confidence:    {context.confidence_level}")
        print(f"\n  Current situation:")
        print(f"    {context.current_situation}")
        print(f"\n  Market context:")
        print(f"    {context.market_context}")
        print(f"\n  Alternatives found:")
        for alt in context.alternative_suppliers_or_routes:
            print(f"    • {alt.name}: {alt.notes}")
        print(f"\n  Risk amplifiers:")
        for r in context.risk_amplifiers:
            print(f"    + {r}")
        print(f"\n  Risk mitigators:")
        for r in context.risk_mitigators:
            print(f"    - {r}")
        print(f"\n  Research gaps:")
        for g in context.research_gaps:
            print(f"    ? {g}")
        print("\n" + "-" * 60)

    print("\nStep 2 researcher working.")