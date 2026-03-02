from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import AccountRestriction, AuditEntry, Client, Investigation, STRDraft
from app.schemas import AuditEntryOut, DashboardSummary

router = APIRouter()


@router.get("/summary", response_model=DashboardSummary)
def get_summary(db: Session = Depends(get_db)):
    """
    Top-level dashboard metrics: restriction breakdown, active cases,
    pending STRs, and filings this month.
    """
    total_clients = db.query(func.count(Client.id)).scalar() or 0

    # Active restriction level distribution
    active_restrictions = (
        db.query(AccountRestriction)
        .filter(AccountRestriction.is_active == True)  # noqa: E712
        .all()
    )
    level_counts: dict[str, int] = {"0": 0, "1": 0, "2": 0, "3": 0, "4": 0}
    restricted_client_ids = {r.client_id for r in active_restrictions}
    for r in active_restrictions:
        level_counts[str(r.level)] = level_counts.get(str(r.level), 0) + 1

    # Unrestricted clients (no active restriction = level 0)
    level_counts["0"] = total_clients - len(restricted_client_ids)

    open_investigations = (
        db.query(func.count(Investigation.id))
        .filter(Investigation.status.in_(["open", "running", "fast_tracked", "str_drafted"]))
        .scalar() or 0
    )

    str_drafts_pending = (
        db.query(func.count(STRDraft.id))
        .filter(STRDraft.status == "draft")
        .scalar() or 0
    )

    month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    strs_filed = (
        db.query(func.count(STRDraft.id))
        .filter(STRDraft.status == "approved", STRDraft.decided_at >= month_start)
        .scalar() or 0
    )

    # Last 20 audit entries as the activity feed
    recent = (
        db.query(AuditEntry)
        .order_by(AuditEntry.timestamp.desc())
        .limit(20)
        .all()
    )
    activity = [
        {
            "id": e.id,
            "entity_type": e.entity_type,
            "entity_id": e.entity_id,
            "action": e.action,
            "actor": e.actor,
            "timestamp": e.timestamp.isoformat(),
        }
        for e in recent
    ]

    return DashboardSummary(
        total_clients=total_clients,
        clients_by_restriction_level=level_counts,
        open_investigations=open_investigations,
        str_drafts_pending=str_drafts_pending,
        strs_filed_this_month=strs_filed,
        recent_activity=activity,
    )


@router.get("/activity", response_model=list[AuditEntryOut])
def get_activity_feed(limit: int = 50, db: Session = Depends(get_db)):
    """Return the most recent audit entries across all entities."""
    entries = (
        db.query(AuditEntry)
        .order_by(AuditEntry.timestamp.desc())
        .limit(limit)
        .all()
    )
    return entries
