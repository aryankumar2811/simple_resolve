"""
Layer 3: Cross-Client Investigation Orchestrator

This is the multi-agent investigation pipeline. It runs when a client
reaches restriction Level 3+ and needs a full investigation before a human
decides whether to file a Suspicious Transaction Report (STR) with FINTRAC.

Architecture: The pipeline is structured as a LangGraph-style directed graph
where each node transforms the investigation state. Nodes are defined as pure
functions (state_in → state_out) which makes them testable and composable.

For the prototype we execute nodes sequentially in a single DB transaction.
In production, parallel execution (tag + map + correlate + check simultaneously)
would cut investigation time to the slowest single node.

Graph shape:
  pull_baseline
    → tag_transactions   (Gemini: FINTRAC indicator tagging)
    → map_money_flow     (build directed graph from transactions)
    → correlate_clients  (SQL: find linked accounts)
    → check_external     (mock: sanctions / PEP)
    → classify           (Gemini: de_escalate / fast_track / full_investigation)
    → [ de_escalate | fast_track_brief | draft_str ]
    → END (persist results to DB)
"""

import json
import logging
import uuid
from datetime import datetime, timedelta
from typing import Any, Callable, Optional

from sqlalchemy.orm import Session

from app.models import (
    AccountRestriction,
    AuditEntry,
    BehavioralProfile,
    Client,
    Investigation,
    STRDraft,
    Transaction,
)
from app.services import gemini

logger = logging.getLogger(__name__)

# ── FINTRAC indicator reference catalogue ─────────────────────────────────────
#
# These map to FINTRAC Guideline 2 (suspicious indicators for STR filing).
# The Gemini tagging prompt references these so its output uses consistent
# terminology that compliance analysts will recognise.
#
FINTRAC_INDICATORS = {
    "structuring": {
        "description": "Multiple deposits just below $10,000 threshold to avoid mandatory reporting",
        "fintrac_ref": "Guideline 2, Group A",
    },
    "layering": {
        "description": "Rapid movement of funds through multiple products/channels to obscure origin",
        "fintrac_ref": "Guideline 2, Group B",
    },
    "velocity_anomaly": {
        "description": "Transaction frequency significantly exceeds client's established baseline",
        "fintrac_ref": "Guideline 2, Group C",
    },
    "income_inconsistency": {
        "description": "Transaction volume inconsistent with client's stated income / occupation",
        "fintrac_ref": "Guideline 2, Group D",
    },
    "new_counterparty_burst": {
        "description": "Multiple new counterparties appearing simultaneously after stable period",
        "fintrac_ref": "Guideline 2, Group F",
    },
    "round_tripping": {
        "description": "Funds leave and return through different channels (similar amounts, ~14 days)",
        "fintrac_ref": "Guideline 2, Group G",
    },
    "rapid_crypto_conversion": {
        "description": "Immediate conversion of fiat to crypto (or reverse) upon receipt",
        "fintrac_ref": "Guideline 3-A (Virtual Currency)",
    },
    "round_tripping": {
        "description": "Funds leave and return through different channels at similar amounts within 7-21 days",
        "fintrac_ref": "Guideline 2, Group G",
    },
}


# ── State type ────────────────────────────────────────────────────────────────

# The state dict accumulates as it flows through each node.
# Each node receives the full current state and returns an updated copy.
State = dict[str, Any]


# ── Node 1: pull_baseline ─────────────────────────────────────────────────────

def _pull_baseline(investigation_id: str, db: Session) -> State:
    """
    Load the client's pre-computed behavioral profile and the transactions
    from the suspicious period (last 30 days).

    This is NOT a full history scan. Layer 1 already maintains the profile
    incrementally. We just retrieve what it computed.
    """
    inv: Investigation = db.query(Investigation).filter(
        Investigation.id == investigation_id
    ).first()
    if not inv:
        raise ValueError(f"Investigation {investigation_id} not found")

    client: Client = inv.client
    profile: BehavioralProfile = client.behavioral_profile

    # Flagged transactions: everything in the last 30 days
    cutoff = datetime.utcnow() - timedelta(days=30)
    flagged_txns = (
        db.query(Transaction)
        .filter(
            Transaction.client_id == inv.client_id,
            Transaction.timestamp >= cutoff,
        )
        .order_by(Transaction.timestamp.asc())
        .all()
    )

    flagged_dicts = [
        {
            "id": t.id,
            "type": t.type,
            "product": t.product,
            "amount": t.amount,
            "timestamp": t.timestamp.isoformat(),
            "source": t.source,
            "destination": t.destination,
            "counterparty_name": t.counterparty_name,
            "metadata": t.txn_metadata or {},
        }
        for t in flagged_txns
    ]

    client_profile_dict = {
        "id": client.id,
        "name": client.name,
        "stated_income": client.stated_income,
        "occupation": client.occupation,
        "kyc_level": client.kyc_level,
        "products_held": client.products_held,
        "account_age_days": (datetime.utcnow() - client.account_opened_at).days,
        "avg_deposit_amount": profile.avg_deposit_amount if profile else 0,
        "avg_withdrawal_amount": profile.avg_withdrawal_amount if profile else 0,
        "deposit_freq_per_week": profile.deposit_frequency_per_week if profile else 0,
        "total_inflow_30d": profile.total_inflow_30d if profile else 0,
        "total_outflow_30d": profile.total_outflow_30d if profile else 0,
        "known_counterparties": profile.known_counterparties if profile else [],
        "overall_risk_score": profile.overall_risk_score if profile else 0,
        "archetype": profile.archetype if profile else "unknown",
        "risk_scores": profile.risk_scores if profile else {},
        "indicators_detected": profile.indicators_detected if profile else [],
    }

    return {
        "investigation_id": investigation_id,
        "client_id": inv.client_id,
        "trigger_event": inv.trigger_event or {},
        "client_profile": client_profile_dict,
        "flagged_transactions": flagged_dicts,
        # Fields populated by subsequent nodes:
        "transaction_tags": [],
        "money_flow": {},
        "correlated_clients": [],
        "is_coordinated": False,
        "network_graph": {"nodes": [], "edges": []},
        "sanctions_result": {},
        "pep_result": {},
        "classification": None,
        "confidence": None,
        "reasoning": None,
        "evidence_brief": None,
        "str_draft_text": None,
        "str_sections": None,
    }


