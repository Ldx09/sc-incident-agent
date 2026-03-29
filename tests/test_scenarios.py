"""
SC Incident Response Agent — Test Scenarios
============================================
8 realistic supply chain incidents covering every incident type.
Use these to demo the full pipeline, test new features, or populate
the dashboard and playbook generator with rich data.

How to use:
    1. Run the app: python -m streamlit run app.py
    2. Copy any scenario text below and paste into the incident report field
    3. Or run the pipeline directly: python tests/test_scenarios.py

Each scenario includes:
    - The incident text (paste into the app)
    - Suggested audit trail actions (fill in after analysis)
    - What features it tests
"""

TEST_SCENARIOS = [
    {
        "id": "SCN-001",
        "label": "Red Sea shipping crisis — geopolitical",
        "incident_type": "geopolitical",
        "tests": [
            "Geopolitical incident type",
            "Multi-supplier watchlist matching",
            "High financial exposure calculation",
            "Alternative routing options",
        ],
        "text": (
            "Our primary ocean freight carrier Maersk has announced immediate suspension "
            "of all Asia-to-Europe sailings through the Red Sea and Suez Canal effective "
            "this week due to escalating Houthi missile attacks on commercial vessels. "
            "All shipments are being rerouted around the Cape of Good Hope, adding "
            "12-16 days to transit times. We have 18 active shipments currently at sea "
            "valued at $6.8M total. Eight of these carry time-critical components for our "
            "German manufacturing plant with hard assembly line deadlines in 3 weeks. "
            "Freight rates have surged 280% above Q3 baseline. Our freight budget for Q1 "
            "will be exceeded by an estimated $1.4M if rerouting continues through March. "
            "Three alternative carriers — MSC, CMA CGM, and Hapag-Lloyd — are also "
            "rerouting. No carrier is currently transiting the Red Sea."
        ),
        "suggested_audit": {
            "actions_taken": [1, 2],
            "outcomes": {1: "ongoing", 2: "partially_resolved"},
            "overall": "ongoing",
            "resolution_time": "6-8 weeks",
            "lessons": "No freight rate hedging instruments were in place",
        },
    },
    {
        "id": "SCN-002",
        "label": "Ransomware attack on ERP supplier — cyberattack",
        "incident_type": "cyberattack",
        "tests": [
            "Cyberattack incident type",
            "Data breach / IP exposure angle",
            "Sole-source dependency",
            "Unknown recovery timeline handling",
        ],
        "text": (
            "TechParts Co, our sole-qualified supplier for RF antenna modules (Part #RF-112), "
            "notified us this morning that they suffered a ransomware attack on their "
            "production planning and ERP systems 36 hours ago. Their manufacturing floor "
            "is offline. All order management, inventory visibility, and shipping systems "
            "are non-functional. We have 12 open purchase orders with TechParts totaling "
            "$2.1M that we cannot confirm status on. Our engineering specs, pricing data, "
            "and 3-year contract terms were stored in their supplier portal and may have "
            "been compromised. We currently have 19 days of RF-112 inventory remaining. "
            "TechParts has not communicated a recovery timeline. Their CEO called "
            "personally to apologize but could not provide an ETA. We are their second "
            "largest customer. No second-source supplier for RF-112 exists — qualification "
            "process takes 4-6 months minimum."
        ),
        "suggested_audit": {
            "actions_taken": [1, 2, 3],
            "outcomes": {1: "ongoing", 2: "ongoing", 3: "resolved"},
            "overall": "escalated",
            "resolution_time": "Unknown",
            "lessons": "Supplier cybersecurity posture was never assessed during qualification",
        },
    },
    {
        "id": "SCN-003",
        "label": "Taiwan earthquake — semiconductor shortage",
        "incident_type": "geopolitical",
        "tests": [
            "Geographic concentration vulnerability",
            "Long recovery timeline",
            "Multi-product-line impact",
            "Spot market pricing surge",
        ],
        "text": (
            "Our semiconductor distributor AVNET has issued a force majeure notice "
            "covering all orders for STM32 microcontrollers and Texas Instruments "
            "TMS320 DSP chips through Q2. A 7.4 magnitude earthquake near Hsinchu "
            "Science Park in Taiwan damaged cleanroom facilities at two major fabs. "
            "TSMC has confirmed production will be reduced by approximately 30% for "
            "minimum 8 weeks while structural assessments and repairs are completed. "
            "These components are used in 6 of our 9 product lines. Current on-hand "
            "inventory covers 5 weeks of production at normal run rates. We source "
            "100% of these chips from Taiwan-based manufacturers with no approved "
            "alternative sources in our AVL. Spot market pricing has already increased "
            "340% above contracted rates. Competitors are reportedly placing emergency "
            "orders to secure available inventory."
        ),
        "suggested_audit": {
            "actions_taken": [1, 3],
            "outcomes": {1: "partially_resolved", 3: "ongoing"},
            "overall": "ongoing",
            "resolution_time": "4-5 months",
            "lessons": "Geographic concentration in Taiwan was known risk but never formally mitigated",
        },
    },
    {
        "id": "SCN-004",
        "label": "East Coast port strike — ILA walkout",
        "incident_type": "port_disruption",
        "tests": [
            "Port disruption type (East Coast vs West Coast)",
            "Comparison with existing port disruption playbook",
            "Retail deadline pressure",
            "Government intervention precedent",
        ],
        "text": (
            "The International Longshoremen's Association has called a strike at all "
            "36 East Coast and Gulf Coast ports effective midnight tonight after "
            "contract negotiations with the United States Maritime Alliance collapsed. "
            "This is the first full East Coast port strike since 1977. Approximately "
            "$3.8B of goods move through these ports daily. We have 340 containers "
            "currently at sea destined for East Coast ports carrying finished goods "
            "inventory for our Q4 holiday season. Estimated value: $4.2M. If the "
            "strike lasts more than 5 days, we will miss our retail distribution "
            "windows entirely. Our West Coast distribution center in Los Angeles has "
            "limited capacity — currently at 91% utilization. All our key retailers "
            "have force majeure clauses that allow order cancellation after a 14-day "
            "delay. Historically, East Coast port strikes resolve within 5-10 days "
            "under government intervention."
        ),
        "suggested_audit": {
            "actions_taken": [1, 2, 4],
            "outcomes": {1: "resolved", 2: "ongoing", 4: "partially_resolved"},
            "overall": "resolved",
            "resolution_time": "8 days",
            "lessons": "West Coast overflow capacity needs to be pre-contracted, not reactive",
        },
    },
    {
        "id": "SCN-005",
        "label": "FDA recall — contaminated packaging",
        "incident_type": "quality_recall",
        "tests": [
            "Quality recall type",
            "Regulatory / legal obligation handling",
            "Reputational risk scoring",
            "24-hour FDA notification deadline",
        ],
        "text": (
            "Our quality team has identified a contamination issue in lot numbers "
            "PKG-4401 through PKG-4488 of medical-grade polyethylene packaging film "
            "received from ChemPack Solutions. Lab testing confirms phthalate "
            "contamination at 4.2x the FDA limit for food-contact materials. These "
            "lots were used to package 22,000 units of our nutritional supplement "
            "product line (SKUs NS-100 through NS-118) over the past 6 weeks. "
            "Approximately 14,500 units have already shipped to distributors across "
            "38 states. FDA notification is legally required within 24 hours of "
            "confirmed contamination finding. We have 3 class action attorneys "
            "who have already contacted our legal team after social media reports. "
            "ChemPack Solutions is not responding to our emergency calls. This "
            "product line represents 23% of our annual revenue. No replacement "
            "packaging inventory is on hand from an alternate supplier."
        ),
        "suggested_audit": {
            "actions_taken": [1, 2, 3, 4, 5],
            "outcomes": {
                1: "resolved",
                2: "ongoing",
                3: "escalated",
                4: "ongoing",
                5: "resolved",
            },
            "overall": "escalated",
            "resolution_time": "3 months",
            "lessons": "No incoming QC testing for packaging materials — only product testing",
        },
    },
    {
        "id": "SCN-006",
        "label": "Supplier acquired by competitor — strategic risk",
        "incident_type": "other",
        "tests": [
            "Other incident type",
            "No single supplier at fault",
            "Contract vulnerability / no change-of-control clause",
            "Proprietary tooling recovery",
        ],
        "text": (
            "We received notice this morning that MoldTech Precision, our primary "
            "injection molding partner responsible for 34% of our custom tooled "
            "components, has been acquired by Nexus Industrial — our direct "
            "competitor in the commercial HVAC market. The acquisition closed "
            "yesterday. MoldTech holds proprietary tooling for 23 of our part "
            "numbers, all physically located at their Monterrey, Mexico facility. "
            "Our current contract with MoldTech runs through December and contains "
            "no change-of-control clause — legal has confirmed the acquiring party "
            "is not obligated to honor the existing terms. We have 8 weeks of "
            "inventory for the most critical MoldTech-produced components. Nexus "
            "Industrial's CEO was quoted today saying they plan to vertically "
            "integrate MoldTech's capabilities. Annual spend with MoldTech was "
            "$3.1M. Recovering our tooling would require MoldTech's cooperation "
            "and could take 4-6 weeks even in a best-case scenario."
        ),
        "suggested_audit": {
            "actions_taken": [1, 2],
            "outcomes": {1: "ongoing", 2: "resolved"},
            "overall": "escalated",
            "resolution_time": "5 months",
            "lessons": "No change-of-control clauses in any supplier contracts — immediate legal review needed",
        },
    },
    {
        "id": "SCN-007",
        "label": "Freight forwarder insolvency — Chapter 7",
        "incident_type": "supplier_bankruptcy",
        "tests": [
            "Supplier bankruptcy type (logistics angle)",
            "In-transit goods at risk",
            "Prepaid credit recovery",
            "No backup forwarder established",
        ],
        "text": (
            "Our primary freight forwarder GlobalFreight Partners filed for Chapter 7 "
            "liquidation in Delaware federal court this morning with no prior warning. "
            "GlobalFreight handles 60% of our international freight bookings and "
            "currently has 47 of our shipments in transit across 12 countries — "
            "total goods value $8.3M. We have no visibility into whether these "
            "shipments are pre-paid or whether carriers will release them without "
            "additional payment. GlobalFreight holds $340,000 of our prepaid freight "
            "credits that are now frozen. Their website and phone systems are offline. "
            "Our logistics team is attempting to contact individual carriers directly "
            "but does not have master service agreements with any of them. Our peak "
            "shipping season begins in 6 weeks. We have no secondary freight forwarder "
            "with established relationships and credit lines currently approved."
        ),
        "suggested_audit": {
            "actions_taken": [1, 2, 3],
            "outcomes": {
                1: "partially_resolved",
                2: "ongoing",
                3: "resolved",
            },
            "overall": "ongoing",
            "resolution_time": "4 weeks",
            "lessons": "Single forwarder dependency with no backup — same structural risk as single-source suppliers",
        },
    },
    {
        "id": "SCN-008",
        "label": "Section 232 steel tariffs — raw material price spike",
        "incident_type": "tariff_change",
        "tests": [
            "Tariff change type (raw material vs finished goods)",
            "Multiple service centers affected simultaneously",
            "Margin compression calculation",
            "Customer contract escalation clause timing",
        ],
        "text": (
            "Hot-rolled steel coil prices have surged 67% in the past 30 days following "
            "the US government's announcement of 25% Section 232 tariffs on all steel "
            "imports from Canada, Mexico, and the EU effective immediately. Our "
            "three primary steel service centers — Metals USA, Service Center Inc, "
            "and Steel Technologies — have all issued price adjustment notices "
            "canceling previously agreed Q2 pricing and moving to weekly spot pricing. "
            "Steel represents approximately 31% of our total COGS for our structural "
            "product lines. At current spot prices, our gross margin on the affected "
            "product lines drops from 38% to approximately 19%. We have 6 weeks of "
            "steel inventory at the old pricing. Our customer contracts contain "
            "material cost escalation clauses but require 60 days notice — we cannot "
            "pass costs through in time for Q2. Estimated annualized EBITDA impact: "
            "$2.8M if current pricing holds."
        ),
        "suggested_audit": {
            "actions_taken": [1, 2, 3, 4],
            "outcomes": {
                1: "ongoing",
                2: "resolved",
                3: "partially_resolved",
                4: "ongoing",
            },
            "overall": "ongoing",
            "resolution_time": "Ongoing — market dependent",
            "lessons": "No hedging strategy or forward purchasing contracts for key commodities",
        },
    },
]


