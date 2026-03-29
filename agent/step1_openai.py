import json
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pydantic import BaseModel, Field
from typing import Literal
from utils.helpers_openai import call_model


PARSER_SYSTEM_PROMPT = """
You are a supply chain incident analyst. Your job is to read raw incident
reports and extract structured data from them with precision.

You will always respond with a single valid JSON object — nothing else.
No explanation, no markdown, no code fences. Just the raw JSON.

Extract the following fields:

- incident_type: one of [port_disruption, supplier_bankruptcy, tariff_change,
  weather_event, quality_recall, facility_damage, geopolitical, cyberattack, other]

- title: a short 8-10 word title summarizing the incident

- affected_suppliers: list of supplier or company names mentioned

- affected_products: list of product names, part numbers, or SKUs mentioned
  (empty list if none specified)

- affected_region: the primary geographic location or region affected

- severity: integer 1-5 where:
  1 = minor inconvenience, easily absorbed
  2 = moderate, requires monitoring
  3 = significant, requires active response
  4 = major, threatens production or revenue
  5 = critical, existential threat to operations

- severity_reasoning: one sentence explaining why you chose that severity score

- estimated_financial_impact: your best estimate of financial impact in USD
  (e.g. "$2.3M in delayed orders"). Write "Unknown" if not determinable.

- time_sensitivity: one of [immediate, within_48h, within_week, within_month]
  based on how urgently a response is needed

- key_facts: list of 3-5 bullet-point facts — the most important numbers,
  dates, and specifics from the incident report

- missing_information: list of important questions that are unanswered in the
  report but would be critical to know for a full response
""".strip()


class ParsedIncident(BaseModel):
    incident_type: Literal[
        "port_disruption", "supplier_bankruptcy", "tariff_change",
        "weather_event", "quality_recall", "facility_damage",
        "geopolitical", "cyberattack", "other"
    ]
    title: str
    affected_suppliers: list[str]
    affected_products: list[str]
    affected_region: str
    severity: int = Field(ge=1, le=5)
    severity_reasoning: str
    estimated_financial_impact: str
    time_sensitivity: Literal[
        "immediate", "within_48h", "within_week", "within_month"
    ]
    key_facts: list[str]
    missing_information: list[str]


def parse_incident(incident_text: str) -> ParsedIncident:
    """
    Step 1: Take raw incident text, return a validated ParsedIncident object.
    """
    raw_json = call_model(
        system_prompt=PARSER_SYSTEM_PROMPT,
        user_message=f"Parse this supply chain incident report:\n\n{incident_text}",
        max_tokens=1024
    )

    clean = raw_json
    if clean.startswith("```"):
        clean = clean.split("\n", 1)[-1]
        clean = clean.rsplit("```", 1)[0]
    clean = clean.strip()

    try:
        data = json.loads(clean)
    except json.JSONDecodeError as e:
        raise ValueError(f"Model returned invalid JSON: {e}\nRaw output:\n{clean}")

    parsed = ParsedIncident(**data)
    return parsed


if __name__ == "__main__":
    from tests.test_incidents import TEST_INCIDENTS

    print("=" * 60)
    print("STEP 1 — INCIDENT PARSER TEST")
    print("=" * 60)

    for incident in TEST_INCIDENTS[:3]:
        print(f"\nTesting: {incident['id']} — {incident['label']}")
        print("-" * 40)

        result = parse_incident(incident["text"])

        print(f"  Type:       {result.incident_type}")
        print(f"  Title:      {result.title}")
        print(f"  Severity:   {result.severity}/5 — {result.severity_reasoning}")
        print(f"  Region:     {result.affected_region}")
        print(f"  Urgency:    {result.time_sensitivity}")
        print(f"  $ Impact:   {result.estimated_financial_impact}")
        print(f"  Suppliers:  {', '.join(result.affected_suppliers) or 'None listed'}")
        print(f"  Key facts:")
        for fact in result.key_facts:
            print(f"    • {fact}")
        print(f"  Missing info:")
        for gap in result.missing_information:
            print(f"    ? {gap}")

    print("\n" + "=" * 60)
    print("Step 1 parser working.")
    print("=" * 60)