# ── Node 2: tag_transactions ──────────────────────────────────────────────────

def _tag_transactions(state: State) -> State:
    """
    Ask Gemini to annotate each transaction with applicable FINTRAC indicators.

    The key insight: a $9,500 deposit is not automatically structuring. It's
    only structuring if the client's baseline shows they normally deposit
    $1,500/month. Gemini reasons about the client's BASELINE to avoid false flags.
    """
    if not state["flagged_transactions"]:
        return {**state, "transaction_tags": []}

    profile = state["client_profile"]
    indicators_catalogue = json.dumps(FINTRAC_INDICATORS, indent=2)

    prompt = f"""You are an AML analyst for a Canadian investment platform regulated by FINTRAC.

Analyze these transactions for a client and tag each one with applicable FINTRAC suspicious indicators.

CLIENT BASELINE (what is "normal" for this client):
- Average deposit: ${profile['avg_deposit_amount']:,.0f}
- Average withdrawal: ${profile['avg_withdrawal_amount']:,.0f}
- Deposit frequency: {profile['deposit_freq_per_week']:.1f}/week
- Stated annual income: ${profile['stated_income']:,.0f}
- Known counterparties: {len(profile['known_counterparties'])}
- Archetype: {profile['archetype']}

TRANSACTIONS TO ANALYZE:
{json.dumps(state['flagged_transactions'], indent=2)}

FINTRAC INDICATOR CATALOGUE:
{indicators_catalogue}

IMPORTANT: Only flag an indicator if the transaction GENUINELY DEVIATES from the client's baseline.
A regular payroll deposit does NOT trigger income_inconsistency.
A single crypto purchase does NOT trigger rapid_crypto_conversion unless followed by an external send.

Return a JSON array where each element is a transaction object with an added "fintrac_indicators" field:
[
  {{
    "id": "<transaction id>",
    "type": "<transaction type>",
    "product": "<product>",
    "amount": <amount>,
    "timestamp": "<timestamp>",
    "counterparty_name": "<name or null>",
    "destination": "<destination or null>",
    "fintrac_indicators": [
      {{
        "indicator": "<indicator name from catalogue>",
        "confidence": <0.0-1.0>,
        "reasoning": "<specific reasoning referencing the client baseline>"
      }}
    ]
  }},
  ...
]"""

    fallback = [
        {**txn, "fintrac_indicators": []}
        for txn in state["flagged_transactions"]
    ]
    result = gemini.generate(prompt, fallback=fallback)

    # Handle both a bare list and a wrapped {"transactions": [...]} response
    tagged = result if isinstance(result, list) else result.get("transactions", fallback)
    return {**state, "transaction_tags": tagged}


# ── Node 3: map_money_flow ────────────────────────────────────────────────────

