TEST_INCIDENTS = [
    {
        "id": "INC-001",
        "label": "Port congestion — Long Beach",
        "text": (
            "Our primary freight forwarder has reported severe congestion at the Port of Long Beach. "
            "Current wait times for container unloading are 9–12 days, up from the normal 2–3 days. "
            "Approximately 1,200 containers of electronics components (PCBs, memory chips, display modules) "
            "are affected. Shipments were due to arrive at our Memphis distribution center by November 15. "
            "The congestion is being attributed to a labor dispute among dock workers and a simultaneous "
            "surge in pre-holiday imports. Three of our tier-1 suppliers — TechComp Taiwan, SemiconductorCo, "
            "and DisplayTech — all route through this port."
        ),
    },
    {
        "id": "INC-002",
        "label": "Supplier bankruptcy — FastenersCo",
        "text": (
            "We have received notification that FastenersCo, a tier-1 supplier of industrial fasteners "
            "and bolts (representing ~18% of our total fastener spend), filed for Chapter 11 bankruptcy "
            "protection this morning. Their two manufacturing facilities in Ohio and Michigan have halted "
            "production as of today. We have approximately 6 weeks of inventory on hand. "
            "FastenersCo supplies 47 unique SKUs critical to our automotive assembly line. "
            "Annual spend with this supplier was $4.2M. No prior warning was given."
        ),
    },
    {
        "id": "INC-003",
        "label": "Tariff escalation — Chinese electronics",
        "text": (
            "The US Trade Representative has announced a new 35% tariff on electronic subassemblies "
            "imported from China, effective in 30 days. This affects approximately 60% of our "
            "component sourcing by volume. Key affected categories: power supply units, motor controllers, "
            "and sensor modules. Current annualized import value subject to the new tariff is $12.8M. "
            "Our current contracts with Chinese suppliers run through Q2 next year with no tariff "
            "adjustment clauses. The new tariff applies on top of the existing 7.5% Section 301 tariffs."
        ),
    },
    {
        "id": "INC-004",
        "label": "Weather disruption — hurricane",
        "text": (
            "Hurricane Helene has made landfall near Charleston, South Carolina. Our third-party "
            "logistics provider, Coastal 3PL, operates a major regional distribution hub in Charleston "
            "that handles fulfillment for our Southeast US customers. The facility has been evacuated "
            "and is expected to be offline for 7–14 days minimum. The hub currently holds $3.1M worth "
            "of finished goods inventory. Power restoration timelines are unknown. "
            "Approximately 2,400 open customer orders totaling $890K are at risk of delay. "
            "Alternate fulfillment capacity is available at our Atlanta hub but is currently operating "
            "at 87% capacity."
        ),
    },
    {
        "id": "INC-005",
        "label": "Quality recall — contaminated raw materials",
        "text": (
            "Our QA team has identified a contamination issue in a batch of pharmaceutical-grade "
            "polyethylene resin received from ChemSupply GmbH (Germany). Lot numbers AX-2291 through "
            "AX-2308 are affected. The contamination is a phthalate compound exceeding FDA limits by "
            "approximately 3x. These lots have already been used in production of 14,000 units of "
            "our medical device product line (SKUs MD-400 through MD-412). "
            "Approximately 6,200 units have already shipped to healthcare distributors. "
            "We are legally required to initiate a recall. ChemSupply has not yet responded to our "
            "communications. No replacement resin inventory is on hand."
        ),
    },
    {
        "id": "INC-006",
        "label": "Sole-source supplier fire",
        "text": (
            "A fire broke out at the manufacturing facility of PrecisionMolds Ltd in Guadalajara, Mexico, "
            "last night. PrecisionMolds is our sole-source supplier for a custom injection-molded housing "
            "component (Part #PM-7741) used in our flagship product. The fire destroyed the tooling "
            "and approximately 40% of the production floor. No injuries reported. "
            "Our current inventory of PM-7741 is 1,100 units — approximately 11 days of production "
            "at current run rates. PrecisionMolds estimates 12–16 weeks to rebuild tooling and "
            "resume production. No second source for this component exists. "
            "Lead time to qualify a new supplier from scratch is estimated at 6–9 months."
        ),
    },
    {
        "id": "INC-007",
        "label": "Geopolitical — Red Sea shipping disruption",
        "text": (
            "Ongoing Houthi attacks in the Red Sea have forced our primary ocean freight carrier "
            "Maersk to reroute all Asia-to-Europe shipments around the Cape of Good Hope, adding "
            "10–14 days to transit times and increasing freight rates by approximately 180% vs Q3 rates. "
            "We have 23 active shipments currently at sea on Asia-Europe lanes. "
            "8 of these are carrying time-sensitive materials for our German manufacturing plant "
            "with hard assembly deadlines. Total value of in-transit goods affected: $7.4M. "
            "Our freight budget for Q1 will be exceeded by an estimated $1.1M if rerouting continues."
        ),
    },
    {
        "id": "INC-008",
        "label": "IT/ERP cyberattack at supplier",
        "text": (
            "Our tier-1 electronics supplier, TechParts Co, notified us this morning that they "
            "suffered a ransomware attack on their ERP and order management systems 48 hours ago. "
            "Their production planning, inventory visibility, and order processing systems are all offline. "
            "They cannot confirm status of our 12 open purchase orders totaling $2.3M. "
            "It is unclear whether our own data (pricing, contracts, engineering specs shared via "
            "their supplier portal) has been compromised. TechParts' recovery timeline is unknown. "
            "They are our only qualified supplier for RF antenna modules (Part #RF-112), "
            "with 22 days of inventory remaining."
        ),
    },
]

if __name__ == "__main__":
    print(f"Loaded {len(TEST_INCIDENTS)} test incidents\n")
    for inc in TEST_INCIDENTS:
        print(f"  {inc['id']} — {inc['label']}"
)