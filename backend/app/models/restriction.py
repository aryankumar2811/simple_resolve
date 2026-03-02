import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.client import Client


class AccountRestriction(Base):
    __tablename__ = "account_restrictions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    client_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("clients.id"), nullable=False, index=True
    )

    # Response level 0–4
    # 0=baseline, 1=monitor, 2=guardrail, 3=restrict, 4=freeze
    level: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Scope of restriction — which capabilities are affected
    # e.g. ["crypto_send_external", "e_transfer_out_new_recipient"]
    restricted_capabilities: Mapped[list] = mapped_column(JSON, default=list)
    # e.g. ["chequing_deposit", "bill_payment", "investment_buy"]
    allowed_capabilities: Mapped[list] = mapped_column(JSON, default=list)

    reason: Mapped[str] = mapped_column(String(500), nullable=False)
    client_message: Mapped[str] = mapped_column(String(1000), nullable=False, default="")

    # Gemini's scope-reasoning output (stored for audit and explainability)
    gemini_reasoning: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # What triggered this restriction
    trigger_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    trigger_event: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    triggered_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    client: Mapped["Client"] = relationship("Client", back_populates="restrictions")
