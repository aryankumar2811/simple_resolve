import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, Float, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.investigation import Investigation
    from app.models.profile import BehavioralProfile
    from app.models.restriction import AccountRestriction
    from app.models.transaction import Transaction


class Client(Base):
    __tablename__ = "clients"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    date_of_birth: Mapped[str] = mapped_column(String(20), nullable=False)
    stated_income: Mapped[float] = mapped_column(Float, nullable=False)
    occupation: Mapped[str] = mapped_column(String(200), nullable=False)
    # basic | standard | enhanced
    kyc_level: Mapped[str] = mapped_column(String(20), nullable=False, default="standard")
    account_opened_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    # e.g. ["chequing", "crypto", "tfsa", "rrsp", "visa"]
    products_held: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    transactions: Mapped[list["Transaction"]] = relationship(
        "Transaction", back_populates="client", lazy="select"
    )
    behavioral_profile: Mapped[Optional["BehavioralProfile"]] = relationship(
        "BehavioralProfile", back_populates="client", uselist=False, lazy="select"
    )
    restrictions: Mapped[list["AccountRestriction"]] = relationship(
        "AccountRestriction", back_populates="client", lazy="select"
    )
    investigations: Mapped[list["Investigation"]] = relationship(
        "Investigation", back_populates="client", lazy="select"
    )
