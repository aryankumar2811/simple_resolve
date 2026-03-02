import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, Float, ForeignKey, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.client import Client


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    client_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("clients.id"), nullable=False, index=True
    )

    # Transaction classification
    # Types: e_transfer_in, e_transfer_out, crypto_buy, crypto_sell, crypto_send,
    #        crypto_receive, bill_payment, deposit, withdrawal, investment_buy, investment_sell
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    # Products: chequing, crypto, tfsa, rrsp, visa
    product: Mapped[str] = mapped_column(String(50), nullable=False)

    amount: Mapped[float] = mapped_column(Float, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)

    # Counterparty / routing info
    source: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    destination: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    counterparty_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    # Extra metadata (wallet address, IP, device fingerprint, etc.)
    txn_metadata: Mapped[Optional[dict]] = mapped_column("metadata", JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    client: Mapped["Client"] = relationship("Client", back_populates="transactions")
