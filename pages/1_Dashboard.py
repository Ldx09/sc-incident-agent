import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import streamlit as st
import streamlit.components.v1 as components
from utils.database import get_stats, get_all_incidents, delete_incident
from utils.audit import get_audit_stats

st.set_page_config(
    page_title="Incident Dashboard",
    page_icon="📊",
    layout="wide"
)

SEVERITY_ORDER  = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
SEVERITY_COLORS = {
    "CRITICAL": "#A32D2D",
    "HIGH":     "#D85A30",
    "MEDIUM":   "#BA7517",
    "LOW":      "#1D9E75",
}
VULN_COLORS = [
    "#7F77DD","#1D9E75","#D85A30","#378ADD",
    "#BA7517","#A32D2D","#639922","#D4537E",
]
TYPE_COLORS = [
    "#378ADD","#7F77DD","#1D9E75","#D85A30",
    "#BA7517","#639922","#D4537E","#A32D2D",
]


def chart(html: str, height: int = 320):
    components.html(html, height=height, scrolling=False)


def severity_pie(counts: dict):
    labels  = [s for s in SEVERITY_ORDER if s in counts]
    values  = [counts[s] for s in labels]
    colors  = [SEVERITY_COLORS[s] for s in labels]
    html = f"""
<!DOCTYPE html><html><head>
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.js"></script>
</head><body style="margin:0;background:transparent">
<div style="position:relative;width:100%;height:280px">
<canvas id="c"></canvas></div>
<script>
new Chart(document.getElementById('c'),{{
  type:'doughnut',
  data:{{
    labels:{json.dumps(labels)},
    datasets:[{{
      data:{json.dumps(values)},
      backgroundColor:{json.dumps(colors)},
      borderWidth:2,
      borderColor:'#ffffff'
    }}]
  }},
  options:{{
    responsive:true,
    maintainAspectRatio:false,
    plugins:{{
      legend:{{position:'right',labels:{{font:{{size:12}},padding:12}}}},
      tooltip:{{callbacks:{{label:function(c){{
        var t=c.chart.data.datasets[0].data.reduce((a,b)=>a+b,0);
        return c.label+': '+c.raw+' ('+Math.round(c.raw/t*100)+'%)';
      }}}}}}
    }}
  }}
}});
</script></body></html>"""
    chart(html, 300)


def vuln_bar(counts: dict):
    labels = list(counts.keys())
    values = list(counts.values())
    colors = VULN_COLORS[:len(labels)]
    clean  = [l.replace("_", " ").title() for l in labels]
    html = f"""
<!DOCTYPE html><html><head>
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.js"></script>
</head><body style="margin:0;background:transparent">
<div style="position:relative;width:100%;height:300px">
<canvas id="c"></canvas></div>
<script>
new Chart(document.getElementById('c'),{{
  type:'bar',
  data:{{
    labels:{json.dumps(clean)},
    datasets:[{{
      label:'Incidents',
      data:{json.dumps(values)},
      backgroundColor:{json.dumps(colors)},
      borderRadius:4,
      borderSkipped:false
    }}]
  }},
  options:{{
    indexAxis:'y',
    responsive:true,
    maintainAspectRatio:false,
    plugins:{{legend:{{display:false}}}},
    scales:{{
      x:{{ticks:{{stepSize:1}},grid:{{color:'rgba(0,0,0,0.06)'}}}},
      y:{{ticks:{{font:{{size:11}}}}}}
    }}
  }}
}});
</script></body></html>"""
    chart(html, 320)


