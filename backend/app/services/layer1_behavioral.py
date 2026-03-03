"""
Layer 1: Continuous Behavioral Intelligence

This service maintains a living behavioral profile for every client.
It computes a structured risk fingerprint from transaction history that
all downstream layers (graduated response, investigation orchestrator) consume.

In a production system this would run after every incoming transaction event.
In the prototype it is called:
  - by the seed script to pre-compute profiles
  - via GET /clients/{id}/profile/recompute to refresh on demand
"""

from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.models import BehavioralProfile, Client, Transaction

# ── Constants ─────────────────────────────────────────────────────────────────

REPORTING_THRESHOLD = 10_000.0   # FINTRAC Large Cash Transaction threshold (CAD)
STRUCTURING_BAND = 0.20           # within 20% below = structuring suspicion

# Risk score → response level mapping consumed by Layer 2
LEVEL_THRESHOLDS = {
    0: 0.00,   # baseline: no restrictions
    1: 0.40,   # monitor: enhanced logging
    2: 0.60,   # guardrail: step-up auth
    3: 0.75,   # restrict: capability-scoped block
    4: 0.95,   # freeze: full lock (reserved for confirmed ATO / sanctions)
}


def response_level_for_score(score: float) -> int:
    """Map an overall risk score to a graduated response level."""
    if score >= LEVEL_THRESHOLDS[4]:
        return 4
    if score >= LEVEL_THRESHOLDS[3]:
        return 3
    if score >= LEVEL_THRESHOLDS[2]:
        return 2
    if score >= LEVEL_THRESHOLDS[1]:
        return 1
    return 0


# ── FINTRAC indicator detectors ───────────────────────────────────────────────

def _detect_structuring(deposits: list) -> float:
    """
    Multiple deposits in the band [8000, 10000) within 7 days suggest
    deliberate structuring to avoid the $10,000 reporting threshold.
    """
    window = datetime.utcnow() - timedelta(days=7)
    near = [
        t for t in deposits
        if t.timestamp >= window
        and REPORTING_THRESHOLD * (1 - STRUCTURING_BAND) <= t.amount < REPORTING_THRESHOLD
    ]
    if len(near) >= 3:
        return min(0.95, 0.75 + len(near) * 0.05)
    if len(near) == 2:
        return 0.70
    if len(near) == 1:
        return 0.35
    return 0.0


def _detect_layering(transactions: list) -> float:
    """
    Funds traversing 3+ distinct products within 24 hours indicates
    layering to obscure the origin of funds.
    """
    by_day: dict = {}
    for t in transactions:
        day = t.timestamp.date()
        by_day.setdefault(day, set()).add(t.product)

    max_products = max((len(v) for v in by_day.values()), default=0)
    if max_products >= 3:
        return min(0.95, 0.72 + (max_products - 3) * 0.08)
    return 0.0


def _detect_rapid_crypto_conversion(transactions: list) -> float:
    """
    Fiat received and crypto sent to an external wallet within 4 hours
    is a strong indicator of using crypto as a laundering rail.
    """
    deposits = [t for t in transactions if t.type in ("e_transfer_in", "deposit")]
    sends = [t for t in transactions if t.type == "crypto_send"]

    for send in sends:
        for dep in deposits:
            gap_hours = abs((send.timestamp - dep.timestamp).total_seconds()) / 3600
            if gap_hours <= 4:
                return 0.92
    return 0.0


def _detect_income_inconsistency(transactions: list, stated_income: float) -> float:
    """
    30-day inflow significantly exceeding stated monthly income raises
    an income-inconsistency flag (FINTRAC Guideline 2-D).
    """
    if stated_income <= 0:
        return 0.0
    cutoff = datetime.utcnow() - timedelta(days=30)
    inflow_30d = sum(
        t.amount for t in transactions
        if t.timestamp >= cutoff
        and t.type in ("e_transfer_in", "deposit", "crypto_receive")
    )
    monthly_income = stated_income / 12
    if monthly_income == 0:
        return 0.0
    ratio = inflow_30d / monthly_income
    if ratio > 1.5:
        return min(0.95, 0.55 + ratio * 0.06)
    return 0.0


def _detect_new_counterparty_burst(transactions: list, known_cps: list) -> float:
    """
    Several never-before-seen counterparties appearing in a short window
    after a period of stability is a strong mule-network signal.
    """
    known_names = {cp["name"] for cp in known_cps}
    cutoff = datetime.utcnow() - timedelta(days=7)
    new_names = {
        t.counterparty_name
        for t in transactions
        if t.timestamp >= cutoff
        and t.counterparty_name
        and t.counterparty_name not in known_names
    }
    if len(new_names) >= 3:
        return 0.85
    if len(new_names) == 2:
        return 0.60
    return 0.0


