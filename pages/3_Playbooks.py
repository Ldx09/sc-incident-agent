import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from fpdf import FPDF
from utils.playbook import (
    generate_playbook, get_all_playbooks,
    get_playbook, delete_playbook, get_incident_type_counts
)

st.set_page_config(
    page_title="Response Playbooks",
    page_icon="📋",
    layout="wide"
)

TYPE_LABELS = {
    "port_disruption":              "Port disruption",
    "supplier_bankruptcy":          "Supplier bankruptcy",
    "tariff_change":                "Tariff change",
    "weather_event":                "Weather event",
    "quality_recall":               "Quality recall",
    "facility_damage":              "Facility damage",
    "geopolitical":                 "Geopolitical",
    "cyberattack":                  "Cyberattack",
    "other":                        "Other",
}


def generate_playbook_pdf(playbook: dict) -> bytes:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_margins(15, 15, 15)

    def safe(text):
        return str(text).encode("latin-1", "replace").decode("latin-1")

    def section(title):
        pdf.set_font("Helvetica", "B", 13)
        pdf.set_fill_color(240, 240, 240)
        pdf.cell(0, 8, safe(title), ln=True, fill=True)
        pdf.set_font("Helvetica", "", 10)
        pdf.ln(2)

    def body(text):
        pdf.multi_cell(0, 5, safe(str(text)))
        pdf.ln(2)

    def bullet_list(items):
        for item in items:
            if isinstance(item, dict):
                text = f"{item.get('role', '')}: {item.get('why_needed', '')}"
            else:
                text = str(item)
            pdf.multi_cell(0, 5, safe(f"  * {text}"))
        pdf.ln(2)

    pdf.set_font("Helvetica", "B", 20)
    pdf.cell(0, 12, safe(playbook.get("title", "Response Playbook")), ln=True)
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(
        0, 6,
        safe(
            f"Incident type: {playbook.get('incident_type', '').replace('_', ' ').title()}  |  "
            f"Based on {playbook.get('incident_count', 0)} incident(s)  |  "
            f"Generated: {(playbook.get('generated_at', ''))[:10]}"
        ),
        ln=True
    )
    pdf.ln(4)

    if playbook.get("incident_type_description"):
        section("Overview")
        body(playbook["incident_type_description"])

    if playbook.get("early_warnings"):
        section("Early warning signals")
        bullet_list(playbook["early_warnings"])

    if playbook.get("first_24h"):
        section("First 24 hours — priority actions")
        for i, action in enumerate(playbook["first_24h"], 1):
            pdf.multi_cell(0, 5, safe(f"  {i}. {action}"))
        pdf.ln(2)

    if playbook.get("root_causes"):
        section("Common root causes")
        bullet_list(playbook["root_causes"])

    if playbook.get("what_worked"):
        section("What worked")
        bullet_list(playbook["what_worked"])

    if playbook.get("what_failed"):
        section("What failed or made things worse")
        bullet_list(playbook["what_failed"])

    if playbook.get("success_metrics"):
        section("Success metrics — how to know it's resolving")
        bullet_list(playbook["success_metrics"])

    if playbook.get("key_contacts"):
        section("Key contacts to have ready")
        for c in playbook["key_contacts"]:
            if isinstance(c, dict):
                body(f"{c.get('role', '')}: {c.get('why_needed', '')}")
            else:
                body(str(c))

    if playbook.get("prevention_recommendations"):
        section("Prevention recommendations")
        bullet_list(playbook.get("prevention_recommendations", []))

    if playbook.get("lessons"):
        section("Key lesson — never forget this")
        body(playbook["lessons"])

    return pdf.output()