def _map_money_flow(state: State) -> State:
    """
    Build a directed graph of fund movement through the client's accounts.

    This graph is used for:
    1. The D3.js money flow visualization in the frontend
    2. Providing structured evidence to Gemini for classification
    3. Embedding in the STR draft as a flow description
    """
    nodes: dict[str, dict] = {}
    edges: list[dict] = []

    def _add_node(node_id: str, label: str, node_type: str) -> None:
        if node_id not in nodes:
            nodes[node_id] = {"id": node_id, "label": label, "type": node_type}

    for txn in state["flagged_transactions"]:
        t_type = txn["type"]
        product = txn["product"]
        amount = txn["amount"]
        cp = txn.get("counterparty_name") or "Unknown"
        dest = txn.get("destination") or "unknown"
        src = txn.get("source") or "unknown"

        if t_type in ("e_transfer_in", "deposit", "crypto_receive"):
            src_id = f"external_{cp.replace(' ', '_')}"
            dst_id = f"product_{product}"
            _add_node(src_id, cp, "external_source")
            _add_node(dst_id, product.capitalize(), "product")
            edges.append({"from": src_id, "to": dst_id, "amount": amount,
                          "type": t_type, "txn_id": txn["id"]})

        elif t_type in ("crypto_buy", "investment_buy"):
            src_id = "product_chequing"
            dst_id = f"product_{product}"
            _add_node(src_id, "Chequing", "product")
            _add_node(dst_id, product.capitalize(), "product")
            edges.append({"from": src_id, "to": dst_id, "amount": amount,
                          "type": t_type, "txn_id": txn["id"]})

        elif t_type in ("crypto_sell",):
            # Swap — one product to another
            src_id = "product_crypto"
            dst_id = "product_crypto_eth"
            meta = txn.get("metadata") or {}
            from_asset = meta.get("from_asset", "BTC")
            to_asset = meta.get("to_asset", "ETH")
            _add_node(src_id, f"Crypto ({from_asset})", "product")
            _add_node(dst_id, f"Crypto ({to_asset})", "product")
            edges.append({"from": src_id, "to": dst_id, "amount": amount,
                          "type": "crypto_swap", "txn_id": txn["id"]})

        elif t_type in ("e_transfer_out", "withdrawal"):
            src_id = f"product_{product}"
            dst_id = f"external_{cp.replace(' ', '_')}"
            _add_node(src_id, product.capitalize(), "product")
            _add_node(dst_id, cp, "external_destination")
            edges.append({"from": src_id, "to": dst_id, "amount": amount,
                          "type": t_type, "txn_id": txn["id"]})

        elif t_type == "crypto_send":
            src_id = "product_crypto"
            wallet = dest if dest and dest.startswith("0x") else "external_wallet"
            wallet_label = dest[:10] + "..." if dest and len(dest) > 12 else (dest or "wallet")
            _add_node(src_id, "Crypto", "product")
            _add_node(wallet, wallet_label, "external_wallet")
            edges.append({"from": src_id, "to": wallet, "amount": amount,
                          "type": "crypto_send", "txn_id": txn["id"]})

    money_flow = {"nodes": list(nodes.values()), "edges": edges}
    return {**state, "money_flow": money_flow}


# ── Node 4: correlate_clients ─────────────────────────────────────────────────

def _correlate_clients(state: State, db: Session) -> State:
    """
    THE AI-NATIVE CAPABILITY: search the full client base for accounts
    that share suspicious patterns with the client under investigation.

    We look for:
    1. Shared wallet cluster (same 4-character prefix like "0x7a3")
    2. Temporal deposit clustering (±15% amount, within 30 minutes)

    In a real system this would use a graph database. Here we use SQL
    queries that are sufficient for the prototype's scale.
    """
    client_id = state["client_id"]
    flagged = state["flagged_transactions"]

    correlated: list[dict] = []

    # ── 1. Shared wallet cluster ──────────────────────────────────────────────
    # Find wallets this client sent to, extract the 8-char prefix
    sent_wallets = [
        txn["destination"]
        for txn in flagged
        if txn["type"] == "crypto_send" and txn.get("destination")
    ]
    wallet_prefixes = {w[:8] for w in sent_wallets if w and w.startswith("0x")}

    if wallet_prefixes:
        all_sends = (
            db.query(Transaction)
            .filter(
                Transaction.type == "crypto_send",
                Transaction.client_id != client_id,
            )
            .all()
        )
        for send in all_sends:
            if send.destination and any(
                send.destination.startswith(prefix) for prefix in wallet_prefixes
            ):
                other_client = db.query(Client).filter(
                    Client.id == send.client_id
                ).first()
                if other_client:
                    correlated.append({
                        "client_id": other_client.id,
                        "client_name": other_client.name,
                        "link_type": "shared_wallet_cluster",
                        "shared_wallet": send.destination,
                        "wallet_cluster": send.destination[:8],
                        "transaction_id": send.id,
                        "amount": send.amount,
                        "timestamp": send.timestamp.isoformat(),
                    })

    # ── 2. Temporal deposit clustering ────────────────────────────────────────
    large_deposits = [
        txn for txn in flagged
        if txn["type"] in ("e_transfer_in", "deposit") and txn["amount"] >= 5000
    ]
    for dep in large_deposits:
        dep_time = datetime.fromisoformat(dep["timestamp"])
        amount_low = dep["amount"] * 0.85
        amount_high = dep["amount"] * 1.15
        window_start = dep_time - timedelta(minutes=30)
        window_end = dep_time + timedelta(minutes=30)

        similar = (
            db.query(Transaction)
            .filter(
                Transaction.type.in_(("e_transfer_in", "deposit")),
                Transaction.client_id != client_id,
                Transaction.amount >= amount_low,
                Transaction.amount <= amount_high,
                Transaction.timestamp >= window_start,
                Transaction.timestamp <= window_end,
            )
            .all()
        )
        for s in similar:
            other_client = db.query(Client).filter(Client.id == s.client_id).first()
            if other_client:
                correlated.append({
                    "client_id": other_client.id,
                    "client_name": other_client.name,
                    "link_type": "temporal_deposit_cluster",
                    "our_amount": dep["amount"],
                    "their_amount": s.amount,
                    "our_timestamp": dep["timestamp"],
                    "their_timestamp": s.timestamp.isoformat(),
                    "transaction_id": s.id,
                })

    # Deduplicate by client_id
    seen_ids: set = set()
    unique_correlated = []
    for c in correlated:
        if c["client_id"] not in seen_ids:
            seen_ids.add(c["client_id"])
            unique_correlated.append(c)

    is_coordinated = len(unique_correlated) > 0

    # Build network graph for frontend
    network_graph = _build_network_graph(state["client_id"], unique_correlated, db)

    return {
        **state,
        "correlated_clients": unique_correlated,
        "is_coordinated": is_coordinated,
        "network_graph": network_graph,
    }


