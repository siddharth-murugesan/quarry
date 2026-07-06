"""Stage 3: Render the HTML report from analysis.json."""

import json
from collections import defaultdict
from datetime import datetime

import plotly.graph_objects as go
from jinja2 import Environment, FileSystemLoader

from quarry.paths import ANALYSIS, REPORT, ROOT

TEMPLATE_DIR = ROOT / "quarry" / "templates"

CASE_LABELS = {
    1: "Phrasing gap (retrain)",
    2: "Data gap (Custom Action)",
    3: "Should be human (route)",
    4: "Already working",
}

CASE_COLORS = {
    1: "#e8a838",
    2: "#0a4d8f",
    3: "#b04a4a",
    4: "#6b7280",
}

# Meridian's assumed current human-support burn — for the "% of burn" headline.
# 42,000 conversations/month × 56% escalated × $8 × 12 = ~$2.25M
MERIDIAN_ANNUAL_BURN = 2_257_920


def build_case_summary(clusters: list[dict]) -> list[dict]:
    """Aggregate cluster stats by case for the executive summary table."""
    agg = defaultdict(lambda: {"clusters": 0, "volume_pct": 0.0, "savings": 0})
    for c in clusters:
        if c["case"] is None:
            continue
        agg[c["case"]]["clusters"] += 1
        agg[c["case"]]["volume_pct"] += c["volume_pct"]
        agg[c["case"]]["savings"] += c["estimated_annual_savings_usd"]

    return [
        {
            "case": case,
            "label": CASE_LABELS[case],
            "clusters": v["clusters"],
            "volume_pct": v["volume_pct"],
            "savings": v["savings"],
        }
        for case, v in sorted(agg.items())
    ]


def build_chart(clusters: list[dict]) -> str:
    """Bubble chart: resolution_rate x savings, size = volume, color = case."""
    fig = go.Figure()

    # Only label the top-N by savings to avoid overlaps.
    LABEL_TOP_N = 5
    top_savings_ids = {
        c["cluster_id"]
        for c in sorted(clusters, key=lambda x: x["estimated_annual_savings_usd"], reverse=True)[:LABEL_TOP_N]
    }

    by_case = defaultdict(list)
    for c in clusters:
        if c["case"] is None:
            continue
        by_case[c["case"]].append(c)

    for case in sorted(by_case):
        cs = by_case[case]
        labels = [c["label"] if c["cluster_id"] in top_savings_ids else "" for c in cs]
        fig.add_trace(go.Scatter(
            x=[c["resolution_rate"] for c in cs],
            y=[c["estimated_annual_savings_usd"] for c in cs],
            mode="markers+text",
            marker=dict(
                size=[c["size"] for c in cs],
                sizemode="area",
                sizeref=0.15,
                color=CASE_COLORS[case],
                line=dict(width=1, color="white"),
            ),
            text=labels,
            textposition="top center",
            textfont=dict(size=10),
            name=f"Case {case} — {CASE_LABELS[case]}",
            hovertemplate=(
                "<b>%{customdata}</b><br>"
                "Resolution rate: %{x:.1f}%<br>"
                "Est. annual savings: $%{y:,.0f}<extra></extra>"
            ),
            customdata=[c["label"] for c in cs],
        ))

    fig.update_layout(
        xaxis=dict(title="Current Fin resolution rate (%)", range=[-5, 105]),
        yaxis=dict(title="Estimated annual savings ($)"),
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5),
        margin=dict(t=20, b=80, l=60, r=20),
        plot_bgcolor="#fafbfc",
    )
    return fig.to_json()

def render_report() -> None:
    with ANALYSIS.open() as f:
        analysis = json.load(f)

    clusters = analysis["clusters"]
    meta = analysis["meta"]

    env = Environment(loader=FileSystemLoader(TEMPLATE_DIR), autoescape=True)
    template = env.get_template("report.html")

    html = template.render(
        generated_at=datetime.now().strftime("%B %d, %Y"),
        meta=meta,
        clusters=clusters,
        case_summary=build_case_summary(clusters),
        savings_pct_of_burn=round(
            100 * meta["total_estimated_annual_savings_usd"] / MERIDIAN_ANNUAL_BURN
        ),
        chart_json=build_chart(clusters),
    )

    with REPORT.open("w") as f:
        f.write(html)

    print(f"Report written to {REPORT}")