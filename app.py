import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
from fpdf import FPDF
from agent.pipeline import run_pipeline, PipelineResult, PipelineStepError


st.set_page_config(
    page_title="SC Incident Response Agent",
    page_icon="🚨",
    layout="wide"
)

EXAMPLES = {
    "Port congestion — Long Beach": (
        "Our primary freight forwarder has reported severe congestion at the Port of Long Beach. "
        "Current wait times for container unloading are 9–12 days, up from the normal 2–3 days. "
        "Approximately 1,200 containers of electronics components (PCBs, memory chips, display modules) "
        "are affected. Shipments were due to arrive at our Memphis distribution center by November 15. "
        "The congestion is being attributed to a labor dispute among dock workers and a simultaneous "
        "surge in pre-holiday imports. Three of our tier-1 suppliers — TechComp Taiwan, SemiconductorCo, "
        "and DisplayTech — all route through this port."
    ),
    "Supplier bankruptcy — FastenersCo": (
        "We have received notification that FastenersCo, a tier-1 supplier of industrial fasteners "
        "and bolts (representing ~18% of our total fastener spend), filed for Chapter 11 bankruptcy "
        "protection this morning. Their two manufacturing facilities in Ohio and Michigan have halted "
        "production as of today. We have approximately 6 weeks of inventory on hand. "
        "FastenersCo supplies 47 unique SKUs critical to our automotive assembly line. "
        "Annual spend with this supplier was $4.2M. No prior warning was given."
    ),
    "Sole-source supplier fire": (
        "A fire broke out at the manufacturing facility of PrecisionMolds Ltd in Guadalajara, Mexico, "
        "last night. PrecisionMolds is our sole-source supplier for a custom injection-molded housing "
        "component (Part #PM-7741) used in our flagship product. The fire destroyed the tooling "
        "and approximately 40% of the production floor. No injuries reported. "
        "Our current inventory of PM-7741 is 1,100 units — approximately 11 days of production "
        "at current run rates. PrecisionMolds estimates 12–16 weeks to rebuild tooling and "
        "resume production. No second source for this component exists."
    ),
    "Tariff escalation — Chinese electronics": (
        "The US Trade Representative has announced a new 35% tariff on electronic subassemblies "
        "imported from China, effective in 30 days. This affects approximately 60% of our "
        "component sourcing by volume. Key affected categories: power supply units, motor controllers, "
        "and sensor modules. Current annualized import value subject to the new tariff is $12.8M. "
        "Our current contracts with Chinese suppliers run through Q2 next year with no tariff "
        "adjustment clauses."
    ),
}

SEVERITY_COLORS = {
    "LOW":      ("#1D9E75", "#E1F5EE"),
    "MEDIUM":   ("#BA7517", "#FAEEDA"),
    "HIGH":     ("#D85A30", "#FAECE7"),
    "CRITICAL": ("#A32D2D", "#FCEBEB"),
}

IMPACT_COLORS = {
    "minimal":     "#1D9E75",
    "moderate":    "#BA7517",
    "significant": "#D85A30",
    "severe":      "#A32D2D",
    "critical":    "#7F1D1D",
}

STEP_ERROR_GUIDANCE = {
    1: (
        "**The incident parser failed.** This usually means the input text "
        "was too short or the AI returned unexpected output.\n\n"
        "**Try:** Add more detail — include supplier names, affected products, "
        "region, and financial figures."
    ),
    2: (
        "**The context researcher failed.**\n\n"
        "**Try:** Run the analysis again — this step occasionally times out."
    ),
    3: (
        "**The root cause analyzer failed.** Usually a JSON parsing issue.\n\n"
        "**Try:** Run the analysis again."
    ),
    4: (
        "**The brief generator failed.**\n\n"
        "**Try:** Run the analysis again — almost always a transient API issue."
    ),
}


def severity_badge(level: str) -> str:
    color, bg = SEVERITY_COLORS.get(level, ("#888", "#eee"))
    return (
        f'<span style="background:{bg};color:{color};padding:3px 10px;'
        f'border-radius:4px;font-weight:600;font-size:13px;">{level}</span>'
    )


