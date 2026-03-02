import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.client import Client


class Investigation(Base):
    __tablename__ = "investigations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    client_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("clients.id"), nullable=False, index=True
    )

    # What triggered this investigation
    trigger_event: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    response_level: Mapped[int] = mapped_column(Integer, default=3)

    # Lifecycle: open → running → de_escalated | fast_tracked | str_drafted → filed | dismissed
    status: Mapped[str] = mapped_column(String(50), default="open", index=True)

    # Cross-client coordination data
    correlated_client_ids: Mapped[list] = mapped_column(JSON, default=list)
    is_coordinated: Mapped[bool] = mapped_column(Boolean, default=False)
    # Network graph for visualization: {nodes: [...], edges: [...]}
    network_graph: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # LangGraph outputs
    # de_escalate | fast_track | full_investigation
    classification: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    reasoning: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Full LangGraph state snapshot kept for debugging and audit
    langgraph_state: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Step-by-step pipeline log for the simulate progress bar
    # Each entry: {step, label, layer, status, timestamp, details, action_type}
    step_log: Mapped[list] = mapped_column(JSON, default=list)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    client: Mapped["Client"] = relationship("Client", back_populates="investigations")
    str_draft: Mapped[Optional["STRDraft"]] = relationship(
        "STRDraft", back_populates="investigation", uselist=False, lazy="select"
    )


class STRDraft(Base):
    __tablename__ = "str_drafts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    investigation_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("investigations.id"), nullable=False, unique=True
    )

    # FINTRAC STR narrative sections
    subject_profile: Mapped[str] = mapped_column(Text, default="")
    activity_description: Mapped[str] = mapped_column(Text, default="")
    # [{"indicator": str, "confidence": float, "reasoning": str, "fintrac_ref": str}]
    indicators_present: Mapped[list] = mapped_column(JSON, default=list)
    behavioral_context: Mapped[str] = mapped_column(Text, default="")
    network_analysis: Mapped[str] = mapped_column(Text, default="")
    recommendation: Mapped[str] = mapped_column(Text, default="")
    key_uncertainties: Mapped[list] = mapped_column(JSON, default=list)

    # Full formatted narrative ready for FINTRAC review
    narrative_full: Mapped[str] = mapped_column(Text, default="")

    # Evidence package
    # Each transaction enriched with fintrac_indicators field
    tagged_transactions: Mapped[list] = mapped_column(JSON, default=list)
    # Directed graph: {nodes: [{id, label, type}], edges: [{from, to, amount, type}]}
    money_flow: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # AI metadata (for the explainability panel in the frontend)
    ai_confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    ai_reasoning_chain: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Human decision: draft | approved | dismissed
    status: Mapped[str] = mapped_column(String(20), default="draft")
    analyst_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    decided_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    decided_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    investigation: Mapped["Investigation"] = relationship(
        "Investigation", back_populates="str_draft"
    )


class AuditEntry(Base):
    __tablename__ = "audit_entries"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    # client | investigation | restriction | str_draft | system
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    action: Mapped[str] = mapped_column(String(200), nullable=False)
    # system | human:{analyst_name}
    actor: Mapped[str] = mapped_column(String(100), nullable=False, default="system")
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    details: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