def _detect_round_tripping(transactions: list) -> float:
    """
    Funds leaving and returning through different channels at similar amounts
    within 7-21 days suggests round-tripping to obscure origin (FINTRAC Guideline 2-G).
    """
    outflows = [t for t in transactions if t.type in ("e_transfer_out", "crypto_send")]
    inflows = [t for t in transactions if t.type in ("e_transfer_in", "deposit")]

    for out_txn in outflows:
        for in_txn in inflows:
            gap_days = (in_txn.timestamp - out_txn.timestamp).total_seconds() / 86400
            if 7 <= gap_days <= 21:
                high = max(out_txn.amount, in_txn.amount)
                if high == 0:
                    continue
                amount_ratio = min(out_txn.amount, in_txn.amount) / high
                if amount_ratio >= 0.85 and out_txn.counterparty_name != in_txn.counterparty_name:
                    return 0.82
    return 0.0


# ── Archetype classification ──────────────────────────────────────────────────

def _classify_archetype(
    client: "Client",
    dep_freq: float,
    has_crypto: bool,
    overall_score: float,
    outflow_30d: float,
    inflow_30d: float,
    cp_count: int,
) -> tuple[str, str]:
    """
    Assign the client to the closest behavioral archetype.
    Returns (archetype, trajectory).
    """
    account_age = (datetime.utcnow() - client.account_opened_at).days
    rapid_outflow = inflow_30d > 0 and (outflow_30d / inflow_30d) > 0.80

    if overall_score >= 0.65 and rapid_outflow:
        return "mule_like", "shifting_negative"

    if dep_freq >= 0.3 and not has_crypto and cp_count <= 4:
        trajectory = "shifting_negative" if overall_score > 0.4 else "stable"
        return "payroll_depositor", trajectory

    if account_age <= 180 and overall_score < 0.35:
        return "new_investor", "stable"

    if has_crypto and dep_freq > 1.0:
        return "active_trader", "stable"

    trajectory = "shifting_negative" if overall_score > 0.4 else "stable"
    return "seasonal_spiker", trajectory


# ── Core computation ──────────────────────────────────────────────────────────