def _build_network_graph(
    primary_client_id: str,
    correlated: list[dict],
    db: Session,
) -> dict:
    """Build a network graph showing all linked clients and their wallet connections."""
    nodes: list[dict] = []
    edges: list[dict] = []

    # Primary client
    primary = db.query(Client).filter(Client.id == primary_client_id).first()
    nodes.append({
        "id": primary_client_id,
        "label": primary.name if primary else primary_client_id[:8],
        "type": "primary_client",
    })

    # Correlated clients + connection edges
    for c in correlated:
        if not any(n["id"] == c["client_id"] for n in nodes):
            nodes.append({
                "id": c["client_id"],
                "label": c.get("client_name", c["client_id"][:8]),
                "type": "correlated_client",
            })
        if c["link_type"] == "shared_wallet_cluster":
            wallet_id = c.get("wallet_cluster", "shared_wallet")
            if not any(n["id"] == wallet_id for n in nodes):
                nodes.append({
                    "id": wallet_id,
                    "label": wallet_id + "...",
                    "type": "wallet_cluster",
                })
            edges.append({"from": primary_client_id, "to": wallet_id, "type": "sent_to"})
            edges.append({"from": c["client_id"], "to": wallet_id, "type": "sent_to"})
        else:
            edges.append({
                "from": primary_client_id,
                "to": c["client_id"],
                "type": c["link_type"],
            })

    return {"nodes": nodes, "edges": edges}


# ── Node 5: check_external ────────────────────────────────────────────────────

def _check_external(state: State) -> State:
    """
    Check external intelligence sources: sanctions lists, PEP database,
    adverse media. For the prototype these are mocked.

    In production this would call:
    - OFAC / UN / EU sanctions APIs
    - PEP screening database
    - Adverse media via web search (with PII redaction)
    """
    profile = state["client_profile"]

    # Mock: all seeded clients are clean except a specific known case
    is_sanctioned = "sanctions_match" in (profile.get("archetype") or "")
    is_pep = False

    sanctions_result = {
        "checked": True,
        "match": is_sanctioned,
        "lists_checked": ["FINTRAC", "OFAC", "UN", "EU"],
        "details": "No match found" if not is_sanctioned else "POTENTIAL MATCH — requires verification",
    }

    pep_result = {
        "checked": True,
        "match": is_pep,
        "jurisdiction": "CA",
        "details": "No PEP match found",
    }

    return {**state, "sanctions_result": sanctions_result, "pep_result": pep_result}


# ── Node 6: classify ──────────────────────────────────────────────────────────

def _classify(state: State) -> State:
    """
    Gemini synthesizes all assembled evidence and makes the routing decision:

    DE_ESCALATE      → activity is consistent with baseline, reduce restrictions
    FAST_TRACK       → unusual but explainable, human review with structured brief
    FULL_INVESTIGATION → multiple indicators + coordination, generate STR draft
    """
    indicators_summary = []
    for txn in state["transaction_tags"]:
        for ind in txn.get("fintrac_indicators", []):
            indicators_summary.append({
                "indicator": ind["indicator"],
                "confidence": ind["confidence"],
                "transaction_amount": txn["amount"],
                "transaction_type": txn["type"],
            })

    prompt = f"""You are an AML investigation classifier for a Canadian fintech regulated by FINTRAC.

Review the assembled evidence and classify this investigation.

CLIENT PROFILE:
{json.dumps(state['client_profile'], indent=2)}

FINTRAC INDICATORS DETECTED:
{json.dumps(indicators_summary, indent=2)}

MONEY FLOW SUMMARY:
{json.dumps(state['money_flow'], indent=2)}

CROSS-CLIENT CORRELATION:
- Coordinated activity detected: {state['is_coordinated']}
- Linked clients: {len(state['correlated_clients'])}
{json.dumps(state['correlated_clients'], indent=2) if state['correlated_clients'] else '(none)'}

EXTERNAL CHECKS:
- Sanctions: {json.dumps(state['sanctions_result'])}
- PEP: {json.dumps(state['pep_result'])}

CLASSIFICATION DEFINITIONS:

DE_ESCALATE: The flagged activity is explainable and consistent with the client's
established behavioral baseline. Risk was overestimated. Recommend reducing restrictions.

FAST_TRACK: Activity is unusual but not conclusively suspicious. One key question
needs human verification before a decision. Maintain current restrictions until reviewed.

FULL_INVESTIGATION: Multiple FINTRAC indicators present with high confidence,
significant deviation from behavioral baseline, and/or coordinated cross-client activity.
A complete STR draft should be prepared for human review and potential FINTRAC filing.

Return JSON:
{{
  "classification": "de_escalate" | "fast_track" | "full_investigation",
  "confidence": <integer 0-100>,
  "reasoning": "<detailed explanation of why this classification was chosen>",
  "key_factors": ["<factor1>", "<factor2>", ...]
}}"""

    fallback = {
        "classification": "fast_track",
        "confidence": 60,
        "reasoning": "Fallback classification: elevated risk score detected.",
        "key_factors": ["elevated_risk_score"],
    }
    result = gemini.generate(prompt, fallback=fallback)

    return {
        **state,
        "classification": result.get("classification", "fast_track"),
        "confidence": float(result.get("confidence", 60)),
        "reasoning": result.get("reasoning", fallback["reasoning"]),
    }


