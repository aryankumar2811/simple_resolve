import uuid
from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import AuditEntry, Client, Investigation, STRDraft
from app.schemas import (
    AuditEntryOut,
    InvestigationDetail,
    InvestigationSummary,
    STRDecision,
    TriggerInvestigationRequest,
)
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