def type_bar(counts: dict):
    labels = list(counts.keys())
    values = list(counts.values())
    colors = TYPE_COLORS[:len(labels)]
    clean  = [l.replace("_", " ").title() for l in labels]
    html = f"""
<!DOCTYPE html><html><head>
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.js"></script>
</head><body style="margin:0;background:transparent">
<div style="position:relative;width:100%;height:280px">
<canvas id="c"></canvas></div>
<script>
new Chart(document.getElementById('c'),{{
  type:'bar',
  data:{{
    labels:{json.dumps(clean)},
    datasets:[{{
      label:'Count',
      data:{json.dumps(values)},
      backgroundColor:{json.dumps(colors)},
      borderRadius:4,
      borderSkipped:false
    }}]
  }},
  options:{{
    responsive:true,
    maintainAspectRatio:false,
    plugins:{{legend:{{display:false}}}},
    scales:{{
      y:{{ticks:{{stepSize:1}},grid:{{color:'rgba(0,0,0,0.06)'}}}},
      x:{{ticks:{{font:{{size:11}}}}}}
    }}
  }}
}});
</script></body></html>"""
    chart(html, 300)


def risk_timeline(incidents: list):
    if len(incidents) < 2:
        return
    rows   = list(reversed(incidents[:20]))
    labels = [r["incident_id"].split("-")[-1] + " " + r["severity_level"]
              for r in rows]
    values = [r["risk_score_overall"] for r in rows]
    html = f"""
<!DOCTYPE html><html><head>
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.js"></script>
</head><body style="margin:0;background:transparent">
<div style="position:relative;width:100%;height:240px">
<canvas id="c"></canvas></div>
<script>
new Chart(document.getElementById('c'),{{
  type:'line',
  data:{{
    labels:{json.dumps(labels)},
    datasets:[{{
      label:'Risk score',
      data:{json.dumps(values)},
      borderColor:'#D85A30',
      backgroundColor:'rgba(216,90,48,0.08)',
      borderWidth:2,
      pointBackgroundColor:'#D85A30',
      pointRadius:4,
      tension:0.3,
      fill:true
    }}]
  }},
  options:{{
    responsive:true,
    maintainAspectRatio:false,
    plugins:{{legend:{{display:false}}}},
    scales:{{
      y:{{min:0,max:10,ticks:{{stepSize:2}},
         grid:{{color:'rgba(0,0,0,0.06)'}}}},
      x:{{ticks:{{font:{{size:10}},maxRotation:30}}}}
    }}
  }}
}});
</script></body></html>"""
    chart(html, 260)


