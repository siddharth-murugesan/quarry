"""Stage 2: Business analysis of clustered conversations."""

import json
from collections import defaultdict

from quarry.paths import CLUSTERS, CLUSTER_LABELS, PROCESSED_DIR

# ─── Constants (all in USD) ────────────────────────────────
HUMAN_HANDLE_COST = 8.00   # fully-loaded cost of one human-handled conversation
FIN_OUTCOME_FEE = 0.99     # what Fin charges per resolved outcome
NET_SAVINGS_PER_RESOLUTION = HUMAN_HANDLE_COST - FIN_OUTCOME_FEE  # $7.01

# Meridian's real monthly conversation volume (from our scenario design)
MONTHLY_CONVERSATION_VOLUME = 42_000

# Realistic capture rates: what fraction of a cluster's currently-escalated
# conversations we'd actually convert to Fin resolutions after the fix.
# Grounded in the observation that automation rarely captures 100% of a
# cluster — edge cases and ambiguous phrasings always escape.
CAPTURE_RATE_BY_CASE: dict[int, float] = {
    1: 0.40,  # phrasing gap (retrain): moves the needle, doesn't clear it
    2: 0.70,  # data gap (Custom Action): high effectiveness where data exists
    3: 0.00,  # should be human: no automation attempted
    4: 0.00,  # already fine: nothing to do
}

# ─── Case classification (the FDE judgment layer) ──────────
# case: 1 = phrasing gap, 2 = data gap, 3 = should be human, 4 = already fine
CLUSTER_CASE_MAP: dict[int, dict] = {
    0: {
        "case": 2,
        "fix": "Wire a Custom Action to the Auth service: `GET /accounts/{id}/sso-config`. Return current SAML config state, IdP metadata URL, and last-successful-auth timestamp so Fin can answer 'is SSO set up?' and 'why can't user X log in via SSO?' without human escalation.",
    },
    1: {
        "case": 1,
        "fix": "Retrain Fin on Slack integration troubleshooting. Add specific phrasing variants for common failure modes (workspace mismatch, bot not invited to channel, OAuth token expired). Consider a targeted help article if none exists.",
    },
    2: {
        "case": 1,
        "fix": "Retrain Fin on Google Drive integration setup. Common failure modes: shared drive vs personal drive permissions, org-level restrictions on third-party apps. Consider a step-by-step help article.",
    },
    3: {
        "case": 4,
        "fix": "No action needed. Fin resolves these appropriately as short acknowledgements.",
    },
    4: {
        "case": 3,
        "fix": "DO NOT automate. Route to retention team on detection of churn signals (competitor mentions, 'thinking of leaving', extended frustration). A 5-minute conversation with a retention specialist can save a multi-thousand-dollar account.",
    },
    5: {
        "case": 2,
        "fix": "Wire a Custom Action to Stripe: `GET /subscriptions/{account_id}/upcoming_invoice`. Return line items, proration details, and next-charge date. Highest-ROI single fix in this analysis — customers cannot get this answer from a help article because it requires live account-specific data.",
    },
    6: {
        "case": 2,
        "fix": "Wire two Custom Actions: (a) Meridian API `GET /accounts/{id}/plan` returning current seat count and limit; (b) Stripe seat-adjustment endpoint for self-service seat additions. Combine with a Procedure so Fin can handle both 'how many seats do I have?' and 'add 5 more seats' end-to-end.",
    },
    7: {
        "case": 3,
        "fix": "Route to account management. Procurement and compliance documentation requests are relationship touchpoints — mishandling them creates deal risk. Fin can acknowledge and hand off, but should not attempt to answer.",
    },
    8: {
        "case": 3,
        "fix": "Route to compliance team. GDPR/data-export requests carry legal exposure and jurisdictional nuance. Attempting to automate creates regulatory risk that far exceeds the human-handling cost.",
    },
    9: {
        "case": 1,
        "fix": "Retrain Fin on mobile-specific troubleshooting phrasings (iOS vs Android, offline sync issues, push notification failures). Consider a mobile-specific help section.",
    },
    10: {
        "case": 1,
        "fix": "Retrain Fin on notification settings — high volume (n=83) but reasonable resolution rate. Focus on the specific failure modes: users who describe missing notifications rather than asking how to change them.",
    },
    11: {
        "case": 1,
        "fix": "Retrain Fin on permissions and role explanations. Complex multi-part questions (‘why can X see project Y but not project Z') are the current failure mode. Consider a decision-tree Procedure.",
    },
    12: {
        "case": 1,
        "fix": "Mostly working. Marginal gains available by adding phrasing variants for enterprise onboarding scenarios (SSO-first signups, invited-vs-inviter flows).",
    },
    13: {
        "case": 1,
        "fix": "Retrain Fin on automation setup. Failure mode: users describe *what they want* rather than *what to configure*. Add examples that translate business goals into Meridian automation primitives.",
    },
    14: {
        "case": 2,
        "fix": "Wire a Custom Action to Meridian Core API: `GET /workspaces/{id}/sync-status` returning last-sync timestamp and any pending queue for third-party integrations. Distinguish 'sync stuck' from 'expected delay' from 'legitimate bug'.",
    },
    -1: {
        "case": 4,
        "fix": "Noise bucket — genuinely long-tail one-off questions. No systematic fix; existing human escalation is appropriate.",
    },
}