def render_playbook_card(playbook: dict):
    inc_type  = playbook.get("incident_type", "")
    label     = TYPE_LABELS.get(inc_type, inc_type.replace("_", " ").title())
    count     = playbook.get("incident_count", 0)
    conf      = playbook.get("confidence", "medium")
    generated = (playbook.get("generated_at") or "")[:10]

    conf_color = {
        "high":   "#1D9E75",
        "medium": "#BA7517",
        "low":    "#D85A30"
    }.get(conf, "#888")

    st.markdown(
        f'<div style="display:flex;align-items:center;gap:10px;margin-bottom:.5rem">'
        f'<span style="font-size:15px;font-weight:500">{playbook.get("title", label)}</span>'
        f'<span style="font-size:11px;padding:2px 8px;border-radius:4px;'
        f'background:var(--color-background-secondary);color:var(--color-text-secondary)">'
        f'{label}</span>'
        f'<span style="font-size:11px;color:{conf_color};font-weight:500">'
        f'● {conf.upper()} confidence</span>'
        f'<span style="font-size:11px;color:var(--color-text-tertiary);margin-left:auto">'
        f'Based on {count} incident(s) · Generated {generated}</span>'
        f'</div>',
        unsafe_allow_html=True
    )

    if playbook.get("incident_type_description"):
        st.caption(playbook["incident_type_description"])

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Early warnings",
        "First 24 hours",
        "Root causes & lessons",
        "What worked / failed",
        "Contacts & metrics",
    ])

    with tab1:
        st.markdown("**Signals to watch for — before it becomes critical:**")
        warnings = playbook.get("early_warnings", [])
        if warnings:
            for w in warnings:
                st.markdown(
                    f'<div style="display:flex;gap:10px;padding:6px 0;'
                    f'border-bottom:0.5px solid var(--color-border-tertiary)">'
                    f'<span style="color:#BA7517;font-size:14px;flex-shrink:0">⚠</span>'
                    f'<span style="font-size:13px">{w}</span></div>',
                    unsafe_allow_html=True
                )
        else:
            st.caption("No early warning data yet.")

    with tab2:
        st.markdown("**Priority actions — first 24 hours:**")
        actions = playbook.get("first_24h", [])
        if actions:
            for i, action in enumerate(actions, 1):
                parts = action.split(":", 1) if ":" in action else ["", action]
                owner = parts[0].strip()
                task  = parts[1].strip() if len(parts) > 1 else action
                st.markdown(
                    f'<div style="display:flex;gap:12px;padding:8px 0;'
                    f'border-bottom:0.5px solid var(--color-border-tertiary)">'
                    f'<span style="font-weight:600;color:#D85A30;min-width:22px;'
                    f'font-size:13px">{i}</span>'
                    f'<div>'
                    f'<div style="font-size:11px;color:var(--color-text-tertiary);'
                    f'font-weight:500;text-transform:uppercase;letter-spacing:.04em">'
                    f'{owner}</div>'
                    f'<div style="font-size:13px;color:var(--color-text-primary)">'
                    f'{task}</div>'
                    f'</div></div>',
                    unsafe_allow_html=True
                )
        else:
            st.caption("No first-24h actions recorded yet.")

    with tab3:
        col_rc, col_lesson = st.columns([1, 1])
        with col_rc:
            st.markdown("**Common root causes:**")
            for rc in playbook.get("root_causes", []):
                st.markdown(f"~ {rc}")

        with col_lesson:
            st.markdown("**Key lesson — never forget this:**")
            if playbook.get("lessons"):
                st.markdown(
                    f'<div style="border-left:3px solid #7F77DD;padding:10px 14px;'
                    f'background:#EEEDFE;border-radius:0 6px 6px 0;font-size:13px;'
                    f'line-height:1.6;color:#26215C">'
                    f'{playbook["lessons"]}</div>',
                    unsafe_allow_html=True
                )

        if playbook.get("prevention_recommendations"):
            st.markdown("**Prevention recommendations:**")
            for p in playbook["prevention_recommendations"]:
                st.markdown(f"→ {p}")

    with tab4:
        col_w, col_f = st.columns(2)
        with col_w:
            st.markdown("**What worked:**")
            worked = playbook.get("what_worked", [])
            if worked:
                for w in worked:
                    st.markdown(
                        f'<div style="padding:5px 0;border-bottom:0.5px solid '
                        f'var(--color-border-tertiary);font-size:13px">'
                        f'<span style="color:#1D9E75">✓</span> {w}</div>',
                        unsafe_allow_html=True
                    )
            else:
                st.caption("No audit data yet — run audits to populate this.")

        with col_f:
            st.markdown("**What failed or made things worse:**")
            failed = playbook.get("what_failed", [])
            if failed:
                for f in failed:
                    st.markdown(
                        f'<div style="padding:5px 0;border-bottom:0.5px solid '
                        f'var(--color-border-tertiary);font-size:13px">'
                        f'<span style="color:#D85A30">✗</span> {f}</div>',
                        unsafe_allow_html=True
                    )
            else:
                st.caption("No failure data recorded yet.")

    with tab5:
        col_c, col_m = st.columns(2)
        with col_c:
            st.markdown("**Key contacts to have ready:**")
            contacts = playbook.get("key_contacts", [])
            if contacts:
                for c in contacts:
                    if isinstance(c, dict):
                        st.markdown(
                            f'<div style="padding:5px 0;border-bottom:0.5px solid '
                            f'var(--color-border-tertiary)">'
                            f'<span style="font-size:13px;font-weight:500">'
                            f'{c.get("role", "")}</span>'
                            f'<br><span style="font-size:12px;color:var(--color-text-secondary)">'
                            f'{c.get("why_needed", "")}</span></div>',
                            unsafe_allow_html=True
                        )
                    else:
                        st.markdown(f"• {c}")
            else:
                st.caption("No contact data yet.")

        with col_m:
            st.markdown("**Success metrics — how to know it's resolving:**")
            metrics = playbook.get("success_metrics", [])
            if metrics:
                for m in metrics:
                    st.markdown(
                        f'<div style="padding:5px 0;border-bottom:0.5px solid '
                        f'var(--color-border-tertiary);font-size:13px">'
                        f'<span style="color:#378ADD">◉</span> {m}</div>',
                        unsafe_allow_html=True
                    )
            else:
                st.caption("No metrics defined yet.")


