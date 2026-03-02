from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import AccountRestriction, BehavioralProfile, Client, Transaction
from app.schemas import BehavioralProfileOut, ClientDetail, ClientSummary, TransactionOut
from app.services.layer1_behavioral import compute_profile

router = APIRouter()


def _active_level(client: Client) -> int:
    """Return the highest active restriction level for a client."""
    active = [r for r in client.restrictions if r.is_active]
    return max((r.level for r in active), default=0)


def _to_summary(client: Client) -> ClientSummary:
    profile: BehavioralProfile | None = client.behavioral_profile
    return ClientSummary(
        id=client.id,
        name=client.name,
        kyc_level=client.kyc_level,
        products_held=client.products_held or [],
        account_opened_at=client.account_opened_at,
        stated_income=client.stated_income,
        occupation=client.occupation,
        overall_risk_score=profile.overall_risk_score if profile else 0.0,
        archetype=profile.archetype if profile else "new_investor",
        active_restriction_level=_active_level(client),
    )


def _to_detail(client: Client) -> ClientDetail:
    profile: BehavioralProfile | None = client.behavioral_profile
    base = _to_summary(client)
    return ClientDetail(
        **base.model_dump(),
        date_of_birth=client.date_of_birth,
        archetype_trajectory=profile.archetype_trajectory if profile else "stable",
        risk_trend=profile.risk_trend if profile else "stable",
        risk_scores=profile.risk_scores if profile else {},
        risk_history=profile.risk_history if profile else [],
        indicators_detected=profile.indicators_detected if profile else [],
        known_counterparties=profile.known_counterparties if profile else [],
        total_inflow_30d=profile.total_inflow_30d if profile else 0.0,
        total_outflow_30d=profile.total_outflow_30d if profile else 0.0,
        deposit_frequency_per_week=profile.deposit_frequency_per_week if profile else 0.0,
    )


@router.get("", response_model=list[ClientSummary])
def list_clients(db: Session = Depends(get_db)):
    """Return all clients with a summary including risk score and restriction level."""
    clients = db.query(Client).all()
    return [_to_summary(c) for c in clients]


@router.get("/{client_id}", response_model=ClientDetail)
def get_client(client_id: str, db: Session = Depends(get_db)):
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return _to_detail(client)


@router.get("/{client_id}/profile", response_model=BehavioralProfileOut)
def get_profile(client_id: str, db: Session = Depends(get_db)):
    """Return the full behavioral profile for a client."""
    profile = (
        db.query(BehavioralProfile)
        .filter(BehavioralProfile.client_id == client_id)
        .first()
    )
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile


@router.post("/{client_id}/profile/recompute", response_model=BehavioralProfileOut)
def recompute_profile(
    client_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Recompute the behavioral profile from the client's transaction history.
    This is Layer 1 running on-demand — in production it would run after
    every incoming transaction event.
    """
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    profile = compute_profile(client_id, db)
    db.commit()
    return profile


@router.get("/{client_id}/transactions", response_model=list[TransactionOut])
def get_client_transactions(
    client_id: str,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """Return the most recent transactions for a client."""
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    txns = (
        db.query(Transaction)
        .filter(Transaction.client_id == client_id)
        .order_by(Transaction.timestamp.desc())
        .limit(limit)
        .all()
    )
    return txns
