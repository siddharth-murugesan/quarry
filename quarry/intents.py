"""
Intent taxonomy for Meridian (fictional mid-market SaaS PM tool).

Each intent has:
- id: short identifier
- name: human-readable label
- case: 1 (phrasing gap), 2 (data gap), or 3 (should-be-human)
- volume_pct: % of total conversations
- resolution_rate: % Fin currently resolves
- description: what customers are actually asking about
- backend_hint: for Case 2, which Meridian system holds the answer
"""

INTENTS = [
    # ─── CASE 2: DATA GAP (buried treasure — biggest ROI) ───
    {
        "id": "billing_charges",
        "name": "Billing / invoice questions",
        "case": 2,
        "volume_pct": 11,
        "resolution_rate": 9,
        "description": "Customer wants to know why they were charged a specific amount, when their next invoice is due, or how their bill is calculated.",
        "backend_hint": "Stripe: GET /subscriptions/{account_id}/upcoming_invoice",
    },
    {
        "id": "seat_management",
        "name": "Seat management",
        "case": 2,
        "volume_pct": 7,
        "resolution_rate": 12,
        "description": "Customer wants to know how many seats they have, add or remove seats, or understand seat limits on their plan.",
        "backend_hint": "Meridian API: GET /accounts/{id}/plan + Stripe seat update",
    },
    {
        "id": "account_access",
        "name": "Account / workspace access",
        "case": 2,
        "volume_pct": 8,
        "resolution_rate": 18,
        "description": "Customer cannot log in, is locked out of their workspace, or their account status seems wrong.",
        "backend_hint": "Auth service: GET /users/{email}/status",
    },
    {
        "id": "project_sync",
        "name": "Task / project sync status",
        "case": 2,
        "volume_pct": 6,
        "resolution_rate": 22,
        "description": "Customer reports that changes aren't syncing, projects aren't showing up, or integrations look stale.",
        "backend_hint": "Meridian Core API: GET /workspaces/{id}/sync-status",
    },
    {
        "id": "sso_state",
        "name": "SSO / SAML configuration state",
        "case": 2,
        "volume_pct": 3,
        "resolution_rate": 15,
        "description": "Admin wants to know if SSO is enabled, why users can't log in via SSO, or how their SAML config is set.",
        "backend_hint": "Auth service: GET /accounts/{id}/sso-config",
    },

    # ─── CASE 1: PHRASING GAP (needs Fin tuning, not integrations) ───
    {
        "id": "create_project",
        "name": "How to create a project or workspace",
        "case": 1,
        "volume_pct": 6,
        "resolution_rate": 78,
        "description": "New users asking how to set up their first project, create workspaces, or invite teammates.",
        "backend_hint": None,
    },
    {
        "id": "automations",
        "name": "How to set up automations / workflows",
        "case": 1,
        "volume_pct": 5,
        "resolution_rate": 41,
        "description": "Customer wants to configure automation rules, workflow triggers, or recurring task templates.",
        "backend_hint": None,
    },
    {
        "id": "permissions",
        "name": "Permissions and role explanations",
        "case": 1,
        "volume_pct": 4,
        "resolution_rate": 52,
        "description": "Customer asking why someone can or can't see a project, how roles work, or how to change permissions.",
        "backend_hint": None,
    },
    {
        "id": "integrations_setup",
        "name": "Integrations setup (Slack, GitHub, etc.)",
        "case": 1,
        "volume_pct": 5,
        "resolution_rate": 63,
        "description": "Customer trying to connect Meridian to Slack, GitHub, Google Drive, or similar third-party tools.",
        "backend_hint": None,
    },
    {
        "id": "notifications",
        "name": "Notification settings",
        "case": 1,
        "volume_pct": 3,
        "resolution_rate": 71,
        "description": "Customer wants to change email frequency, mute a project, or fix missing notifications.",
        "backend_hint": None,
    },
    {
        "id": "mobile_app",
        "name": "Mobile app troubleshooting",
        "case": 1,
        "volume_pct": 4,
        "resolution_rate": 38,
        "description": "Customer reporting bugs, crashes, or missing features on the iOS or Android app.",
        "backend_hint": None,
    },

    # ─── CASE 3: SHOULD BE HUMAN (don't automate) ───
    {
        "id": "cancellation_retention",
        "name": "Cancellation with retention signal",
        "case": 3,
        "volume_pct": 4,
        "resolution_rate": 21,
        "description": "Customer expressing frustration, considering competitors, or asking to cancel — high-value retention moment.",
        "backend_hint": None,
    },
    {
        "id": "enterprise_procurement",
        "name": "Enterprise contract / procurement",
        "case": 3,
        "volume_pct": 2,
        "resolution_rate": 15,
        "description": "Procurement teams asking about contracts, security questionnaires, MSAs, or custom pricing.",
        "backend_hint": None,
    },
    {
        "id": "gdpr_compliance",
        "name": "Data export / GDPR / compliance requests",
        "case": 3,
        "volume_pct": 2,
        "resolution_rate": 25,
        "description": "Customer requesting data export, deletion, DPA, or asking compliance-related questions.",
        "backend_hint": None,
    },
    {
        "id": "bug_reports",
        "name": "Bug reports with reproduction steps",
        "case": 3,
        "volume_pct": 5,
        "resolution_rate": 32,
        "description": "Customer submitting a detailed bug report with steps to reproduce, screenshots, or error logs.",
        "backend_hint": None,
    },

    # ─── LONG TAIL (realistic noise) ───
    {
        "id": "praise_feedback",
        "name": "Praise / feedback / thanks",
        "case": 1,
        "volume_pct": 4,
        "resolution_rate": 92,
        "description": "Customer thanking support, giving positive feedback, or sharing feature requests casually.",
        "backend_hint": None,
    },
    {
        "id": "general_howto",
        "name": "General 'how do I...' questions",
        "case": 1,
        "volume_pct": 15,
        "resolution_rate": 74,
        "description": "Well-documented feature questions — how to use a specific view, keyboard shortcuts, basic operations.",
        "backend_hint": None,
    },
    {
        "id": "misc_oneoffs",
        "name": "Miscellaneous / one-off weird questions",
        "case": 3,
        "volume_pct": 6,
        "resolution_rate": 28,
        "description": "Genuinely varied one-off questions that don't fit other categories — legitimate long tail.",
        "backend_hint": None,
    },
]


def total_volume():
    """Sanity check: intent volumes should sum to 100%."""
    return sum(i["volume_pct"] for i in INTENTS)


def weighted_resolution_rate():
    """Sanity check: should land near Meridian's stated 44%."""
    return sum(i["volume_pct"] * i["resolution_rate"] for i in INTENTS) / 100


if __name__ == "__main__":
    print(f"Total intents: {len(INTENTS)}")
    print(f"Total volume: {total_volume()}%")
    print(f"Weighted avg resolution rate: {weighted_resolution_rate():.1f}%")