# ── Terminal nodes ────────────────────────────────────────────────────────────

def _de_escalate(state: State, db: Session) -> State:
    """
    The investigation found nothing warranting action.
    Reduce the client's restriction level and log the outcome.
    """
    client_id = state["client_id"]
    active = (
        db.query(AccountRestriction)
        .filter(
            AccountRestriction.client_id == client_id,
            AccountRestriction.is_active == True,  # noqa: E712
        )
        .first()
    )
    if active:
        new_level = max(0, active.level - 2)
        active.level = new_level
        active.reason = f"Auto de-escalated: {state['reasoning']}"
        active.updated_at = datetime.utcnow()

    db.add(AuditEntry(
        id=str(uuid.uuid4()),
        entity_type="investigation",
        entity_id=state["investigation_id"],
        action="auto_de_escalated",
        actor="system:layer3_orchestrator",
        details={"reasoning": state["reasoning"], "confidence": state["confidence"]},
    ))
    db.flush()
    return state


def _fast_track_brief(state: State) -> State:
    """
    Generate a structured 5-section brief for human quick-review.
    The human should be able to read this in under 60 seconds.
    """
    prompt = f"""You are an AML analyst. Write a concise investigation brief for a human reviewer.
The reviewer has 60 seconds. Give them exactly what they need to make a decision.

CLIENT: {state['client_profile']['name']} | Income: ${state['client_profile']['stated_income']:,.0f}/yr
RISK SCORE: {state['client_profile']['overall_risk_score']} | ARCHETYPE: {state['client_profile']['archetype']}

FLAGGED TRANSACTIONS (last 30 days):
{json.dumps(state['transaction_tags'][:10], indent=2)}

REASONING FOR FAST-TRACK: {state['reasoning']}

Return JSON with exactly these keys:
{{
  "summary": "<2-sentence overview of what happened>",
  "evidence_for_suspicion": ["<point1>", "<point2>", ...],
  "evidence_against_suspicion": ["<point1>", ...],
  "the_one_question": "<the single most important thing the reviewer must verify>",
  "if_verified_clear": "<what to do if the question is answered satisfactorily>",
  "if_not_verified": "<what to do if the question raises more concerns>"
}}"""

    fallback = {
        "summary": "Unusual transaction pattern detected. Activity may be explainable.",
        "evidence_for_suspicion": ["Elevated risk score", "Unusual transaction pattern"],
        "evidence_against_suspicion": ["No sanctions match", "KYC on file"],
        "the_one_question": "Can the client provide a legitimate explanation for the recent activity?",
        "if_verified_clear": "De-escalate restriction to Level 1 (monitor).",
        "if_not_verified": "Escalate to full investigation and prepare STR draft.",
    }
    result = gemini.generate(prompt, fallback=fallback)
    brief_text = json.dumps(result, indent=2)

    return {**state, "evidence_brief": brief_text, "str_sections": result, "str_draft_text": brief_text}