def main():
    st.title("Response playbooks")
    st.markdown(
        "Playbooks are automatically synthesized from your incident history. "
        "The more incidents you analyze, the sharper each playbook becomes. "
        "Generate a playbook for any incident type with 1+ incidents on record."
    )

    type_counts = get_incident_type_counts()
    existing    = get_all_playbooks()
    existing_types = {p["incident_type"] for p in existing}

    if not type_counts:
        st.info(
            "No incidents analyzed yet. Go to the main page, run some analyses, "
            "then come back to generate your first playbook."
        )
        st.page_link("app.py", label="Go to main page", icon="🚨")
        return

    c1, c2, c3 = st.columns(3)
    c1.metric("Incident types on record", len(type_counts))
    c2.metric("Playbooks generated",      len(existing))
    c3.metric("Total incidents analyzed", sum(type_counts.values()))

    st.divider()
    st.subheader("Generate a playbook")
    st.markdown(
        "Select an incident type to synthesize all past incidents of that type "
        "into a reusable SOP. Re-generate any time to incorporate new incidents."
    )

    gen_cols = st.columns(min(len(type_counts), 4))
    for col, (inc_type, count) in zip(gen_cols, type_counts.items()):
        label   = TYPE_LABELS.get(inc_type, inc_type.replace("_", " ").title())
        has_one = inc_type in existing_types
        badge   = " ✓" if has_one else ""
        with col:
            st.markdown(
                f'<div style="text-align:center;padding:8px;background:'
                f'var(--color-background-secondary);border-radius:8px;'
                f'margin-bottom:6px">'
                f'<div style="font-size:13px;font-weight:500">{label}{badge}</div>'
                f'<div style="font-size:11px;color:var(--color-text-tertiary)">'
                f'{count} incident(s)</div></div>',
                unsafe_allow_html=True
            )
            btn_label = "Re-generate" if has_one else "Generate"
            if st.button(btn_label, key=f"gen_{inc_type}", use_container_width=True):
                with st.spinner(
                    f"Synthesizing {count} incident(s) into a {label} playbook..."
                ):
                    try:
                        playbook = generate_playbook(inc_type)
                        if playbook:
                            st.success(
                                f"Playbook generated from {count} incident(s). "
                                f"Scroll down to view it."
                            )
                            st.rerun()
                        else:
                            st.error("Could not generate playbook. No incidents found.")
                    except Exception as e:
                        st.error(f"Generation failed: {e}")

    st.divider()

    existing = get_all_playbooks()
    if not existing:
        st.info("No playbooks generated yet. Click a button above to create your first one.")
        return

    st.subheader(f"Your playbooks ({len(existing)})")

    for playbook in existing:
        inc_type = playbook.get("incident_type", "")
        label    = TYPE_LABELS.get(inc_type, inc_type.replace("_", " ").title())

        with st.expander(
            f"**{playbook.get('title', label)}**  |  "
            f"{label}  |  "
            f"{playbook.get('incident_count', 0)} incident(s)  |  "
            f"Generated {(playbook.get('generated_at') or '')[:10]}",
            expanded=True
        ):
            render_playbook_card(playbook)

            st.markdown("")
            col_pdf, col_regen, col_del = st.columns([2, 1, 1])

            with col_pdf:
                try:
                    pdf_bytes = generate_playbook_pdf(playbook)
                    filename  = f"{inc_type}_playbook.pdf"
                    st.download_button(
                        label="Download as PDF",
                        data=bytes(pdf_bytes),
                        file_name=filename,
                        mime="application/pdf",
                        type="primary",
                        key=f"pdf_{inc_type}",
                        use_container_width=True
                    )
                except Exception as e:
                    st.caption(f"PDF error: {e}")

            with col_regen:
                count = type_counts.get(inc_type, 0)
                if st.button(
                    "Re-generate",
                    key=f"regen_{inc_type}",
                    use_container_width=True
                ):
                    with st.spinner("Re-synthesizing..."):
                        try:
                            generate_playbook(inc_type)
                            st.success("Playbook updated.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Failed: {e}")

            with col_del:
                if st.button(
                    "Delete",
                    key=f"del_{inc_type}",
                    type="secondary",
                    use_container_width=True
                ):
                    delete_playbook(inc_type)
                    st.warning("Playbook deleted.")
                    st.rerun()


main()