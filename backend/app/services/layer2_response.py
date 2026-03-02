"""
Layer 2: Graduated Response Engine

This is where the AI-native behaviour begins in earnest.

Given a risk event (a client whose risk score has crossed a threshold),
the engine calls Gemini to reason about *which* capabilities to restrict
and *which* to leave untouched — something rules engines cannot do.

Key principle: the response should be PROPORTIONAL and SCOPED.
A crypto layering trigger → restrict crypto, leave chequing alone.
An income inconsistency trigger → step-up auth on large inflows, not a full freeze.

The scope reasoning is a language task: it requires understanding the
semantic relationship between the trigger and each account capability.
"""

import json
import logging
import uuid
from datetime import datetime

from sqlalchemy.orm import Session

from app.models import AccountRestriction, AuditEntry, BehavioralProfile, Client
from app.services import gemini
from app.services.layer1_behavioral import response_level_for_score

logger = logging.getLogger(__name__)

# ── Fallback responses (used when Gemini is unavailable) ─────────────────────

_FALLBACKS: dict[str, dict] = {
    # ── Auto-resolve: one-time salary spike from known employer ──────────────
    "salary_spike": {
        "level": 0,
        "restricted_capabilities": [],
        "allowed_capabilities": ["all_standard"],
        "client_message": (
            "Our system flagged an unusual deposit but determined it matches your "
            "regular employer. No action required — your account is fully accessible."
        ),
        "reasoning": (
            "Auto-resolved: deposit originates from a known employer counterparty. "
            "Pattern is consistent with a one-time bonus or RRSP contribution. "
            "No restrictions applied."
        ),
    },
    # ── Minor freeze: structuring-like pattern but below L3 threshold ────────
    "minor_structuring": {
        "level": 2,
        "restricted_capabilities": ["e_transfer_in_large_unverified", "e_transfer_out_new"],
        "allowed_capabilities": [
            "chequing_deposit", "e_transfer_in_known", "bill_payment",
            "investment_buy", "investment_sell",
        ],
        "client_message": (
            "We've added a verification step for large e-transfers from new sources. "
            "All other account features are working normally."
        ),
        "reasoning": (
            "Structuring-like pattern detected but confidence below investigation threshold. "
            "Step-up auth applied on e-transfers as a guardrail."
        ),
    },
    # ── Mule account: many inbound senders → single crypto outbound ──────────
    "mule_pattern": {
        "level": 3,
        "restricted_capabilities": [
            "crypto_send_external", "crypto_buy", "e_transfer_out_new",
        ],
        "allowed_capabilities": ["chequing_deposit", "bill_payment", "e_transfer_in_known"],
        "client_message": (
            "We've temporarily restricted certain outbound transfers pending a "
            "security review. All deposit and standard payment features remain active."
        ),
        "reasoning": (
            "Mule account pattern: many new inbound senders with rapid outbound crypto consolidation. "
            "Restricting all outbound crypto and new-counterparty transfers."
        ),
    },
    # ── Coordinated minor participant: linked but lower exposure ─────────────
    "coordinated_minor": {
        "level": 2,
        "restricted_capabilities": ["crypto_send_external"],
        "allowed_capabilities": [
            "chequing_deposit", "e_transfer_in", "e_transfer_out_known",
            "bill_payment", "crypto_buy",
        ],
        "client_message": (
            "We've temporarily paused external crypto transfers as a security precaution. "
            "All other account features are available."
        ),
        "reasoning": (
            "Account linked to a coordinated wallet cluster but with lower exposure. "
            "Targeted restriction on external crypto sends only."
        ),
    },
    "structuring_crypto_layering": {
        "level": 3,
        "restricted_capabilities": ["crypto_send_external", "crypto_buy", "crypto_sell"],
        "allowed_capabilities": [
            "chequing_deposit", "e_transfer_in", "e_transfer_out_known",
            "bill_payment", "investment_buy", "investment_sell",
        ],
        "client_message": (
            "We've temporarily paused external crypto transfers while we verify "
            "some recent activity. Your chequing account, investments, and all "
            "other services are working normally. We'll update you within 24 hours."
        ),
        "reasoning": (
            "Fallback: crypto trigger detected. Restricting crypto capabilities only "
            "to preserve proportionality."
        ),
    },
    "crypto_layering": {
        "level": 3,
        "restricted_capabilities": ["crypto_send_external", "crypto_buy", "crypto_sell"],
        "allowed_capabilities": [
            "chequing_deposit", "e_transfer_in", "bill_payment",
        ],
        "client_message": (
            "We've temporarily paused external crypto transfers pending a "
            "verification review. All other account features remain available."
        ),
        "reasoning": "Fallback: crypto layering detected. Restricting crypto only.",
    },
    "income_inconsistency": {
        "level": 2,
        "restricted_capabilities": ["e_transfer_in_large_unverified"],
        "allowed_capabilities": [
            "chequing_deposit", "e_transfer_in_known", "bill_payment", "e_transfer_out",
        ],
        "client_message": (
            "For your security, we've added a verification step for large incoming "
            "transfers from new sources. All other account features are working normally."
        ),
        "reasoning": "Fallback: income inconsistency detected. Step-up auth on large inflows.",
    },
    "coordinated_crypto": {
        "level": 3,
        "restricted_capabilities": ["crypto_send_external", "crypto_buy"],
        "allowed_capabilities": ["chequing_deposit", "e_transfer_in", "bill_payment"],
        "client_message": (
            "We've temporarily paused external crypto transfers pending a "
            "verification review. All other account features remain available."
        ),
        "reasoning": "Fallback: coordinated crypto activity. Restricting crypto sends.",
    },
}