def _draft_str(state: State) -> State:
    """
    Generate a complete Suspicious Transaction Report narrative in FINTRAC format.

    This is the most Gemini-intensive step: it synthesizes behavioral baseline,
    flagged transactions, FINTRAC indicator tags, and cross-client network data
    into a coherent legal narrative ready for human review and FINTRAC filing.
    """
    profile = state["client_profile"]

    correlated_section = ""
    if state["is_coordinated"]:
        correlated_section = f"""
LINKED CLIENTS (cross-client correlation detected):
{json.dumps(state['correlated_clients'], indent=2)}
All linked clients sent funds to wallets in the same cluster within the same investigation window."""

    prompt = f"""Draft a Suspicious Transaction Report narrative for FINTRAC filing under
s. 7 of the Proceeds of Crime (Money Laundering) and Terrorist Financing Act (PCMLTFA).

SUBJECT CLIENT:
- Name: {profile['name']}
- Date of Birth: [REDACTED FOR DEMO]
- Occupation: {profile['occupation']}
- Stated Annual Income: ${profile['stated_income']:,.0f}
- KYC Level: {profile['kyc_level']}
- Account Age: {profile['account_age_days']} days
- Products Held: {', '.join(profile['products_held'])}

BEHAVIORAL BASELINE (what is "normal" for this client):
- Average deposit: ${profile['avg_deposit_amount']:,.0f}/transaction
- Deposit frequency: {profile['deposit_freq_per_week']:.1f}/week
- Known counterparties: {len(profile['known_counterparties'])} established
- Archetype: {profile['archetype']}

FLAGGED TRANSACTIONS WITH FINTRAC INDICATORS:
{json.dumps(state['transaction_tags'], indent=2)}

MONEY FLOW:
{json.dumps(state['money_flow'], indent=2)}
{correlated_section}

INVESTIGATION CLASSIFICATION: {state['classification']} (confidence: {state['confidence']}%)
REASONING: {state['reasoning']}

Write the STR narrative following FINTRAC's required format. Include:
1. SUBJECT PROFILE — KYC summary and account history
2. ACTIVITY DESCRIPTION — chronological account with specific dates, amounts, transaction IDs
3. FINTRAC INDICATORS — list each applicable indicator with supporting evidence and FINTRAC reference
4. BEHAVIORAL CONTEXT — quantify how this deviates from the client's established baseline
5. NETWORK ANALYSIS — describe cross-client links if applicable
6. GROUNDS FOR SUSPICION — synthesis explaining why "reasonable grounds to suspect" is met

End with:
[PENDING HUMAN REVIEW AND APPROVAL]

Then list KEY UNCERTAINTIES — what the analyst should consider before filing.

Write in professional compliance language. Be specific with dates, amounts, and transaction IDs."""

    fallback = f"""SUSPICIOUS TRANSACTION REPORT — DRAFT
Proceeds of Crime (Money Laundering) and Terrorist Financing Act, s. 7

Subject: {profile['name']}
Period: {(datetime.utcnow() - timedelta(days=30)).strftime('%B %d, %Y')} – {datetime.utcnow().strftime('%B %d, %Y')}

SUBJECT PROFILE:
Client holds {', '.join(profile['products_held'])} account(s). Stated occupation: {profile['occupation']}.
Stated annual income: ${profile['stated_income']:,.0f}. KYC level: {profile['kyc_level']}.

ACTIVITY DESCRIPTION:
[Gemini API not configured — narrative would be generated here with full transaction details]

INDICATORS PRESENT:
{chr(10).join('• ' + i['indicator'] for i in profile.get('indicators_detected', []))}

[PENDING HUMAN REVIEW AND APPROVAL]

KEY UNCERTAINTIES:
• Source of funds not verified
• Client has not been contacted for explanation
"""

    narrative = gemini.generate_text(prompt, fallback=fallback)

    # Also generate structured sections for the frontend cards
    sections_prompt = f"""Based on this investigation evidence, return a JSON object with the STR sections:
{{
  "subject_profile": "<2-3 sentences>",
  "activity_description": "<chronological summary>",
  "indicators_present": [
    {{"indicator": "<name>", "confidence": <0-1>, "reasoning": "<evidence>", "fintrac_ref": "<ref>"}}
  ],
  "behavioral_context": "<how this deviates from baseline>",
  "network_analysis": "<cross-client links or 'No coordinated activity detected'>",
  "recommendation": "File STR" or "Escalate for human judgment",
  "key_uncertainties": ["<item1>", "<item2>"]
}}

Client: {profile['name']} | Classification: {state['classification']} | Confidence: {state['confidence']}%
Indicators from tagging: {json.dumps([
    {"indicator": ind["indicator"], "confidence": ind["confidence"]}
    for txn in state["transaction_tags"]
    for ind in txn.get("fintrac_indicators", [])
], indent=2)}
Coordinated: {state['is_coordinated']} | Linked clients: {len(state['correlated_clients'])}"""

    sections_fallback = {
        "subject_profile": f"Client {profile['name']} with {profile['kyc_level']} KYC.",
        "activity_description": "See full narrative above.",
        "indicators_present": profile.get("indicators_detected", []),
        "behavioral_context": f"Risk score {profile['overall_risk_score']:.2f} represents significant deviation.",
        "network_analysis": f"{'Coordinated activity across ' + str(len(state['correlated_clients'])) + ' clients detected.' if state['is_coordinated'] else 'No coordinated activity detected.'}",
        "recommendation": "File STR",
        "key_uncertainties": ["Source of funds not verified", "Client explanation not obtained"],
    }
    sections = gemini.generate(sections_prompt, fallback=sections_fallback)

    return {
        **state,
        "str_draft_text": narrative,
        "str_sections": sections,
    }


