import json
import uuid
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import AccountRestriction, AuditEntry, BehavioralProfile, Client, Investigation, STRDraft
from app.schemas import (
    AuditEntryOut,
    InvestigationDetail,
    InvestigationSummary,
    STRDecision,
    SimulateResponse,
    TriggerInvestigationRequest,
)
from app.services.layer1_behavioral import compute_profile
from app.services.layer2_response import determine_response
from app.services.layer3_orchestrator import run_investigation

router = APIRouter()


def _to_summary(inv: Investigation) -> InvestigationSummary:
    client_name = inv.client.name if inv.client else "Unknown"
    return InvestigationSummary(
        id=inv.id,
        client_id=inv.client_id,
        client_name=client_name,
        status=inv.status,
        classification=inv.classification,
        confidence=inv.confidence,
        is_coordinated=inv.is_coordinated,
        correlated_client_ids=inv.correlated_client_ids or [],
        response_level=inv.response_level,
        step_log=inv.step_log or [],
        created_at=inv.created_at,
        updated_at=inv.updated_at,
    )


@router.get("", response_model=list[InvestigationSummary])
def list_investigations(
    status: str | None = None,
    db: Session = Depends(get_db),
):
    """List all investigations, optionally filtered by status."""
    q = db.query(Investigation)
    if status:
        q = q.filter(Investigation.status == status)
    return [_to_summary(inv) for inv in q.order_by(Investigation.created_at.desc()).all()]