def compute_profile(client_id: str, db: Session) -> BehavioralProfile:
    """
    Compute (or recompute) the behavioral profile for a client.

    This is the backbone of Layer 1. It reads raw transactions and produces
    a structured fingerprint used by every downstream layer:
      - Layer 2 uses overall_risk_score → response level
      - Layer 3 uses the full fingerprint as investigation context
      - The frontend renders risk_history as a time-series chart
    """
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise ValueError(f"Client {client_id} not found")

    now = datetime.utcnow()
    window_90d = now - timedelta(days=90)
    window_30d = now - timedelta(days=30)

    all_txns: list[Transaction] = (
        db.query(Transaction).filter(Transaction.client_id == client_id).all()
    )
    recent_txns = [t for t in all_txns if t.timestamp >= window_90d]
    last_30d = [t for t in all_txns if t.timestamp >= window_30d]

    deposits = [
        t for t in recent_txns
        if t.type in ("e_transfer_in", "deposit", "crypto_receive")
    ]
    withdrawals = [
        t for t in recent_txns
        if t.type in ("e_transfer_out", "withdrawal", "crypto_send")
    ]

    avg_dep = sum(t.amount for t in deposits) / len(deposits) if deposits else 0.0
    avg_wdw = sum(t.amount for t in withdrawals) / len(withdrawals) if withdrawals else 0.0
    dep_freq = len(deposits) / (90 / 7) if deposits else 0.0

    inflow_30d = sum(
        t.amount for t in last_30d
        if t.type in ("e_transfer_in", "deposit", "crypto_receive")
    )
    outflow_30d = sum(
        t.amount for t in last_30d
        if t.type in ("e_transfer_out", "withdrawal", "crypto_send", "crypto_buy")
    )

    # Build counterparty registry
    cp_map: dict = {}
    for t in recent_txns:
        if t.counterparty_name:
            entry = cp_map.setdefault(t.counterparty_name, {
                "name": t.counterparty_name,
                "type": "sender" if t.type in ("e_transfer_in", "deposit") else "recipient",
                "last_seen": t.timestamp.isoformat(),
                "frequency": 0,
            })
            entry["frequency"] += 1
            if t.timestamp.isoformat() > entry["last_seen"]:
                entry["last_seen"] = t.timestamp.isoformat()
    known_counterparties = list(cp_map.values())

    # ── Risk scoring ──────────────────────────────────────────────────────────
    struct_conf = _detect_structuring(deposits)
    layer_conf = _detect_layering(recent_txns)
    crypto_conf = _detect_rapid_crypto_conversion(recent_txns)
    income_conf = _detect_income_inconsistency(all_txns, client.stated_income)
    cp_conf = _detect_new_counterparty_burst(recent_txns, known_counterparties)
    round_trip_conf = _detect_round_tripping(recent_txns)

    # Product-scoped scores: the highest relevant indicator per product
    risk_scores: dict[str, float] = {}

    chequing_txns = [t for t in recent_txns if t.product == "chequing"]
    if chequing_txns:
        risk_scores["chequing"] = round(
            max(struct_conf, income_conf, cp_conf, round_trip_conf), 3
        )

    crypto_txns = [t for t in recent_txns if t.product == "crypto"]
    if crypto_txns:
        risk_scores["crypto"] = round(
            max(layer_conf, crypto_conf, struct_conf), 3
        )

    investment_txns = [t for t in recent_txns if t.product in ("tfsa", "rrsp")]
    if investment_txns:
        risk_scores["investments"] = round(max(struct_conf * 0.3, income_conf * 0.4), 3)

    overall = round(max(risk_scores.values()) if risk_scores else 0.0, 3)
    risk_scores["overall"] = overall

    # ── Archetype ─────────────────────────────────────────────────────────────
    has_crypto = "crypto" in (client.products_held or [])
    archetype, trajectory = _classify_archetype(
        client, dep_freq, has_crypto, overall, outflow_30d, inflow_30d, len(cp_map)
    )

    risk_trend = "rising" if overall >= 0.5 else "stable"

    # ── FINTRAC indicators ────────────────────────────────────────────────────
    indicators_detected = []
    now_str = now.isoformat()
    for indicator, confidence in [
        ("structuring", struct_conf),
        ("layering", layer_conf),
        ("rapid_crypto_conversion", crypto_conf),
        ("income_inconsistency", income_conf),
        ("new_counterparty_burst", cp_conf),
        ("round_tripping", round_trip_conf),
    ]:
        if confidence >= 0.50:
            indicators_detected.append({
                "indicator": indicator,
                "detected_at": now_str,
                "confidence": round(confidence, 2),
            })

    # ── Risk history (append today, keep last 30 days) ────────────────────────
    existing: BehavioralProfile | None = (
        db.query(BehavioralProfile)
        .filter(BehavioralProfile.client_id == client_id)
        .first()
    )
    risk_history = list(existing.risk_history) if existing else []
    today_str = now.strftime("%Y-%m-%d")
    risk_history = [h for h in risk_history if h["date"] != today_str]
    risk_history.append({"date": today_str, "score": overall})
    risk_history = sorted(risk_history, key=lambda x: x["date"])[-30:]

    # ── Upsert ────────────────────────────────────────────────────────────────
    if existing:
        existing.avg_deposit_amount = round(avg_dep, 2)
        existing.avg_withdrawal_amount = round(avg_wdw, 2)
        existing.deposit_frequency_per_week = round(dep_freq, 2)
        existing.total_inflow_30d = round(inflow_30d, 2)
        existing.total_outflow_30d = round(outflow_30d, 2)
        existing.known_counterparties = known_counterparties
        existing.risk_scores = risk_scores
        existing.overall_risk_score = overall
        existing.archetype = archetype
        existing.archetype_trajectory = trajectory
        existing.risk_trend = risk_trend
        existing.risk_history = risk_history
        existing.indicators_detected = indicators_detected
        existing.last_updated = now
        return existing

    profile = BehavioralProfile(
        client_id=client_id,
        avg_deposit_amount=round(avg_dep, 2),
        avg_withdrawal_amount=round(avg_wdw, 2),
        deposit_frequency_per_week=round(dep_freq, 2),
        total_inflow_30d=round(inflow_30d, 2),
        total_outflow_30d=round(outflow_30d, 2),
        known_counterparties=known_counterparties,
        risk_scores=risk_scores,
        overall_risk_score=overall,
        archetype=archetype,
        archetype_trajectory=trajectory,
        risk_trend=risk_trend,
        risk_history=risk_history,
        indicators_detected=indicators_detected,
        last_updated=now,
    )
    db.add(profile)
    db.flush()
    return profile
