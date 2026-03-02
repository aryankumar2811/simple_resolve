from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import AccountRestriction, AuditEntry, Client
from app.schemas import AuditEntryOut, RestrictionOut, RestrictionOverride
from app.services.layer2_response import apply_override, determine_response

router = APIRouter()


@router.get("/{client_id}", response_model=RestrictionOut | None)
def get_restriction(client_id: str, db: Session = Depends(get_db)):
    """Return the active restriction for a client, or null if unrestricted."""
    restriction = (
        db.query(AccountRestriction)
        .filter(
            AccountRestriction.client_id == client_id,
            AccountRestriction.is_active == True,  # noqa: E712
        )
        .order_by(AccountRestriction.triggered_at.desc())
        .first()
    )
    return restriction


@router.post("/{client_id}/trigger", response_model=RestrictionOut)
def trigger_response(
    client_id: str,
    body: dict,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Trigger Layer 2 response evaluation for a client.

    Gemini reasons about which capabilities to restrict based on the
    trigger type and the client's current behavioral profile.

    If the resulting level is ≥ 3, Layer 3 investigation is also opened.
    """
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    trigger_type = body.get("trigger_type", "manual")
    restriction = determine_response(
        client_id=client_id,
        trigger_type=trigger_type,
        db=db,
        trigger_event=body,
    )
    db.commit()
    return restriction


@router.patch("/{client_id}", response_model=RestrictionOut)
def override_restriction(
    client_id: str,
    body: RestrictionOverride,
    db: Session = Depends(get_db),
):
    """Human analyst override: change the restriction level directly."""
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    if not 0 <= body.new_level <= 4:
        raise HTTPException(status_code=400, detail="Level must be 0–4")

    restriction = apply_override(
        client_id=client_id,
        new_level=body.new_level,
        reason=body.reason,
        analyst=body.analyst,
        db=db,
    )
    db.commit()
    return restriction


@router.delete("/{client_id}", response_model=RestrictionOut)
def deactivate_restriction(
    client_id: str,
    analyst: str = "human_analyst",
    db: Session = Depends(get_db),
):
    """De-escalate to Level 0 — full access restored."""
    restriction = apply_override(
        client_id=client_id,
        new_level=0,
        reason="Restriction manually cleared by analyst",
        analyst=analyst,
        db=db,
    )
    db.commit()
    return restriction


@router.get("/{client_id}/history", response_model=list[RestrictionOut])
def restriction_history(client_id: str, db: Session = Depends(get_db)):
    """Return all restrictions (active and inactive) for a client."""
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return (
        db.query(AccountRestriction)
        .filter(AccountRestriction.client_id == client_id)
        .order_by(AccountRestriction.triggered_at.desc())
        .all()
    )