def print_scenario(scenario: dict):
    print(f"\n{'=' * 65}")
    print(f"{scenario['id']} — {scenario['label']}")
    print(f"{'=' * 65}")
    print(f"Type: {scenario['incident_type']}")
    print(f"Tests: {', '.join(scenario['tests'])}")
    print(f"\nIncident text:\n")
    print(scenario["text"])
    print(f"\nSuggested audit trail:")
    audit = scenario["suggested_audit"]
    print(f"  Actions to mark taken: {audit['actions_taken']}")
    for action_num, outcome in audit["outcomes"].items():
        print(f"  Action {action_num} outcome: {outcome}")
    print(f"  Overall outcome: {audit['overall']}")
    print(f"  Resolution time: {audit['resolution_time']}")
    print(f"  Lessons learned: {audit['lessons']}")


def run_all_via_pipeline():
    """
    Run all 8 scenarios through the pipeline directly (no UI).
    Useful for bulk testing or populating the database.
    """
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    from agent.pipeline import run_pipeline
    from utils.database import save_incident
    from utils.audit import save_audit

    print("Running all 8 test scenarios through the pipeline...\n")

    for scenario in TEST_SCENARIOS:
        print(f"Processing {scenario['id']} — {scenario['label']}...")
        try:
            result = run_pipeline(scenario["text"])
            save_incident(result)

            audit = scenario["suggested_audit"]
            actions = []
            for action in result.brief.immediate_actions:
                was_taken = action.priority in audit["actions_taken"]
                outcome = audit["outcomes"].get(action.priority, "not_recorded")
                actions.append({
                    "priority": action.priority,
                    "action":   action.action,
                    "owner":    action.owner,
                    "deadline": action.deadline,
                    "was_taken": was_taken,
                    "outcome":  outcome if was_taken else "not_recorded",
                    "notes":    "",
                })

            save_audit(
                incident_id=result.brief.incident_id,
                actions=actions,
                overall_outcome=audit["overall"],
                resolution_time=audit["resolution_time"],
                lessons_learned=audit["lessons"],
            )

            print(f"  DONE — {result.brief.incident_id} | "
                  f"{result.brief.severity_level} | "
                  f"{result.analysis.vulnerability_type}")

        except Exception as e:
            print(f"  FAILED — {e}")

    print("\nAll scenarios complete. Check the dashboard and playbooks page.")


if __name__ == "__main__":
    import sys

    if "--run" in sys.argv:
        run_all_via_pipeline()
    else:
        print("SC Incident Response Agent — Test Scenarios")
        print(f"8 scenarios covering {len(set(s['incident_type'] for s in TEST_SCENARIOS))} incident types\n")
        for s in TEST_SCENARIOS:
            print(f"  {s['id']} — {s['label']}")
        print("\nOptions:")
        print("  python tests/test_scenarios.py          — list all scenarios")
        print("  python tests/test_scenarios.py --run    — run all through pipeline")
        print("\nOr copy any scenario text above into the Streamlit app.")