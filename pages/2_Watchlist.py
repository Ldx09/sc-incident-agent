import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import streamlit.components.v1 as components
import json
from utils.watchlist import (
    get_watchlist, add_supplier, remove_supplier,
    get_hits_for_supplier, update_notes
)

st.set_page_config(
    page_title="Supplier Watchlist",
    page_icon="👁️",
    layout="wide"
)

RISK_COLORS = {
    (0, 0):  ("#888888", "#F1EFE8"),
    (1, 3):  ("#1D9E75", "#E1F5EE"),
    (4, 6):  ("#BA7517", "#FAEEDA"),
    (7, 8):  ("#D85A30", "#FAECE7"),
    (9, 10): ("#A32D2D", "#FCEBEB"),
}

SEV_COLORS = {
    "CRITICAL": "#A32D2D",
    "HIGH":     "#D85A30",
    "MEDIUM":   "#BA7517",
    "LOW":      "#1D9E75",
}


def risk_color(score: int):
    for (lo, hi), colors in RISK_COLORS.items():
        if lo <= score <= hi:
            return colors
    return ("#888", "#eee")


def risk_label(score: int) -> str:
    if score == 0:   return "No incidents"
    if score <= 3:   return "Low risk"
    if score <= 6:   return "Moderate risk"
    if score <= 8:   return "High risk"
    return "Critical risk"


def risk_gauge(score: int):
    fg, bg = risk_color(score)
    pct = score * 10
    html = f"""
<!DOCTYPE html><html><head>
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.js"></script>
</head><body style="margin:0;background:transparent">
<div style="position:relative;width:100%;height:140px">
<canvas id="g{score}_{id(score)}"></canvas>
<div style="position:absolute;top:55%;left:50%;transform:translate(-50%,-50%);
  text-align:center;pointer-events:none">
  <div style="font-size:28px;font-weight:600;color:{fg}">{score}</div>
  <div style="font-size:11px;color:#888">/ 10</div>
</div>
</div>
<script>
var cid = 'g{score}_{id(score)}';
new Chart(document.getElementById(cid),{{
  type:'doughnut',
  data:{{
    datasets:[{{
      data:[{pct},{100-pct}],
      backgroundColor:['{fg}','rgba(0,0,0,0.07)'],
      borderWidth:0,
      circumference:180,
      rotation:270
    }}]
  }},
  options:{{responsive:true,maintainAspectRatio:false,
    plugins:{{legend:{{display:false}},tooltip:{{enabled:false}}}}}}
}});
</script></body></html>"""
    components.html(html, height=150)


def hits_chart(hits: list[dict]):
    if not hits:
        return
    recent = hits[:10]
    labels = [h["incident_id"].split("-")[-1] for h in reversed(recent)]
    colors = [SEV_COLORS.get(h["severity"], "#888") for h in reversed(recent)]
    values = [
        {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1}.get(h["severity"], 1)
        for h in reversed(recent)
    ]
    html = f"""
<!DOCTYPE html><html><head>
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.js"></script>
</head><body style="margin:0;background:transparent">
<div style="position:relative;width:100%;height:160px">
<canvas id="h"></canvas></div>
<script>
new Chart(document.getElementById('h'),{{
  type:'bar',
  data:{{
    labels:{json.dumps(labels)},
    datasets:[{{
      label:'Severity',
      data:{json.dumps(values)},
      backgroundColor:{json.dumps(colors)},
      borderRadius:4,borderSkipped:false
    }}]
  }},
  options:{{
    responsive:true,maintainAspectRatio:false,
    plugins:{{legend:{{display:false}}}},
    scales:{{
      y:{{min:0,max:4,ticks:{{
        stepSize:1,
        callback:function(v){{
          return ['','LOW','MEDIUM','HIGH','CRITICAL'][v]||'';
        }}
      }},grid:{{color:'rgba(0,0,0,0.06)'}}}},
      x:{{ticks:{{font:{{size:10}}}}}}
    }}
  }}
}});
</script></body></html>"""
    components.html(html, height=180)