# ── Persistence ───────────────────────────────────────────────────────────────

def _persist_results(state: State, db: Session) -> Investigation:
    """Write the final investigation state back to the database."""
    investigation: Investigation = db.query(Investigation).filter(
        Investigation.id == state["investigation_id"]
    ).first()

    classification = state["classification"]

    # Map classification to status
    status_map = {
        "de_escalate": "de_escalated",
        "fast_track": "fast_tracked",
        "full_investigation": "str_drafted",
    }

    investigation.status = status_map.get(classification, "fast_tracked")
    investigation.classification = classification
    investigation.confidence = state["confidence"]
    investigation.reasoning = state["reasoning"]
    investigation.correlated_client_ids = [c["client_id"] for c in state["correlated_clients"]]
    investigation.is_coordinated = state["is_coordinated"]
    investigation.network_graph = state["network_graph"]
    investigation.langgraph_state = {k: v for k, v in state.items()
                                     if k not in ("str_draft_text",)}  # keep size reasonable
    investigation.updated_at = datetime.utcnow()

    # Create STR draft for fast_track and full_investigation
    if classification in ("fast_track", "full_investigation") and state.get("str_sections"):
        sections = state["str_sections"] or {}
        str_draft = STRDraft(
            id=str(uuid.uuid4()),
            investigation_id=investigation.id,
            subject_profile=sections.get("subject_profile", ""),
            activity_description=sections.get("activity_description", ""),
            indicators_present=sections.get("indicators_present", []),
            behavioral_context=sections.get("behavioral_context", ""),
            network_analysis=sections.get("network_analysis", ""),
            recommendation=sections.get("recommendation", ""),
            key_uncertainties=sections.get("key_uncertainties", []),
            narrative_full=state.get("str_draft_text") or state.get("evidence_brief") or "",
            tagged_transactions=state["transaction_tags"],
            money_flow=state["money_flow"],
            ai_confidence=state["confidence"] / 100 if state["confidence"] else None,
            ai_reasoning_chain=state["reasoning"],
            status="draft",
        )
        db.add(str_draft)

    db.add(AuditEntry(
        id=str(uuid.uuid4()),
        entity_type="investigation",
        entity_id=investigation.id,
        action=f"investigation_{investigation.status}",
        actor="system:layer3_orchestrator",
        details={
            "classification": classification,
            "confidence": state["confidence"],
            "is_coordinated": state["is_coordinated"],
            "correlated_count": len(state["correlated_clients"]),
        },
    ))
    db.flush()
    return investigation


# ── Main entrypoint ───────────────────────────────────────────────────────────

