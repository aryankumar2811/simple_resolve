from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import Transaction
from app.schemas import TransactionOut

router = APIRouter()


@router.get("", response_model=list[TransactionOut])
def list_transactions(
    client_id: str | None = Query(default=None),
    product: str | None = Query(default=None),
    type_filter: str | None = Query(default=None, alias="type"),
    limit: int = Query(default=50, le=500),
    db: Session = Depends(get_db),
):
    """List transactions with optional filtering by client, product, or type."""
    q = db.query(Transaction)
    if client_id:
        q = q.filter(Transaction.client_id == client_id)
    if product:
        q = q.filter(Transaction.product == product)
    if type_filter:
        q = q.filter(Transaction.type == type_filter)
    return q.order_by(Transaction.timestamp.desc()).limit(limit).all()
