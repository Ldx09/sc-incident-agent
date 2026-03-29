# SC Incident Response Agent

An AI-powered supply chain incident response tool that transforms raw incident reports into structured, actionable briefs for operations teams. Built as a portfolio project demonstrating AI product management, multi-step agent pipelines, and supply chain domain expertise.

**Live demo:** [Add your Streamlit URL here after deployment]

---

## What it does

Paste any supply chain incident report — port congestion, supplier bankruptcy, tariff escalation, quality recall, cyberattack — and the agent runs a 4-step AI pipeline to generate a complete incident brief in under 60 seconds.

### The 4-step pipeline

```
Raw incident text
       ↓
[Step 1] Incident Parser        — extracts structured fields, severity score, affected suppliers
       ↓
[Step 2] Context Researcher     — reasons from industry knowledge, surfaces historical precedents
       ↓
[Step 3] Root Cause Analyzer    — identifies systemic vulnerabilities, builds impact chain
       ↓
[Step 4] Brief Generator        — produces executive summary, ranked actions, stakeholder email
       ↓
Complete incident brief (+ PDF export)
```

### Output includes

- Executive summary (3 sentences, C-suite ready)
- Risk scores: Overall, Operational, Financial, Reputational (1–10)
- Financial exposure range with confidence level
- 5 immediate actions — priority ranked with owner and deadline
- Root cause analysis with impact chain (domino effect visualization)
- Alternative suppliers or routes
- Ready-to-send stakeholder email
- 72-hour monitoring plan with escalation triggers
- PDF export

---

## Features

### Core agent
- 4-step AI pipeline using OpenAI `gpt-4o-mini`
- Structured JSON output with Pydantic validation
- Input validation and error handling with user-friendly messages
- Auto-retry on rate limits

### Incident history dashboard
- Every analysis auto-saved to SQLite
- Severity breakdown, vulnerability type distribution, incident type charts
- Risk score trend over time
- Financial exposure per incident (stacked bar)
- Filterable incident table with full detail view
- Built with Chart.js via Streamlit components

### Supplier risk watchlist
- Add suppliers to track across incidents
- Fuzzy name matching — catches `FastenersCo` and `Fasteners CO.` as the same supplier
- Risk score accumulates automatically (CRITICAL = 4pts, HIGH = 3pts, etc.)
- Incident history chart per supplier
- High-risk alert section for suppliers scoring 7+

### Decision audit trail
- After each analysis, mark which immediate actions were taken
- Record outcome per action: Resolved / Partially resolved / Escalated / Ongoing / Skipped
- Track overall incident outcome and resolution time
- Lessons learned field
- Dashboard shows: follow-through rate, outcome distribution, action take-rate by priority

### Playbook generator
- Synthesizes all past incidents of the same type into a reusable SOP
- Sections: Early warning signals, First 24h actions, Root causes, What worked, What failed, Key contacts, Success metrics, Prevention recommendations
- Improves automatically as more incidents are analyzed
- Incorporates audit trail data into "what worked / what failed" sections
- PDF export of each playbook

---

## Tech stack

| Layer | Technology |
|---|---|
| AI model | OpenAI `gpt-4o-mini` |
| Frontend | Streamlit |
| Backend | Python — pipeline orchestrator |
| Data models | Pydantic v2 |
| Database | SQLite |
| Charts | Chart.js (via Streamlit components) |
| PDF export | fpdf2 |
| Deployment | Streamlit Cloud |

---

## Project structure

```
sc-incident-agent/
├── agent/
│   ├── pipeline.py          # orchestrator — chains all 4 steps
│   ├── step1_openai.py      # incident parser + Pydantic model
│   ├── step2_openai.py      # context researcher
│   ├── step3_openai.py      # root cause analyzer
│   └── step4_openai.py      # brief generator
├── pages/
│   ├── 1_Dashboard.py       # incident history dashboard
│   ├── 2_Watchlist.py       # supplier risk watchlist
│   └── 3_Playbooks.py       # playbook generator
├── utils/
│   ├── helpers_openai.py    # OpenAI client + call_model helpers
│   ├── database.py          # SQLite — incident storage
│   ├── watchlist.py         # SQLite — watchlist + risk scoring
│   ├── audit.py             # SQLite — decision audit trail
│   └── playbook.py          # playbook generation + storage
├── tests/
│   ├── test_incidents.py    # 8 built-in test incidents (Phase 1)
│   └── test_scenarios.py    # 8 advanced scenarios with audit data
├── app.py                   # main Streamlit app
├── requirements.txt
└── README.md
```

---

## Test scenarios

The repo includes 8 production-grade test scenarios in `tests/test_scenarios.py` covering all incident types:

| ID | Scenario | Type |
|---|---|---|
| SCN-001 | Red Sea shipping crisis | Geopolitical |
| SCN-002 | Ransomware attack on ERP supplier | Cyberattack |
| SCN-003 | Taiwan earthquake — semiconductor shortage | Geopolitical |
| SCN-004 | East Coast port strike — ILA walkout | Port disruption |
| SCN-005 | FDA recall — contaminated packaging | Quality recall |
| SCN-006 | Supplier acquired by competitor | Other |
| SCN-007 | Freight forwarder insolvency | Supplier bankruptcy |
| SCN-008 | Section 232 steel tariffs | Tariff change |

**List all scenarios:**
```bash
python tests/test_scenarios.py
```

**Run all 8 through the pipeline and auto-populate the database:**
```bash
python tests/test_scenarios.py --run
```

---

## PM design decisions

A few intentional product decisions worth noting for interviews:

**Why session state for results?** Streamlit reruns the entire script on every widget interaction. Storing the pipeline result in `st.session_state` means the audit trail widgets stay interactive without re-running the expensive AI pipeline.

**Why fuzzy supplier matching?** Real-world supplier data is messy — `FastenersCo`, `Fasteners Co.`, and `FASTENERSCO` are the same company. Normalizing by stripping spaces, dots, and case before matching makes the watchlist actually useful.

**Why SQLite over a hosted DB?** For an MVP and portfolio project, SQLite gives zero-config persistence with full SQL capability. The abstraction layer in `utils/database.py` makes swapping to Postgres or Supabase a one-file change.

**Why playbooks pull audit data?** A playbook generated from incident reports alone tells you what happened. A playbook that incorporates audit data tells you what worked — which is operationally more valuable. Audit data makes the "what worked / what failed" sections grounded in your team's actual decisions, not AI reasoning.

---

---

## Author

Built by Vrajesh Shahas a portfolio project demonstrating AI product management and supply chain operations expertise.

- LinkedIn: https://www.linkedin.com/in/vrajesh-shah/
- GitHub: https://github.com/Ldx09