def financial_bar(incidents: list):
    if not incidents:
        return
    rows   = list(reversed(incidents[:10]))
    labels = [r["incident_id"].split("-")[-1] for r in rows]
    mins   = [r["financial_min"] // 1000 for r in rows]
    maxs   = [(r["financial_max"] - r["financial_min"]) // 1000 for r in rows]
    html = f"""
<!DOCTYPE html><html><head>
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.js"></script>
</head><body style="margin:0;background:transparent">
<div style="position:relative;width:100%;height:260px">
<canvas id="c"></canvas></div>
<script>
new Chart(document.getElementById('c'),{{
  type:'bar',
  data:{{
    labels:{json.dumps(labels)},
    datasets:[
      {{label:'Min ($K)',data:{json.dumps(mins)},
        backgroundColor:'rgba(55,138,221,0.5)',borderRadius:3,borderSkipped:false}},
      {{label:'Additional exposure ($K)',data:{json.dumps(maxs)},
        backgroundColor:'rgba(216,90,48,0.6)',borderRadius:3,borderSkipped:false}}
    ]
  }},
  options:{{
    responsive:true,
    maintainAspectRatio:false,
    plugins:{{legend:{{position:'top',labels:{{font:{{size:11}}}}}}}},
    scales:{{
      x:{{stacked:true,ticks:{{font:{{size:11}}}}}},
      y:{{stacked:true,title:{{display:true,text:'$K',font:{{size:11}}}},
         grid:{{color:'rgba(0,0,0,0.06)'}}}}
    }}
  }}
}});
</script></body></html>"""
    chart(html, 280)

def audit_section(stats: dict):
    """Render the audit trail stats section on the dashboard."""
    import streamlit.components.v1 as components
    import json

    if stats["incidents_audited"] == 0:
        st.info(
            "No audit trails recorded yet. After running an analysis, "
            "scroll to the bottom of the results and mark which actions "
            "you took — they will appear here."
        )
        return

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Incidents audited",    stats["incidents_audited"])
    c2.metric("Actions recorded",     stats["total_actions"])
    c3.metric("Actions taken",        stats["actions_taken"])
    ft = stats["follow_through_pct"]
    ft_color = "normal" if ft >= 60 else "inverse"
    c4.metric("Follow-through rate",  f"{ft}%", delta_color=ft_color)

    st.markdown("")

    col_outcome, col_priority = st.columns(2)

    with col_outcome:
        st.markdown("**Outcome distribution**")
        oc = stats["outcome_counts"]
        if oc:
            labels = list(oc.keys())
            values = list(oc.values())
            label_map = {
                "resolved":           "Resolved",
                "partially_resolved": "Partial",
                "escalated":          "Escalated",
                "ongoing":            "Ongoing",
                "skipped":            "Skipped",
                "not_recorded":       "Not recorded",
            }
            color_map = {
                "resolved":           "#1D9E75",
                "partially_resolved": "#BA7517",
                "escalated":          "#D85A30",
                "ongoing":            "#378ADD",
                "skipped":            "#888888",
                "not_recorded":       "#cccccc",
            }
            clean_labels = [label_map.get(l, l) for l in labels]
            colors       = [color_map.get(l, "#888") for l in labels]
            html = f"""<!DOCTYPE html><html><head>
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.js"></script>
</head><body style="margin:0;background:transparent">
<div style="position:relative;width:100%;height:220px">
<canvas id="oc"></canvas></div>
<script>
new Chart(document.getElementById('oc'),{{
  type:'doughnut',
  data:{{
    labels:{json.dumps(clean_labels)},
    datasets:[{{
      data:{json.dumps(values)},
      backgroundColor:{json.dumps(colors)},
      borderWidth:2,borderColor:'#ffffff'
    }}]
  }},
  options:{{
    responsive:true,maintainAspectRatio:false,
    plugins:{{
      legend:{{position:'right',labels:{{font:{{size:11}},padding:10}}}},
      tooltip:{{callbacks:{{label:function(c){{
        var t=c.chart.data.datasets[0].data.reduce((a,b)=>a+b,0);
        return c.label+': '+c.raw+' ('+Math.round(c.raw/t*100)+'%)';
      }}}}}}
    }}
  }}
}});
</script></body></html>"""
            components.html(html, height=240)
        else:
            st.caption("No outcomes recorded yet.")

    with col_priority:
        st.markdown("**Action follow-through by priority**")
        pr = stats["priority_rates"]
        if pr:
            labels = [f"Action {r['priority']}" for r in pr]
            rates  = [r["rate"] for r in pr]
            colors = [
                "#1D9E75" if r >= 80
                else "#BA7517" if r >= 50
                else "#D85A30"
                for r in rates
            ]
            html = f"""<!DOCTYPE html><html><head>
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.js"></script>
</head><body style="margin:0;background:transparent">
<div style="position:relative;width:100%;height:220px">
<canvas id="pr"></canvas></div>
<script>
new Chart(document.getElementById('pr'),{{
  type:'bar',
  data:{{
    labels:{json.dumps(labels)},
    datasets:[{{
      label:'Take rate %',
      data:{json.dumps(rates)},
      backgroundColor:{json.dumps(colors)},
      borderRadius:4,borderSkipped:false
    }}]
  }},
  options:{{
    responsive:true,maintainAspectRatio:false,
    plugins:{{legend:{{display:false}}}},
    scales:{{
      y:{{min:0,max:100,
        ticks:{{callback:function(v){{return v+'%'}}}},
        grid:{{color:'rgba(0,0,0,0.06)'}}}},
      x:{{ticks:{{font:{{size:11}}}}}}
    }}
  }}
}});
</script></body></html>"""
            components.html(html, height=240)
        else:
            st.caption("No priority data yet.")

    if stats["overall_counts"]:
        st.markdown("**Overall incident outcomes**")
        ov = stats["overall_counts"]
        overall_labels = {
            "resolved":           "Resolved",
            "escalated":          "Escalated",
            "ongoing":            "Ongoing",
            "closed_unresolved":  "Closed unresolved",
        }
        ov_colors = {
            "resolved":           "#1D9E75",
            "escalated":          "#D85A30",
            "ongoing":            "#378ADD",
            "closed_unresolved":  "#A32D2D",
        }
        for status, count in ov.items():
            label = overall_labels.get(status, status)
            color = ov_colors.get(status, "#888")
            pct   = round(count / stats["incidents_audited"] * 100)
            st.markdown(
                f'<div style="display:flex;align-items:center;gap:12px;'
                f'padding:6px 0;border-bottom:1px solid rgba(0,0,0,0.06)">'
                f'<span style="color:{color};font-size:14px">●</span>'
                f'<span style="font-size:13px;flex:1">{label}</span>'
                f'<span style="font-weight:600;font-size:13px">{count}</span>'
                f'<span style="color:#888;font-size:12px;min-width:36px'
                f';text-align:right">{pct}%</span>'
                f'</div>',
                unsafe_allow_html=True
            )
            
        
def main():
    st.title("Incident history dashboard")
    st.caption("Every analysis you run is automatically saved here.")

    if st.button("Refresh data", type="secondary"):
        st.rerun()

    stats    = get_stats()
    total    = stats["total"]
    incidents = stats["recent"]

    if total == 0:
        st.info(
            "No incidents analyzed yet. "
            "Go to the main page, run an analysis, and it will appear here."
        )
        st.page_link("app.py", label="Go to main page", icon="🚨")
        return

    # ── Summary metrics ──────────────────────────────────────────
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total incidents", total)
    c2.metric("Avg risk score", f"{stats['avg_risk']}/10")
    avg_fm = stats["avg_financial_max"]
    c3.metric(
        "Avg max exposure",
        f"${avg_fm/1_000_000:.1f}M" if avg_fm >= 1_000_000
        else f"${avg_fm/1_000:.0f}K"
    )
    crit_high = (
        stats["severity_counts"].get("CRITICAL", 0)
        + stats["severity_counts"].get("HIGH", 0)
    )
    c4.metric("Critical/High", crit_high)
    most_vuln = (
        max(stats["vuln_counts"], key=stats["vuln_counts"].get)
        .replace("_", " ").title()
        if stats["vuln_counts"] else "—"
    )
    c5.metric("Top vulnerability", most_vuln)

    st.divider()

    # ── Charts row 1 ─────────────────────────────────────────────
    col_a, col_b, col_c = st.columns(3)

    with col_a:
        st.subheader("Severity breakdown")
        if stats["severity_counts"]:
            severity_pie(stats["severity_counts"])
        else:
            st.caption("No data yet.")

    with col_b:
        st.subheader("Vulnerability types")
        if stats["vuln_counts"]:
            vuln_bar(stats["vuln_counts"])
        else:
            st.caption("No data yet.")

    with col_c:
        st.subheader("Incident types")
        if stats["type_counts"]:
            type_bar(stats["type_counts"])
        else:
            st.caption("No data yet.")

    st.divider()

    # ── Charts row 2 ─────────────────────────────────────────────
    col_d, col_e = st.columns(2)

    with col_d:
        st.subheader("Risk score over time")
        if len(incidents) >= 2:
            risk_timeline(incidents)
        else:
            st.caption("Run at least 2 analyses to see the trend.")

    with col_e:
        st.subheader("Financial exposure per incident ($K)")
        if incidents:
            financial_bar(incidents)
        else:
            st.caption("No data yet.")

    st.divider()
    st.divider()
    st.subheader("Decision audit trail")
    audit_stats = get_audit_stats()
    audit_section(audit_stats)

    # ── Incident table ────────────────────────────────────────────
    st.subheader("All incidents")

    sev_filter  = st.multiselect(
        "Filter by severity",
        ["CRITICAL", "HIGH", "MEDIUM", "LOW"],
        default=[],
        placeholder="All severities"
    )
    type_filter = st.multiselect(
        "Filter by type",
        list(stats["type_counts"].keys()),
        default=[],
        placeholder="All types",
        format_func=lambda x: x.replace("_", " ").title()
    )

    all_rows = get_all_incidents()
    filtered = all_rows
    if sev_filter:
        filtered = [r for r in filtered if r["severity_level"] in sev_filter]
    if type_filter:
        filtered = [r for r in filtered if r["incident_type"] in type_filter]

    if not filtered:
        st.info("No incidents match your filters.")
    else:
        st.caption(f"Showing {len(filtered)} incident(s)")
        for idx, row in enumerate(filtered):
            sev   = row["severity_level"] or "—"
            color_map = {
                "CRITICAL": "#A32D2D", "HIGH": "#D85A30",
                "MEDIUM": "#BA7517",   "LOW": "#1D9E75"
            }
            sev_color = color_map.get(sev, "#888")

            with st.expander(
                f"**{row['incident_id']}** — {row['title'] or 'Untitled'}"
                f"  |  {sev}  |  {(row['created_at'] or '')[:16]}"
            ):
                left, right = st.columns([2, 1])

                with left:
                    st.markdown(f"**Type:** `{row['incident_type']}`")
                    st.markdown(f"**Region:** {row['affected_region'] or '—'}")
                    st.markdown(
                        f"**Vulnerability:** "
                        f"`{row['vulnerability_type'] or '—'}`"
                    )
                    st.markdown(
                        f"**Recovery:** {row['recovery_timeline'] or '—'}"
                    )
                    if row.get("primary_root_cause"):
                        st.markdown("**Primary root cause:**")
                        st.markdown(
                            f'<div style="border-left:3px solid {sev_color};'
                            f'padding:8px 12px;background:var(--color-background-secondary);'
                            f'font-size:13px;border-radius:0 4px 4px 0">'
                            f'{row["primary_root_cause"]}</div>',
                            unsafe_allow_html=True
                        )
                    if row.get("executive_summary"):
                        st.markdown("**Executive summary:**")
                        st.info(row["executive_summary"])

                with right:
                    st.markdown(
                        f'<div style="text-align:center;padding:12px;'
                        f'background:var(--color-background-secondary);'
                        f'border-radius:8px;margin-bottom:8px">'
                        f'<div style="font-size:28px;font-weight:600;'
                        f'color:{sev_color}">'
                        f'{row["risk_score_overall"] or "—"}/10</div>'
                        f'<div style="font-size:11px;color:#888">Risk score</div>'
                        f'</div>',
                        unsafe_allow_html=True
                    )
                    fin_min = row.get("financial_min") or 0
                    fin_max = row.get("financial_max") or 0

                    def fmt(v):
                        if v >= 1_000_000:
                            return f"${v/1_000_000:.1f}M"
                        elif v >= 1_000:
                            return f"${v/1_000:.0f}K"
                        return f"${v:,}"

                    st.markdown(
                        f'<div style="text-align:center;padding:10px;'
                        f'background:var(--color-background-secondary);'
                        f'border-radius:8px">'
                        f'<div style="font-size:15px;font-weight:600">'
                        f'{fmt(fin_min)} – {fmt(fin_max)}</div>'
                        f'<div style="font-size:11px;color:#888">'
                        f'Financial exposure</div></div>',
                        unsafe_allow_html=True
                    )

                    st.markdown("")
                    if st.button(
                        "Delete",
                        key=f"del_{row['incident_id']}_{idx}",
                        type="secondary"
                    ):
                        delete_incident(row["incident_id"])
                        st.success(f"Deleted {row['incident_id']}")
                        st.rerun()


main()