_DEFAULT_FALLBACK = {
    "level": 2,
    "restricted_capabilities": [],
    "allowed_capabilities": ["all_standard"],
    "client_message": (
        "We've added extra security checks on your account. "
        "Please contact support if you have questions."
    ),
    "reasoning": "Fallback: default guardrail applied due to elevated risk score.",
}


# ── Prompt construction ───────────────────────────────────────────────────────

def _build_scope_prompt(client: Client, profile: BehavioralProfile, trigger_type: str) -> str:
    indicators = [i["indicator"] for i in (profile.indicators_detected or [])]
    return f"""You are the Graduated Response Engine for SimpleResolve, a Canadian investment platform.

A risk event has been detected for a client. Your task is to determine the PROPORTIONAL response.

CLIENT CONTEXT:
- Products held: {json.dumps(client.products_held)}
- Stated annual income: ${client.stated_income:,.0f}
- KYC level: {client.kyc_level}
- Account age: {(datetime.utcnow() - client.account_opened_at).days} days

RISK PROFILE:
- Overall risk score: {profile.overall_risk_score:.2f} (0.0 = clean, 1.0 = high risk)
- Per-product scores: {json.dumps(profile.risk_scores)}
- Archetype: {profile.archetype} ({profile.archetype_trajectory})
- Trend: {profile.risk_trend}
- FINTRAC indicators: {json.dumps(indicators)}
- 30-day inflow: ${profile.total_inflow_30d:,.0f}
- 30-day outflow: ${profile.total_outflow_30d:,.0f}
- Known counterparties: {len(profile.known_counterparties or [])}

TRIGGER: {trigger_type}

RESPONSE LEVELS:
0 = BASELINE: No restrictions
1 = MONITOR: Enhanced logging only, no client impact
2 = GUARDRAIL: Step-up authentication for specific high-risk operations only
3 = RESTRICT: Block specific capabilities; all unrelated capabilities remain accessible
4 = FREEZE: Full account lock — ONLY for confirmed account takeover or exact sanctions match

RULES:
1. NEVER restrict capabilities unrelated to the trigger. Crypto trigger → chequing stays open.
2. Level 4 MUST NOT be triggered by a risk score alone. Requires confirmed ATO or sanctions hit.
3. restricted_capabilities must name only the specific operations being blocked.
4. allowed_capabilities must explicitly list what remains accessible.
5. client_message must be honest, specific about what still works, and professionally worded.
6. reasoning must explain WHY this scope is proportional to the trigger.

Return a JSON object with exactly these keys:
{{
  "level": <integer 0-4>,
  "restricted_capabilities": [<string>, ...],
  "allowed_capabilities": [<string>, ...],
  "client_message": "<message to display to the client>",
  "reasoning": "<internal explanation of proportionality decision>"
}}"""


# ── Core function ─────────────────────────────────────────────────────────────