def impact_dot(level: str) -> str:
    color = IMPACT_COLORS.get(level, "#888")
    return f'<span style="color:{color};font-weight:600;">● {level.upper()}</span>'


def generate_pdf(result: PipelineResult) -> bytes:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_margins(15, 15, 15)

    pdf.set_font("Helvetica", "B", 18)
    pdf.cell(0, 10, "Supply Chain Incident Brief", ln=True)
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(
        0, 6,
        f"ID: {result.brief.incident_id}  |  "
        f"Severity: {result.brief.severity_level}  |  "
        f"Status: {result.brief.status}",
        ln=True
    )
    pdf.ln(4)

    def section(title):
        pdf.set_font("Helvetica", "B", 13)
        pdf.set_fill_color(240, 240, 240)
        pdf.cell(0, 8, title, ln=True, fill=True)
        pdf.set_font("Helvetica", "", 10)
        pdf.ln(2)

    def body(text):
        safe = str(text).encode("latin-1", "replace").decode("latin-1")
        pdf.multi_cell(0, 5, safe)
        pdf.ln(2)

    section("Executive Summary")
    body(result.brief.executive_summary)

    section("Risk Scores")
    r = result.brief.risk_score
    body(
        f"Overall: {r.overall}/10  |  Operational: {r.operational}/10  |  "
        f"Financial: {r.financial}/10  |  Reputational: {r.reputational}/10"
    )
    body(r.reasoning)

    section("Financial Exposure")
    f = result.brief.financial_exposure
    body(f"${f.minimum_usd:,} - ${f.maximum_usd:,}  (confidence: {f.confidence})")
    body(f.notes)

    section("Immediate Actions")
    for a in result.brief.immediate_actions:
        body(f"[{a.priority}] {a.action}")
        body(f"    Owner: {a.owner}  |  Deadline: {a.deadline}")
        body(f"    Why: {a.why}")

    section("Root Cause Analysis")
    body(f"Primary root cause: {result.analysis.primary_root_cause}")
    body(f"Vulnerability type: {result.analysis.vulnerability_type}")
    body(f"Recovery timeline: {result.analysis.severity_assessment.recovery_timeline}")

    section("Impact Chain")
    for i, step in enumerate(result.analysis.impact_chain, 1):
        body(f"{i}. {step}")

    section("Alternative Options")
    for opt in result.brief.alternative_options:
        body(f"* {opt.option}  [{opt.feasibility}]  {opt.estimated_cost_impact}")

    section("Stakeholder Email")
    body(f"To: {result.brief.stakeholder_email.to}")
    body(f"Subject: {result.brief.stakeholder_email.subject}")
    pdf.ln(2)
    body(result.brief.stakeholder_email.body)

    section("Monitoring Plan")
    for m in result.brief.monitoring_plan:
        body(f"* {m.metric}  -  check {m.frequency}")
        body(f"  Escalate if: {m.escalation_trigger}")

    section("Analyst Note")
    body(result.analysis.analyst_note)

    return pdf.output()