# ─── Loading + core computation ────────────────────────────
def load_clusters() -> list[dict]:
    with CLUSTERS.open() as f:
        return [json.loads(line) for line in f]


def load_labels() -> dict:
    with CLUSTER_LABELS.open() as f:
        return json.load(f)


def compute_cluster_stats(rows: list[dict]) -> dict[int, dict]:
    """Per-cluster: size, resolution rate, escalated count."""
    stats: dict[int, dict] = defaultdict(lambda: {"size": 0, "resolved": 0})
    for r in rows:
        cid = r["cluster_id"]
        stats[cid]["size"] += 1
        if r["was_resolved_by_fin"]:
            stats[cid]["resolved"] += 1

    for cid, s in stats.items():
        s["resolution_rate"] = 100 * s["resolved"] / s["size"]
        s["escalated"] = s["size"] - s["resolved"]
    return dict(stats)


def estimate_annual_savings(
    escalated_in_cluster: int,
    total_dataset_size: int,
    case: int | None,
) -> float:
    """
    Extrapolate: after applying the case-appropriate fix, how much does
    Meridian save per year? Applies a per-case capture rate to avoid
    the naive assumption that 100% of escalations get automated.
    """
    if case is None:
        return 0.0
    capture = CAPTURE_RATE_BY_CASE.get(case, 0.0)
    escalated_share = escalated_in_cluster / total_dataset_size
    monthly_escalations = escalated_share * MONTHLY_CONVERSATION_VOLUME
    captured_per_month = monthly_escalations * capture
    return captured_per_month * NET_SAVINGS_PER_RESOLUTION * 12

# ─── Public entry point ────────────────────────────────────
def run_analysis() -> dict:
    rows = load_clusters()
    labels = load_labels()
    stats = compute_cluster_stats(rows)
    total = len(rows)

    analysis = {
        "meta": {
            "total_conversations_analyzed": total,
            "monthly_conversation_volume": MONTHLY_CONVERSATION_VOLUME,
            "human_handle_cost": HUMAN_HANDLE_COST,
            "fin_outcome_fee": FIN_OUTCOME_FEE,
            "net_savings_per_resolution": NET_SAVINGS_PER_RESOLUTION,
            "capture_rates": CAPTURE_RATE_BY_CASE,
        },
        "clusters": [],
    }

    for cid_str, label_info in labels.items():
        cid = int(cid_str)
        s = stats.get(cid, {"size": 0, "resolved": 0, "resolution_rate": 0, "escalated": 0})
        case_info = CLUSTER_CASE_MAP.get(cid, {"case": None, "fix": "Unclassified — review manually."})

        savings = estimate_annual_savings(s["escalated"], total, case_info["case"])


        analysis["clusters"].append({
            "cluster_id": cid,
            "label": label_info["label"],
            "description": label_info["description"],
            "size": s["size"],
            "volume_pct": round(100 * s["size"] / total, 1),
            "resolution_rate": round(s["resolution_rate"], 1),
            "escalated": s["escalated"],
            "case": case_info["case"],
            "recommended_fix": case_info["fix"],
            "estimated_annual_savings_usd": round(savings),
            "capture_rate": CAPTURE_RATE_BY_CASE.get(case_info["case"], 0.0),
        })

    analysis["clusters"].sort(
        key=lambda c: c["estimated_annual_savings_usd"],
        reverse=True,
    )

    total_savings = sum(c["estimated_annual_savings_usd"] for c in analysis["clusters"])
    analysis["meta"]["total_estimated_annual_savings_usd"] = round(total_savings)

    return analysis