def determine_response(
    client_id: str,
    trigger_type: str,
    db: Session,
    trigger_event: dict | None = None,
    enqueue_investigation: bool = True,
) -> AccountRestriction:
    """
    Layer 2 main entry point.

    1. Loads the client's behavioral profile from Layer 1
    2. Calls Gemini to reason about scope-proportional response
    3. Upserts the AccountRestriction record
    4. If level ≥ 3, signals Layer 3 to open an investigation
    5. Writes an audit entry
    """
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise ValueError(f"Client {client_id} not found")

    profile = (
        db.query(BehavioralProfile)
        .filter(BehavioralProfile.client_id == client_id)
        .first()
    )
    if not profile:
        raise ValueError(f"No behavioral profile for client {client_id}. Run Layer 1 first.")

    # ── Gemini scope reasoning ────────────────────────────────────────────────
    prompt = _build_scope_prompt(client, profile, trigger_type)
    fallback = _FALLBACKS.get(trigger_type, _DEFAULT_FALLBACK)
    result = gemini.generate(prompt, fallback=fallback)

    level: int = int(result.get("level", fallback["level"]))
    restricted: list = result.get("restricted_capabilities", fallback["restricted_capabilities"])
    allowed: list = result.get("allowed_capabilities", fallback["allowed_capabilities"])
    client_message: str = result.get("client_message", fallback["client_message"])
    reasoning: str = result.get("reasoning", fallback["reasoning"])

    # ── Deactivate previous active restriction ────────────────────────────────
    (
        db.query(AccountRestriction)
        .filter(
            AccountRestriction.client_id == client_id,
            AccountRestriction.is_active == True,  # noqa: E712
        )
        .update({"is_active": False})
    )

    # ── Create new restriction ────────────────────────────────────────────────
    restriction = AccountRestriction(
        id=str(uuid.uuid4()),
        client_id=client_id,
        level=level,
        restricted_capabilities=restricted,
        allowed_capabilities=allowed,
        reason=f"Risk score {profile.overall_risk_score:.2f} — trigger: {trigger_type}",
        client_message=client_message,
        gemini_reasoning=reasoning,
        trigger_type=trigger_type,
        trigger_event=trigger_event,
        is_active=True,
        triggered_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(restriction)
    db.flush()

    # ── Audit ─────────────────────────────────────────────────────────────────
    db.add(AuditEntry(
        id=str(uuid.uuid4()),
        entity_type="restriction",
        entity_id=client_id,
        action=f"restriction_level_{level}_applied",
        actor="system:layer2_response_engine",
        details={
            "trigger_type": trigger_type,
            "level": level,
            "risk_score": profile.overall_risk_score,
            "restricted": restricted,
        },
    ))
    db.flush()

    # ── If Level ≥ 3 → open an investigation (deferred, avoids circular import) ──
    if level >= 3 and enqueue_investigation:
        _open_investigation(client_id, trigger_type, trigger_event, level, db)

    return restriction


def _open_investigation(
    client_id: str,
    trigger_type: str,
    trigger_event: dict | None,
    response_level: int,
    db: Session,
) -> None:
    """
    Create an open Investigation record so Layer 3 can pick it up.
    Imported here to avoid circular dependency at module load time.
    """
    from app.models import Investigation

    investigation = Investigation(
        id=str(uuid.uuid4()),
        client_id=client_id,
        trigger_event={
            "trigger_type": trigger_type,
            "response_level": response_level,
            **(trigger_event or {}),
        },
        response_level=response_level,
        status="open",
    )
    db.add(investigation)
    db.flush()

    db.add(AuditEntry(
        id=str(uuid.uuid4()),
        entity_type="investigation",
        entity_id=investigation.id,
        action="investigation_opened",
        actor="system:layer2_response_engine",
        details={"trigger_type": trigger_type, "response_level": response_level},
    ))
    db.flush()


def apply_override(
    client_id: str,
    new_level: int,
    reason: str,
    analyst: str,
    db: Session,
) -> AccountRestriction:
    """Human analyst overrides the restriction level."""
    (
        db.query(AccountRestriction)
        .filter(
            AccountRestriction.client_id == client_id,
            AccountRestriction.is_active == True,  # noqa: E712
        )
        .update({"is_active": False})
    )

    restriction = AccountRestriction(
        id=str(uuid.uuid4()),
        client_id=client_id,
        level=new_level,
        restricted_capabilities=[],
        allowed_capabilities=["all_standard"],
        reason=reason,
        client_message="Your account has been updated by our compliance team.",
        trigger_type="human_override",
        is_active=True,
        triggered_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(restriction)

    db.add(AuditEntry(
        id=str(uuid.uuid4()),
        entity_type="restriction",
        entity_id=client_id,
        action=f"restriction_override_level_{new_level}",
        actor=f"human:{analyst}",
        details={"new_level": new_level, "reason": reason},
    ))
    db.flush()
    return restriction