def render_audit_trail(result: PipelineResult):
    from utils.audit import save_audit, get_audit

    brief   = result.brief
    inc_id  = brief.incident_id
    actions = brief.immediate_actions

    existing = get_audit(inc_id)

    st.divider()
    st.subheader("Decision audit trail")
    st.markdown(
        "Mark which actions were taken and what happened. "
        "This builds your follow-through rate over time — "
        "tracked on the dashboard."
    )

    OUTCOME_OPTIONS = [
        "not_recorded", "resolved", "partially_resolved",
        "escalated", "ongoing", "skipped",
    ]
    OUTCOME_LABELS = {
        "not_recorded":       "Not recorded",
        "resolved":           "Resolved the issue",
        "partially_resolved": "Partially resolved",
        "escalated":          "Escalated further",
        "ongoing":            "Still ongoing",
        "skipped":            "Decided to skip",
    }
    OUTCOME_COLORS = {
        "resolved":           "#1D9E75",
        "partially_resolved": "#BA7517",
        "escalated":          "#D85A30",
        "ongoing":            "#378ADD",
        "skipped":            "#888888",
        "not_recorded":       "#cccccc",
    }

    existing_actions = {}
    if existing and existing.get("actions"):
        for a in existing["actions"]:
            existing_actions[a["action_priority"]] = a

    audit_data = []

    for action in actions:
        prio = action.priority
        prev = existing_actions.get(prio, {})

        with st.expander(
            f"**[{prio}]** {action.action}",
            expanded=not bool(existing)
        ):
            col_check, col_outcome, col_notes = st.columns([1, 2, 3])

            with col_check:
                was_taken = st.checkbox(
                    "Action taken",
                    value=bool(prev.get("was_taken", False)),
                    key=f"adt_{inc_id}_{prio}"
                )

            with col_outcome:
                prev_outcome = prev.get("outcome", "not_recorded")
                if prev_outcome not in OUTCOME_OPTIONS:
                    prev_outcome = "not_recorded"
                outcome = st.selectbox(
                    "Outcome",
                    options=OUTCOME_OPTIONS,
                    index=OUTCOME_OPTIONS.index(prev_outcome),
                    format_func=lambda x: OUTCOME_LABELS[x],
                    key=f"ado_{inc_id}_{prio}",
                    disabled=not was_taken
                )
                if was_taken and outcome != "not_recorded":
                    color = OUTCOME_COLORS.get(outcome, "#888")
                    st.markdown(
                        f'<span style="color:{color};font-size:12px;'
                        f'font-weight:500">● {OUTCOME_LABELS[outcome]}</span>',
                        unsafe_allow_html=True
                    )

            with col_notes:
                notes = st.text_input(
                    "Notes (optional)",
                    value=prev.get("notes", ""),
                    placeholder="What happened? Any blockers?",
                    key=f"adn_{inc_id}_{prio}"
                )

        audit_data.append({
            "priority":  prio,
            "action":    action.action,
            "owner":     action.owner,
            "deadline":  action.deadline,
            "was_taken": was_taken,
            "outcome":   outcome if was_taken else "not_recorded",
            "notes":     notes,
        })

    st.markdown("---")
    col_overall, col_time, col_lessons = st.columns([2, 1, 3])

    existing_outcome_row = existing.get("outcome", {}) if existing else {}

    OVERALL_OPTIONS = ["ongoing", "resolved", "escalated", "closed_unresolved"]
    OVERALL_LABELS  = {
        "ongoing":           "Still ongoing",
        "resolved":          "Fully resolved",
        "escalated":         "Escalated to leadership",
        "closed_unresolved": "Closed — unresolved",
    }
    prev_overall = existing_outcome_row.get("overall_outcome", "ongoing")
    if prev_overall not in OVERALL_OPTIONS:
        prev_overall = "ongoing"

    with col_overall:
        overall_outcome = st.selectbox(
            "Overall incident outcome",
            options=OVERALL_OPTIONS,
            index=OVERALL_OPTIONS.index(prev_overall),
            format_func=lambda x: OVERALL_LABELS[x],
            key=f"adoverall_{inc_id}"
        )

    with col_time:
        resolution_time = st.text_input(
            "Resolution time",
            value=existing_outcome_row.get("resolution_time", ""),
            placeholder="e.g. 3 days",
            key=f"adtime_{inc_id}"
        )

    with col_lessons:
        lessons = st.text_area(
            "Lessons learned",
            value=existing_outcome_row.get("lessons_learned", ""),
            placeholder="What would you do differently next time?",
            height=80,
            key=f"adlessons_{inc_id}"
        )

    if st.button(
        "Save audit trail",
        type="primary",
        key=f"adsave_{inc_id}"
    ):
        save_audit(
            incident_id=inc_id,
            actions=audit_data,
            overall_outcome=overall_outcome,
            resolution_time=resolution_time,
            lessons_learned=lessons
        )
        taken_count = sum(1 for a in audit_data if a["was_taken"])
        st.success(
            f"Saved. {taken_count}/{len(audit_data)} actions marked as taken. "
            f"Follow-through rate updated on the dashboard."
        )


