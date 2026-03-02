import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Float, ForeignKey, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.client import Client


class BehavioralProfile(Base):
    __tablename__ = "behavioral_profiles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    client_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("clients.id"), nullable=False, unique=True
    )

    # Rolling 90-day transaction statistics
    avg_deposit_amount: Mapped[float] = mapped_column(Float, default=0.0)
    avg_withdrawal_amount: Mapped[float] = mapped_column(Float, default=0.0)
    deposit_frequency_per_week: Mapped[float] = mapped_column(Float, default=0.0)
    total_inflow_30d: Mapped[float] = mapped_column(Float, default=0.0)
    total_outflow_30d: Mapped[float] = mapped_column(Float, default=0.0)

    # Counterparty network
    # Format: [{"name": str, "type": "sender"|"recipient", "last_seen": str, "frequency": int}]
    known_counterparties: Mapped[list] = mapped_column(JSON, default=list)

    # Risk scores per product (0.0–1.0)
    # Format: {"chequing": 0.12, "crypto": 0.85, "overall": 0.65}
    risk_scores: Mapped[dict] = mapped_column(JSON, default=dict)
    overall_risk_score: Mapped[float] = mapped_column(Float, default=0.0)

    # Archetype: new_investor | active_trader | payroll_depositor | seasonal_spiker | mule_like
    archetype: Mapped[str] = mapped_column(String(50), default="new_investor")
    # Trajectory: stable | shifting_negative | shifting_positive
    archetype_trajectory: Mapped[str] = mapped_column(String(30), default="stable")
    # Trend: rising | stable | falling
    risk_trend: Mapped[str] = mapped_column(String(20), default="stable")

    # Time-series risk history for the frontend chart (last 30 daily data points)
    # Format: [{"date": "YYYY-MM-DD", "score": float}]
    risk_history: Mapped[list] = mapped_column(JSON, default=list)

    # FINTRAC indicators currently detected on this client
    # Format: [{"indicator": str, "detected_at": str, "confidence": float}]
    indicators_detected: Mapped[list] = mapped_column(JSON, default=list)

    # System-initiated proactive actions (notifications, step-up auth, calls, info requests)
    # Format: [{"timestamp", "action", "label", "trigger", "channel", "status"}]
    proactive_actions: Mapped[list] = mapped_column(JSON, default=list)

    last_updated: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    client: Mapped["Client"] = relationship("Client", back_populates="behavioral_profile")