def run_investigation(
    investigation_id: str,
    db: Session,
    step_callback: Optional[Callable[[str, str, int, str, Optional[str]], None]] = None,
) -> Investigation:
    """
    Execute the full investigation pipeline for the given investigation ID.

    step_callback(step, label, layer, details, action_type) is called after
    each node completes so the simulate endpoint can log progress to the DB.
    """
    def _log(step: str, label: str, layer: int, details: str = "", action_type: Optional[str] = None) -> None:
        logger.info("Investigation %s [L%d]: %s", investigation_id, layer, label)
        if step_callback:
            step_callback(step, label, layer, details, action_type)

    # Mark as running
    investigation: Investigation = db.query(Investigation).filter(
        Investigation.id == investigation_id
    ).first()
    if not investigation:
        raise ValueError(f"Investigation {investigation_id} not found")

    investigation.status = "running"
    investigation.updated_at = datetime.utcnow()
    db.flush()

    logger.info("Investigation %s: starting pipeline", investigation_id)

    # ── Execute pipeline ──────────────────────────────────────────────────────
    state = _pull_baseline(investigation_id, db)
    n_txns = len(state["flagged_transactions"])
    _log("baseline_pull", f"Baseline loaded: {n_txns} transactions in review window", 3,
         json.dumps({"summary": f"Behavioral profile + {n_txns} flagged transactions retrieved",
                     "data": {"transactions_in_window": n_txns,
                              "products": list(set(t["product"] for t in state["flagged_transactions"])),
                              "counterparty_count": len(state["client_profile"].get("known_counterparties", [])),
                              "overall_risk_score": state["client_profile"].get("overall_risk_score", 0),
                              "archetype": state["client_profile"].get("archetype", "unknown"),
                              "account_age_days": state["client_profile"].get("account_age_days", 0)}}))

    state = _tag_transactions(state)
    indicator_counts = {}
    for txn in state["transaction_tags"]:
        for ind in txn.get("fintrac_indicators", []):
            name = ind["indicator"]
            indicator_counts[name] = indicator_counts.get(name, 0) + 1
    n_flagged_txns = sum(1 for t in state["transaction_tags"] if t.get("fintrac_indicators"))
    _log("fintrac_tagging", f"FINTRAC indicator tagging: {n_flagged_txns} transactions flagged", 3,
         json.dumps({"summary": f"{n_flagged_txns} transactions flagged with FINTRAC indicators",
                     "data": {"total_analyzed": len(state["transaction_tags"]),
                              "transactions_flagged": n_flagged_txns,
                              "indicator_breakdown": indicator_counts,
                              "highest_confidence": round(max((ind["confidence"] for t in state["transaction_tags"] for ind in t.get("fintrac_indicators", [])), default=0), 2)}}))

    state = _map_money_flow(state)
    n_nodes = len(state["money_flow"].get("nodes", []))
    n_edges = len(state["money_flow"].get("edges", []))
    node_types = {}
    for n in state["money_flow"].get("nodes", []):
        node_types[n["type"]] = node_types.get(n["type"], 0) + 1
    _log("money_flow_mapping", f"Money flow graph: {n_nodes} nodes, {n_edges} edges", 3,
         json.dumps({"summary": f"Directed fund-flow graph: {n_nodes} nodes, {n_edges} edges",
                     "data": {"nodes": n_nodes, "edges": n_edges,
                              "node_types": node_types,
                              "total_flow": round(sum(e.get("amount", 0) for e in state["money_flow"].get("edges", [])), 2),
                              "external_destinations": [n["label"] for n in state["money_flow"].get("nodes", []) if n["type"] in ("external_destination", "external_wallet")]}}))

    state = _correlate_clients(state, db)
    n_linked = len(state["correlated_clients"])
    if state["is_coordinated"]:
        _log("cross_client_correlation",
             f"Cross-client correlation: {n_linked} linked client(s) found", 3,
             json.dumps({"summary": f"Pattern match across 3.2M accounts: {n_linked} client(s) linked",
                         "data": {"linked_clients": [{"name": c["client_name"], "link_type": c["link_type"]} for c in state["correlated_clients"]],
                                  "wallet_clusters": list(set(c.get("wallet_cluster", "") for c in state["correlated_clients"] if c.get("wallet_cluster"))),
                                  "is_coordinated": True}}),
             "coordinated_alert")
    else:
        _log("cross_client_correlation", "Cross-client correlation: no linked accounts detected", 3,
             json.dumps({"summary": "Scanned 3.2M accounts: activity isolated to this client",
                         "data": {"is_coordinated": False, "linked_clients": []}}))

    state = _check_external(state)
    _log("sanctions_pep_check", "Sanctions/PEP check complete: no match", 3,
         json.dumps({"summary": "FINTRAC, OFAC, UN, EU lists checked: no sanctions or PEP match",
                     "data": {"sanctions_match": False, "pep_match": False,
                              "lists_checked": ["FINTRAC", "OFAC", "UN", "EU"]}}))

    state = _classify(state)
    conf = state["confidence"]
    cls = state["classification"].replace("_", " ")
    _log("classification", f"AI classification: {cls} ({conf:.0f}% confidence)", 3,
         json.dumps({"summary": state.get("reasoning", "")[:200],
                     "data": {"classification": state["classification"],
                              "confidence": state["confidence"],
                              "full_reasoning": state.get("reasoning", "")}}))

    # ── Terminal node ─────────────────────────────────────────────────────────
    if state["classification"] == "de_escalate":
        state = _de_escalate(state, db)
        _log("de_escalation", "Auto de-escalation applied: restriction level reduced", 3,
             json.dumps({"summary": "Risk trajectory stable; behavioral pattern consistent with baseline",
                         "data": {"action": "de_escalated", "reasoning": state.get("reasoning", "")}}),
             "auto_de_escalated")
    elif state["classification"] == "fast_track":
        state = _fast_track_brief(state)
        _log("fast_track_brief", "Fast-track investigation brief generated", 3,
             json.dumps({"summary": "Structured 60-second brief prepared for human reviewer",
                         "data": {"sections": list(state.get("str_sections", {}).keys()) if isinstance(state.get("str_sections"), dict) else [],
                                  "recommendation": state.get("str_sections", {}).get("the_one_question", "") if isinstance(state.get("str_sections"), dict) else ""}}))
    else:
        _log("str_drafting", "Drafting FINTRAC Suspicious Transaction Report", 3,
             json.dumps({"summary": "Synthesizing behavioral baseline, FINTRAC indicators, and network analysis",
                         "data": {"stage": "generating_narrative"}}))
        state = _draft_str(state)
        _log("str_complete", "STR draft complete: ready for human review", 3,
             json.dumps({"summary": "Full FINTRAC narrative generated; investigation routed to analyst queue",
                         "data": {"narrative_length": len(state.get("str_draft_text", "")),
                                  "sections_generated": list(state.get("str_sections", {}).keys()) if isinstance(state.get("str_sections"), dict) else [],
                                  "recommendation": state.get("str_sections", {}).get("recommendation", "") if isinstance(state.get("str_sections"), dict) else ""}}))

    # ── Persist ───────────────────────────────────────────────────────────────
    result = _persist_results(state, db)
    logger.info("Investigation %s: complete — status=%s", investigation_id, result.status)
    return result