def render_results(result: PipelineResult):
    brief    = result.brief
    analysis = result.analysis
    parsed   = result.parsed
    context  = result.context

    st.divider()

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown("**Incident ID**")
        st.markdown(f"`{brief.incident_id}`")
    with col2:
        st.markdown("**Severity**")
        st.markdown(severity_badge(brief.severity_level), unsafe_allow_html=True)
    with col3:
        st.markdown("**Type**")
        st.markdown(f"`{parsed.incident_type}`")
    with col4:
        st.markdown("**Recovery**")
        st.markdown(f"`{analysis.severity_assessment.recovery_timeline}`")

    st.divider()

    left, right = st.columns([3, 2])

    with left:
        st.subheader("Executive summary")
        st.info(brief.executive_summary)

        st.subheader("Immediate actions")
        for action in brief.immediate_actions:
            with st.expander(f"**[{action.priority}]** {action.action}"):
                st.markdown(f"**Owner:** {action.owner}")
                st.markdown(f"**Deadline:** {action.deadline}")
                st.markdown(f"**Why urgent:** {action.why}")

        st.subheader("Key decisions required")
        for d in brief.key_decisions_required:
            with st.expander(d.decision):
                st.markdown(f"**Deadline:** {d.deadline}")
                st.warning(f"If delayed: {d.consequence_of_delay}")

    with right:
        st.subheader("Risk scores")
        r = brief.risk_score
        for label, score in [
            ("Overall", r.overall),
            ("Operational", r.operational),
            ("Financial", r.financial),
            ("Reputational", r.reputational),
        ]:
            color = (
                "#1D9E75" if score <= 3
                else "#BA7517" if score <= 6
                else "#A32D2D"
            )
            st.markdown(
                f'<div style="display:flex;justify-content:space-between;'
                f'align-items:center;padding:6px 0;border-bottom:1px solid #eee">'
                f'<span style="font-size:13px">{label}</span>'
                f'<span style="font-weight:600;color:{color};font-size:15px">'
                f'{score}/10</span></div>',
                unsafe_allow_html=True
            )
        st.caption(r.reasoning)
        st.markdown("---")

        st.subheader("Financial exposure")
        f = brief.financial_exposure
        st.markdown(
            f'<div style="font-size:20px;font-weight:600">'
            f'${f.minimum_usd:,} – ${f.maximum_usd:,}</div>',
            unsafe_allow_html=True
        )
        st.caption(f"Confidence: {f.confidence}  |  {f.notes}")
        st.markdown("---")

        st.subheader("Severity assessment")
        sa = analysis.severity_assessment
        for label, val in [
            ("Operational",  sa.operational_impact),
            ("Financial",    sa.financial_impact),
            ("Reputational", sa.reputational_impact),
        ]:
            st.markdown(
                f'<div style="display:flex;justify-content:space-between;padding:4px 0">'
                f'<span style="font-size:13px;color:#666">{label}</span>'
                f'{impact_dot(val)}</div>',
                unsafe_allow_html=True
            )

    st.divider()

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Root cause analysis",
        "Alternative options",
        "Stakeholder email",
        "Monitoring plan",
        "Research context",
    ])

    with tab1:
        st.markdown("**Primary root cause**")
        st.error(analysis.primary_root_cause)
        st.markdown(f"**Vulnerability type:** `{analysis.vulnerability_type}`")
        st.markdown(f"**Confidence:** `{analysis.confidence_level}`")

        st.markdown("**Impact chain**")
        for i, step in enumerate(analysis.impact_chain, 1):
            st.markdown(
                f'<div style="display:flex;gap:12px;padding:6px 0;'
                f'border-bottom:1px solid #f0f0f0">'
                f'<span style="font-weight:700;color:#D85A30;min-width:20px">{i}</span>'
                f'<span style="font-size:14px">{step}</span></div>',
                unsafe_allow_html=True
            )

        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("**Contributing factors**")
            for factor in analysis.contributing_factors:
                st.markdown(f"• {factor}")
        with col_b:
            st.markdown("**Immediate risks (next 48–72h)**")
            for risk in analysis.immediate_risks:
                st.markdown(f"⚠️ {risk}")

        st.markdown("**Systemic weaknesses exposed**")
        for w in analysis.systemic_weaknesses_exposed:
            st.markdown(f"~ {w}")

        if analysis.analogous_incidents:
            st.markdown("**Analogous incidents**")
            for a in analysis.analogous_incidents:
                st.markdown(f"**[{a.company}, {a.year}]** {a.lesson}")

        st.markdown("**Analyst note**")
        st.markdown(
            f'<div style="border-left:3px solid #D85A30;padding:10px 16px;'
            f'background:#FAECE7;border-radius:0 6px 6px 0;font-size:14px;'
            f'line-height:1.6">{analysis.analyst_note}</div>',
            unsafe_allow_html=True
        )

    with tab2:
        for opt in brief.alternative_options:
            with st.expander(
                f"**{opt.option}** — {opt.estimated_cost_impact} | `{opt.feasibility}`"
            ):
                col_p, col_c = st.columns(2)
                with col_p:
                    st.markdown("**Pros**")
                    for p in opt.pros:
                        st.markdown(f"✓ {p}")
                with col_c:
                    st.markdown("**Cons**")
                    for c in opt.cons:
                        st.markdown(f"✗ {c}")

    with tab3:
        email = brief.stakeholder_email
        st.markdown(f"**To:** {email.to}")
        st.markdown(f"**Subject:** {email.subject}")
        st.divider()
        st.markdown(email.body)
        st.divider()
        if st.button("Show copyable version", key=f"copy_email_{brief.incident_id}"):
            st.code(email.body, language=None)

    with tab4:
        for m in brief.monitoring_plan:
            with st.expander(f"**{m.metric}** — check {m.frequency}"):
                st.warning(f"Escalate if: {m.escalation_trigger}")
        st.markdown(f"**Next situation report:** {brief.next_update}")

    with tab5:
        st.markdown(f"**Research confidence:** `{context.confidence_level}`")
        st.markdown("**Current situation**")
        st.markdown(context.current_situation)
        st.markdown("**Market context**")
        st.markdown(context.market_context)

        col_amp, col_mit = st.columns(2)
        with col_amp:
            st.markdown("**Risk amplifiers**")
            for r in context.risk_amplifiers:
                st.markdown(f"▲ {r}")
        with col_mit:
            st.markdown("**Risk mitigators**")
            for r in context.risk_mitigators:
                st.markdown(f"▼ {r}")

        if context.alternative_suppliers_or_routes:
            st.markdown("**Alternatives identified**")
            for alt in context.alternative_suppliers_or_routes:
                st.markdown(f"• **{alt.name}** — {alt.notes}")

        if context.research_gaps:
            st.markdown("**Research gaps**")
            for g in context.research_gaps:
                st.markdown(f"? {g}")

    st.divider()
    pdf_bytes = generate_pdf(result)
    st.download_button(
        label="Download incident brief as PDF",
        data=bytes(pdf_bytes),
        file_name=f"{brief.incident_id}.pdf",
        mime="application/pdf",
        type="primary",
    )

    render_audit_trail(result)