def main():
    st.title("Supplier risk watchlist")
    st.markdown(
        "Add suppliers you depend on. Every time an incident analysis "
        "mentions a watchlisted supplier, they are automatically flagged "
        "and their risk score increases."
    )

    watchlist = get_watchlist()

    # ── Summary bar ──────────────────────────────────────────────
    if watchlist:
        total     = len(watchlist)
        at_risk   = sum(1 for w in watchlist if w["risk_score"] >= 4)
        critical  = sum(1 for w in watchlist if w["risk_score"] >= 9)
        total_inc = sum(w["incident_count"] for w in watchlist)

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Suppliers tracked", total)
        c2.metric("At risk (score ≥ 4)", at_risk)
        c3.metric("Critical (score ≥ 9)", critical)
        c4.metric("Total incidents flagged", total_inc)
        st.divider()

    # ── Add supplier ─────────────────────────────────────────────
    with st.expander("Add supplier to watchlist", expanded=len(watchlist) == 0):
        col_a, col_b, col_c = st.columns([2, 3, 1])
        with col_a:
            new_supplier = st.text_input(
                "Supplier name",
                placeholder="e.g. TechComp Taiwan",
                label_visibility="collapsed"
            )
        with col_b:
            new_notes = st.text_input(
                "Notes (optional)",
                placeholder="e.g. Sole source for PCBs, $2.4M annual spend",
                label_visibility="collapsed"
            )
        with col_c:
            if st.button("Add", type="primary", use_container_width=True):
                if new_supplier.strip():
                    added = add_supplier(new_supplier.strip(), new_notes.strip())
                    if added:
                        st.success(f"Added **{new_supplier}** to watchlist.")
                        st.rerun()
                    else:
                        st.warning(f"**{new_supplier}** is already on the watchlist.")
                else:
                    st.warning("Enter a supplier name.")

        st.markdown(
            "**Tip:** Use the exact supplier names that appear in your incident "
            "reports. The agent matches on partial names too — "
            "e.g. 'TechComp' will match 'TechComp Taiwan'."
        )

    if not watchlist:
        st.info(
            "Your watchlist is empty. Add suppliers above to start tracking them. "
            "Once added, every incident analysis will automatically check if "
            "any watchlisted supplier is involved."
        )
        return

    st.divider()

    # ── Sort controls ─────────────────────────────────────────────
    sort_by = st.radio(
        "Sort by",
        ["Risk score", "Incident count", "Last seen", "Name"],
        horizontal=True,
        index=0
    )
    sort_map = {
        "Risk score":     lambda w: -w["risk_score"],
        "Incident count": lambda w: -w["incident_count"],
        "Last seen":      lambda w: w["last_seen"] or "",
        "Name":           lambda w: w["supplier"].lower(),
    }
    sorted_list = sorted(watchlist, key=sort_map[sort_by])

    # ── Supplier cards ────────────────────────────────────────────
    st.subheader("Tracked suppliers")

    for entry in sorted_list:
        score   = entry["risk_score"] or 0
        fg, bg  = risk_color(score)
        label   = risk_label(score)
        hits    = get_hits_for_supplier(entry["supplier"])
        last    = (entry["last_seen"] or "")[:16].replace("T", " ")

        with st.expander(
            f"**{entry['supplier']}** — {label}  |  "
            f"score: {score}/10  |  "
            f"incidents: {entry['incident_count']}",
            expanded=(score >= 7)
        ):
            col_gauge, col_info, col_hist = st.columns([1, 2, 2])

            with col_gauge:
                risk_gauge(score)
                st.markdown(
                    f'<div style="text-align:center;font-size:12px;'
                    f'color:{fg};font-weight:500">{label}</div>',
                    unsafe_allow_html=True
                )

            with col_info:
                st.markdown(f"**Added:** {entry['added_at'][:10]}")
                if last:
                    st.markdown(f"**Last seen in incident:** {last}")
                st.markdown(f"**Total incidents:** {entry['incident_count']}")

                current_notes = entry.get("notes") or ""
                new_note = st.text_area(
                    "Notes",
                    value=current_notes,
                    height=80,
                    key=f"notes_{entry['supplier']}",
                    placeholder="Sole source? Annual spend? Contract expiry?"
                )
                col_save, col_del = st.columns(2)
                with col_save:
                    if st.button(
                        "Save notes",
                        key=f"save_{entry['supplier']}",
                        use_container_width=True
                    ):
                        update_notes(entry["supplier"], new_note)
                        st.success("Saved.")
                with col_del:
                    if st.button(
                        "Remove",
                        key=f"del_{entry['supplier']}",
                        type="secondary",
                        use_container_width=True
                    ):
                        remove_supplier(entry["supplier"])
                        st.warning(f"Removed **{entry['supplier']}**.")
                        st.rerun()

            with col_hist:
                if hits:
                    st.markdown("**Incident history**")
                    hits_chart(hits)
                    for h in hits[:5]:
                        sev_color = SEV_COLORS.get(h["severity"], "#888")
                        st.markdown(
                            f'<div style="display:flex;justify-content:'
                            f'space-between;align-items:center;padding:4px 0;'
                            f'border-bottom:1px solid rgba(0,0,0,0.06);'
                            f'font-size:12px">'
                            f'<span style="font-family:monospace">'
                            f'{h["incident_id"]}</span>'
                            f'<span style="color:{sev_color};font-weight:500">'
                            f'{h["severity"]}</span>'
                            f'<span style="color:#888">'
                            f'{(h["hit_at"] or "")[:10]}</span>'
                            f'</div>',
                            unsafe_allow_html=True
                        )
                    if len(hits) > 5:
                        st.caption(f"+{len(hits)-5} more incidents")
                else:
                    st.markdown("**No incidents yet**")
                    st.caption(
                        "This supplier hasn't appeared in any "
                        "incident analysis yet. Risk score will "
                        "update automatically when they do."
                    )

    # ── High risk alert ───────────────────────────────────────────
    high_risk = [w for w in watchlist if w["risk_score"] >= 7]
    if high_risk:
        st.divider()
        st.subheader("High risk suppliers requiring attention")
        for w in high_risk:
            fg, bg = risk_color(w["risk_score"])
            st.markdown(
                f'<div style="background:{bg};border-left:4px solid {fg};'
                f'padding:10px 16px;border-radius:0 6px 6px 0;'
                f'margin-bottom:8px">'
                f'<strong>{w["supplier"]}</strong> — '
                f'risk score {w["risk_score"]}/10 — '
                f'{w["incident_count"]} incident(s) — '
                f'last seen {(w["last_seen"] or "")[:10]}'
                f'</div>',
                unsafe_allow_html=True
            )


main()