@router.get("/{investigation_id}", response_model=InvestigationDetail)
def get_investigation(investigation_id: str, db: Session = Depends(get_db)):
    """Return full investigation detail including STR draft and evidence."""
    inv = db.query(Investigation).filter(Investigation.id == investigation_id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Investigation not found")

    return InvestigationDetail(
        id=inv.id,
        client_id=inv.client_id,
        client_name=inv.client.name if inv.client else "Unknown",
        trigger_event=inv.trigger_event,
        response_level=inv.response_level,
        status=inv.status,
        correlated_client_ids=inv.correlated_client_ids or [],
        is_coordinated=inv.is_coordinated,
        network_graph=inv.network_graph,
        classification=inv.classification,
        confidence=inv.confidence,
        reasoning=inv.reasoning,
        step_log=inv.step_log or [],
        str_draft=inv.str_draft,
        created_at=inv.created_at,
        updated_at=inv.updated_at,
    )


@router.post("/trigger/{client_id}", response_model=InvestigationSummary)
def trigger_investigation(
    client_id: str,
    body: TriggerInvestigationRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Manually trigger a Layer 3 investigation for a client.
    Creates the Investigation record then runs the full pipeline synchronously.
    """
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    investigation = Investigation(
        id=str(uuid.uuid4()),
        client_id=client_id,
        trigger_event={"trigger_type": body.trigger_type, "notes": body.notes},
        response_level=3,
        status="open",
    )
    db.add(investigation)
    db.add(AuditEntry(
        id=str(uuid.uuid4()),
        entity_type="investigation",
        entity_id=investigation.id,
        action="investigation_manually_triggered",
        actor="human:analyst",
        details={"trigger_type": body.trigger_type},
    ))
    db.commit()

    try:
        result = run_investigation(investigation.id, db)
        db.commit()
        return _to_summary(result)
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/{investigation_id}/decide", response_model=InvestigationSummary)
def decide_str(
    investigation_id: str,
    body: STRDecision,
    db: Session = Depends(get_db),
):
    """
    Layer 4 — the human decision point.
    Analyst approves the STR for FINTRAC filing or dismisses the investigation.
    """
    inv = db.query(Investigation).filter(Investigation.id == investigation_id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Investigation not found")

    if body.decision not in ("approve", "dismiss"):
        raise HTTPException(status_code=400, detail="decision must be 'approve' or 'dismiss'")

    if inv.str_draft:
        inv.str_draft.status = "approved" if body.decision == "approve" else "dismissed"
        inv.str_draft.analyst_notes = body.notes
        inv.str_draft.decided_at = datetime.utcnow()
        inv.str_draft.decided_by = body.analyst
        inv.str_draft.updated_at = datetime.utcnow()

    inv.status = "filed" if body.decision == "approve" else "dismissed"
    inv.updated_at = datetime.utcnow()

    db.add(AuditEntry(
        id=str(uuid.uuid4()),
        entity_type="investigation",
        entity_id=investigation_id,
        action=f"str_{body.decision}d",
        actor=f"human:{body.analyst}",
        details={"notes": body.notes},
    ))
    db.commit()
    return _to_summary(inv)


@router.get("/{investigation_id}/audit", response_model=list[AuditEntryOut])
def get_audit_trail(investigation_id: str, db: Session = Depends(get_db)):
    """Return the audit trail for a specific investigation."""
    entries = (
        db.query(AuditEntry)
        .filter(
            AuditEntry.entity_type == "investigation",
            AuditEntry.entity_id == investigation_id,
        )
        .order_by(AuditEntry.timestamp.asc())
        .all()
    )
    return entries


# ── Simulate endpoint (full pipeline: Layer 1 → 2 → 3) ──────────────────────

def _build_simulate_step_log_entry(
    step: str, label: str, layer: int, details: str, action_type: Optional[str]
) -> dict:
    return {
        "step": step,
        "label": label,
        "layer": layer,
        "status": "complete",
        "timestamp": datetime.utcnow().isoformat(),
        "details": details,
        "action_type": action_type,
    }


def _run_simulate_pipeline(
    investigation_id: str,
    client_id: str,
    client_name: str,
) -> None:
    """
    Background task: runs the full Layer 1 → 2 → 3 pipeline with step logging.
    Uses its own DB session since it runs in a background thread.
    """
    from app.core.database import SessionLocal

    db = SessionLocal()
    try:
        step_log: list[dict] = []

        def append_step(step: str, label: str, layer: int, details: str = "", action_type: Optional[str] = None) -> None:
            entry = _build_simulate_step_log_entry(step, label, layer, details, action_type)
            step_log.append(entry)
            # Persist immediately so the frontend sees progress
            inv = db.query(Investigation).filter(Investigation.id == investigation_id).first()
            if inv:
                inv.step_log = list(step_log)
                inv.updated_at = datetime.utcnow()
                db.flush()
                db.commit()

        # ── Layer 1 steps ────────────────────────────────────────────────────
        append_step("loading_client_data", "Loading client profile, KYC, and transaction history", 1,
                    json.dumps({"summary": f"Client: {client_name} | Account data and 90-day transaction history retrieved",
                                "data": {"client_name": client_name, "client_id": client_id}}))

        # Recompute profile (Layer 1)
        fresh_profile = compute_profile(client_id, db)
        db.commit()

        profile_archetype = fresh_profile.archetype or "new_investor"
        profile_risk_score = fresh_profile.overall_risk_score or 0.0
        indicators = [i["indicator"] for i in (fresh_profile.indicators_detected or [])]

        append_step("behavioral_baseline", "Computing 90-day behavioral baseline", 1,
                    json.dumps({"summary": "Deposit, withdrawal, frequency, and product usage ratios calculated",
                                "data": {"avg_deposit": round(fresh_profile.avg_deposit_amount, 2),
                                         "avg_withdrawal": round(fresh_profile.avg_withdrawal_amount, 2),
                                         "deposit_freq_per_week": round(fresh_profile.deposit_frequency_per_week, 2),
                                         "total_inflow_30d": round(fresh_profile.total_inflow_30d, 2),
                                         "total_outflow_30d": round(fresh_profile.total_outflow_30d, 2),
                                         "known_counterparties": len(fresh_profile.known_counterparties or [])}}))

        append_step("archetype_classification", f"Behavioral archetype: {profile_archetype.replace('_', ' ')}", 1,
                    json.dumps({"summary": f"Client classified as {profile_archetype.replace('_', ' ')}",
                                "data": {"archetype": profile_archetype,
                                         "trajectory": fresh_profile.archetype_trajectory or "stable",
                                         "counterparties_mapped": len(fresh_profile.known_counterparties or [])}}))

        append_step("network_graph_build", "Building known-counterparty network graph", 1,
                    json.dumps({"summary": f"{len(fresh_profile.known_counterparties or [])} counterparty nodes mapped",
                                "data": {"counterparty_count": len(fresh_profile.known_counterparties or []),
                                         "top_counterparties": [cp["name"] for cp in (fresh_profile.known_counterparties or [])[:5]]}}))

        scores_str = ", ".join(f"{k}: {v:.2f}" for k, v in fresh_profile.risk_scores.items() if k != "overall")
        append_step("per_product_risk_scores", "Computing per-product risk scores", 1,
                    json.dumps({"summary": f"Per-product scores: {scores_str}",
                                "data": {k: v for k, v in fresh_profile.risk_scores.items()}}))

        trend = fresh_profile.risk_trend or "stable"
        append_step("risk_trajectory", f"Risk trajectory: {trend}", 1,
                    json.dumps({"summary": f"7-day trend vs 30-day rolling average: {trend}",
                                "data": {"trend": trend, "overall_score": profile_risk_score,
                                         "risk_history_points": len(fresh_profile.risk_history or [])}}))

        append_step("deviation_calculation", "Running deviation analysis", 1,
                    json.dumps({"summary": f"Composite deviation score: {profile_risk_score:.2f}" +
                                (f" | Indicators: {', '.join(indicators)}" if indicators else " | Within normal range"),
                                "data": {"overall_risk_score": profile_risk_score,
                                         "indicators_detected": indicators,
                                         "indicator_count": len(indicators)}}))

        # ── Layer 2 steps ────────────────────────────────────────────────────
        append_step("contextual_reasoning", "AI contextual reasoning: evaluating seasonal and historical context", 2,
                    json.dumps({"summary": "Evaluating RRSP season, prior large deposits, income consistency, and counterparty novelty",
                                "data": {"model": "claude-sonnet-4-6",
                                         "checks": ["RRSP contribution season", "prior large deposit history",
                                                     "income consistency ratio", "counterparty novelty score"],
                                         "indicators_input": indicators,
                                         "risk_score_input": round(profile_risk_score, 3)}}))

        # Determine trigger type from computed indicators for appropriate fallback
        if "rapid_crypto_conversion" in indicators and "structuring" in indicators:
            trigger = "structuring_crypto_layering"
        elif "rapid_crypto_conversion" in indicators or "layering" in indicators:
            trigger = "crypto_layering"
        elif "structuring" in indicators and profile_risk_score >= 0.75:
            trigger = "structuring_crypto_layering"
        elif "structuring" in indicators:
            trigger = "minor_structuring"
        elif "round_tripping" in indicators:
            trigger = "round_tripping"
        elif "income_inconsistency" in indicators and ("new_counterparty_burst" in indicators or "rapid_crypto_conversion" in indicators):
            trigger = "mule_pattern"
        elif "new_counterparty_burst" in indicators:
            trigger = "mule_pattern"
        elif "income_inconsistency" in indicators:
            trigger = "income_inconsistency"
        else:
            trigger = "salary_spike"  # auto-resolve: no significant indicators

        # Run Layer 2 — investigation already exists, don't open another one
        new_restriction = determine_response(client_id, trigger, db, enqueue_investigation=False)
        db.commit()
        new_level = new_restriction.level if new_restriction else 0

        level_descriptions = {
            0: "No restrictions — activity within normal range",
            1: "Enhanced monitoring — passive observation only",
            2: "Guardrail active — step-up verification for flagged operations",
            3: "Restricted — capabilities limited, investigation initiated",
            4: "Frozen — all outbound transactions suspended",
        }
        restricted_caps = []
        if new_restriction:
            restricted_caps = new_restriction.restricted_capabilities or []
        append_step("level_assignment", f"Graduated restriction level: Level {new_level} assigned", 2,
                    json.dumps({"summary": f"Composite deviation + contextual reasoning → Level {new_level}: {level_descriptions.get(new_level, 'Unknown')}",
                                "data": {"level": new_level,
                                         "trigger_type": trigger,
                                         "description": level_descriptions.get(new_level, "Unknown"),
                                         "restricted": restricted_caps if restricted_caps else ["none"],
                                         "risk_score": round(profile_risk_score, 3)}}))

        if new_level >= 2:
            client = db.query(Client).filter(Client.id == client_id).first()
            msg = (
                "We've added a verification step for large transfers as a security precaution. "
                "All other account features remain available."
            )
            append_step("notification_sent",
                        "Client notified: security verification added for large transfers", 2,
                        json.dumps({"summary": f"Push + email sent to {client_name}",
                                    "data": {"channel": "push + email",
                                             "message": msg,
                                             "trigger": f"Level {new_level} guardrail activated",
                                             "client": client_name}}),
                        "notification_sent")

            # Save to proactive_actions
            profile = db.query(BehavioralProfile).filter(BehavioralProfile.client_id == client_id).first()
            if profile:
                actions = list(profile.proactive_actions or [])
                actions.append({
                    "timestamp": datetime.utcnow().isoformat(),
                    "action": "notification_sent",
                    "label": "Client notified: verification step added for large transfers",
                    "trigger": f"Level {new_level} guardrail activated",
                    "channel": "push + email",
                    "status": "delivered",
                })
                profile.proactive_actions = actions
                db.commit()

        if new_level >= 3:
            append_step("guardrail_intercept",
                        "Step-up authentication activated for outbound transfers", 2,
                        json.dumps({"summary": "Biometric or 2FA required for crypto purchases and outbound transfers above $500",
                                    "data": {"blocked_processes": restricted_caps if restricted_caps else ["crypto_send_external", "e_transfer_out_new_recipient"],
                                             "auth_required": "biometric or 2FA",
                                             "threshold": "$500",
                                             "still_allowed": ["bill_payment", "internal_transfer", "payroll_deposit"]}}),
                        "step_up_auth")

            append_step("re_evaluation",
                        "Re-evaluation after guardrail intercept — pattern confirmed", 2,
                        json.dumps({"summary": "Behavioral escalation confirmed — pattern persists after guardrail application",
                                    "data": {"pattern_type": trigger,
                                             "indicators_confirmed": indicators,
                                             "escalation": "Layer 3 investigation initiated",
                                             "confidence": round(profile_risk_score * 100, 1)}}))

            # Save to proactive_actions
            profile = db.query(BehavioralProfile).filter(BehavioralProfile.client_id == client_id).first()
            if profile:
                actions = list(profile.proactive_actions or [])
                call_date = (datetime.utcnow() + timedelta(days=2)).strftime("%B %d, %Y")
                actions.append({
                    "timestamp": datetime.utcnow().isoformat(),
                    "action": "follow_up_call_scheduled",
                    "label": f"Agent scheduled verification call for {call_date}",
                    "trigger": f"Level {new_level} restriction applied",
                    "channel": "phone",
                    "status": "scheduled",
                })
                profile.proactive_actions = actions
                db.commit()

            append_step("follow_up_call_scheduled",
                        f"Agent scheduled verification call for +2 business days", 2,
                        json.dumps({"summary": f"Verification call scheduled — agent will request source-of-funds documentation",
                                    "data": {"reference": f"CASE-{investigation_id[:8].upper()}",
                                             "duration": "15 minutes",
                                             "channel": "phone",
                                             "purpose": "Source-of-funds documentation request",
                                             "scheduled_date": call_date,
                                             "questions": ["Verify identity of recent counterparties",
                                                           "Request supporting documents for flagged transactions",
                                                           "Confirm business or employment relationship"]}}),
                        "follow_up_call_scheduled")

        elif new_level == 2:
            profile = db.query(BehavioralProfile).filter(BehavioralProfile.client_id == client_id).first()
            if profile:
                actions = list(profile.proactive_actions or [])
                deadline = (datetime.utcnow() + timedelta(days=5)).strftime("%B %d, %Y")
                actions.append({
                    "timestamp": datetime.utcnow().isoformat(),
                    "action": "info_request_sent",
                    "label": "Information request sent: source of funds documentation required",
                    "trigger": "Level 2 guardrail — income inconsistency detected",
                    "channel": "secure message + email",
                    "status": "awaiting_response",
                })
                profile.proactive_actions = actions
                db.commit()

            deadline = (datetime.utcnow() + timedelta(days=5)).strftime("%B %d, %Y")
            append_step("info_request_sent",
                        "Information request sent: source of funds documentation required", 2,
                        json.dumps({"summary": f"Client has until {deadline} to provide supporting documentation",
                                    "data": {"deadline": deadline,
                                             "channel": "secure message + email",
                                             "documents_requested": ["Source of funds documentation",
                                                                      "Employment or business verification",
                                                                      "Explanation for flagged transactions"],
                                             "escalation_if_no_response": "Restrictions may escalate to Level 3",
                                             "status": "awaiting_response"}}),
                        "info_request_sent")

        # ── Layer 3 (only if level >= 3) ────────────────────────────────────
        if new_level >= 3:
            # The investigation record already exists; run Layer 3 with step callback
            def layer3_callback(step: str, label: str, layer: int, details: str = "", action_type: Optional[str] = None) -> None:
                append_step(step, label, layer, details, action_type)

            run_investigation(investigation_id, db, step_callback=layer3_callback)
            db.commit()
        else:
            # Mark investigation as de-escalated if level < 3
            inv = db.query(Investigation).filter(Investigation.id == investigation_id).first()
            if inv:
                inv.status = "de_escalated"
                inv.classification = "de_escalate"
                inv.confidence = 85.0
                inv.reasoning = f"Behavioral analysis complete. Client assigned Level {new_level}. No investigation required at this threshold."
                inv.updated_at = datetime.utcnow()
                db.commit()

            if new_level == 0:
                append_step("complete", "Analysis complete — auto-resolved (Level 0)", 2,
                            json.dumps({"summary": "Activity consistent with client baseline. No restrictions applied.",
                                        "data": {"result": "auto-resolved",
                                                 "level": 0,
                                                 "risk_score": round(profile_risk_score, 3),
                                                 "archetype": profile_archetype,
                                                 "action": "No restrictions. Normal monitoring continues."}}))
            else:
                append_step("complete", f"Analysis complete — Level {new_level} monitoring active", 2,
                            json.dumps({"summary": f"Graduated response applied. Client at Level {new_level}. Monitoring enhanced.",
                                        "data": {"result": f"Level {new_level} active",
                                                 "level": new_level,
                                                 "risk_score": round(profile_risk_score, 3),
                                                 "restricted": restricted_caps if restricted_caps else ["enhanced monitoring"],
                                                 "next_steps": "Client notified. Documentation requested."}}))

        # Final "complete" step
        inv = db.query(Investigation).filter(Investigation.id == investigation_id).first()
        if inv and inv.status not in ("str_drafted", "fast_tracked"):
            pass  # complete step already appended above
        elif inv and inv.status in ("str_drafted", "fast_tracked"):
            # Layer 3 callback appended "str_complete" step already
            pass

    except Exception as exc:
        import logging
        logging.getLogger(__name__).error("Simulate pipeline failed: %s", exc, exc_info=True)
        inv = db.query(Investigation).filter(Investigation.id == investigation_id).first()
        if inv:
            inv.status = "dismissed"
            inv.reasoning = f"Pipeline error: {str(exc)}"
            db.commit()
    finally:
        db.close()


@router.post("/simulate/{client_id}", response_model=SimulateResponse)
def simulate_pipeline(
    client_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Run the full Layer 1 → 2 → 3 simulation pipeline for a client.
    Returns immediately with an investigation_id. Frontend polls for step_log progress.
    """
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    # Create the investigation record immediately
    investigation = Investigation(
        id=str(uuid.uuid4()),
        client_id=client_id,
        trigger_event={"trigger_type": "simulate", "source": "dashboard_simulate_button"},
        response_level=3,
        status="open",
        step_log=[],
    )
    db.add(investigation)
    db.add(AuditEntry(
        id=str(uuid.uuid4()),
        entity_type="investigation",
        entity_id=investigation.id,
        action="simulation_triggered",
        actor="human:analyst",
        details={"source": "dashboard"},
    ))
    db.commit()

    background_tasks.add_task(
        _run_simulate_pipeline,
        investigation_id=investigation.id,
        client_id=client_id,
        client_name=client.name,
    )

    return SimulateResponse(
        investigation_id=investigation.id,
        client_id=client_id,
        client_name=client.name,
        message="Simulation started — poll /investigations/{id} for step_log progress",
    )