def main():
    st.title("Supply Chain Incident Response Agent")
    st.markdown(
        "Paste a supply chain incident report below. "
        "The agent runs a 4-step AI pipeline and generates "
        "a complete incident brief with root cause analysis, "
        "immediate actions, and a ready-to-send stakeholder email."
    )

    st.markdown("**Try an example:**")
    cols = st.columns(len(EXAMPLES))
    for col, (label, text) in zip(cols, EXAMPLES.items()):
        with col:
            if st.button(label, use_container_width=True):
                st.session_state["incident_text"] = text

    st.divider()

    incident_text = st.text_area(
        "Incident report",
        value=st.session_state.get("incident_text", ""),
        height=180,
        placeholder=(
            "Paste your supply chain incident report here...\n\n"
            "Include: what happened, where, which suppliers or products "
            "are affected, timeline, and any financial figures you have."
        ),
    )

    is_valid = len(incident_text.strip()) >= 50

    run_clicked = st.button(
        "Run analysis",
        type="primary",
        disabled=not incident_text.strip(),
        use_container_width=True,
    )

    if run_clicked:
        if len(incident_text.strip()) < 50:
            st.error("Incident description is too short. Add more detail and try again.")
            st.stop()

        st.session_state["incident_text"] = incident_text
        progress_placeholder = st.empty()
        step_messages = {}

        def status_callback(step: int, message: str):
            step_messages[step] = message
            with progress_placeholder.container():
                for s in range(1, 5):
                    label = {
                        1: "Parsing incident",
                        2: "Researching context",
                        3: "Analyzing root cause",
                        4: "Generating brief",
                    }[s]
                    if s in step_messages:
                        msg = step_messages[s]
                        if msg.startswith("Done"):
                            st.success(f"Step {s}: {label} — {msg}")
                        else:
                            st.info(f"Step {s}: {label} — {msg}")
                    else:
                        st.markdown(
                            f'<div style="color:#aaa;padding:4px 0">'
                            f'Step {s}: {label} — waiting...</div>',
                            unsafe_allow_html=True
                        )

        try:
            result = run_pipeline(incident_text, status_callback=status_callback)
            st.session_state["last_result"] = result

            from utils.database import save_incident
            from utils.watchlist import check_incident_against_watchlist
            save_incident(result)
            matches = check_incident_against_watchlist(result)
            st.session_state["last_watchlist_matches"] = matches

            progress_placeholder.empty()

            if matches:
                names = ", ".join(m["supplier"] for m in matches)
                st.warning(
                    f"⚠️ Watchlist alert — this incident involves "
                    f"**{len(matches)}** tracked supplier(s): **{names}**. "
                    f"Risk scores updated on the Watchlist page."
                )

            render_results(result)

        except PipelineStepError as e:
            progress_placeholder.empty()
            st.error(f"Analysis failed at Step {e.step}: {e.step_name}")
            guidance = STEP_ERROR_GUIDANCE.get(e.step, "")
            if guidance:
                st.markdown(guidance)
            with st.expander("Technical error details"):
                st.code(str(e.original_error))

        except RuntimeError as e:
            progress_placeholder.empty()
            error_msg = str(e)
            st.error(error_msg)
            if "rate limit" in error_msg.lower():
                st.info("Wait 60 seconds then click Run analysis again.")
            elif "quota" in error_msg.lower():
                st.info("Add credits at platform.openai.com/settings/billing")
            elif "api key" in error_msg.lower() or "invalid" in error_msg.lower():
                st.info("Check your `.env` file — the key should start with `sk-...`")
            elif "connect" in error_msg.lower():
                st.info("Check your internet connection and try again.")

        except Exception as e:
            progress_placeholder.empty()
            st.error("An unexpected error occurred.")
            with st.expander("Technical error details"):
                st.code(str(e))
            st.markdown(
                "**Common fixes:**\n"
                "- Check your `OPENAI_API_KEY` in `.env`\n"
                "- Make sure you have API credits at platform.openai.com\n"
                "- Try a shorter incident description\n"
                "- Restart the app: `python -m streamlit run app.py`"
            )

    elif not run_clicked:
        if "last_result" in st.session_state:
            result = st.session_state["last_result"]
            if matches := st.session_state.get("last_watchlist_matches"):
                names = ", ".join(m["supplier"] for m in matches)
                st.warning(
                    f"⚠️ Watchlist alert — this incident involves "
                    f"**{len(matches)}** tracked supplier(s): **{names}**."
                )
            render_results(result)
        else:
            st.markdown(
                '<div style="text-align:center;padding:3rem;color:#aaa;">'
                'Click an example above or paste your own incident report, '
                'then click Run analysis</div>',
                unsafe_allow_html=True
            )
if __name__ == "__main__":
    main()