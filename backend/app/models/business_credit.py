"""Business Credit model for PayNet, D&B, and trade lines."""

import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, Date, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.business import Business


class BusinessCredit(Base, UUIDMixin, TimestampMixin):
    """Represents business credit profile (PayNet, D&B, trade lines)."""

    __tablename__ = "business_credits"

    # SQLAlchemy's `default=` in mapped_column() only applies during database INSERT,
    # not at Python object instantiation. We override __init__ to set defaults so that
    # model instances have correct values immediately upon creation (e.g., in tests).
    def __init__(self, **kwargs: object) -> None:
        if "has_slow_pays" not in kwargs:
            kwargs["has_slow_pays"] = False
        super().__init__(**kwargs)

    business_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("businesses.id"), unique=True
    )

    # PayNet Score
    paynet_score: Mapped[Optional[int]] = mapped_column(Integer)
    paynet_master_score: Mapped[Optional[int]] = mapped_column(Integer)

    # D&B (Dun & Bradstreet)
    duns_number: Mapped[Optional[str]] = mapped_column(String(9))
    dnb_rating: Mapped[Optional[str]] = mapped_column(String(10))
    paydex_score: Mapped[Optional[int]] = mapped_column(Integer)

    # Trade Lines
    trade_line_count: Mapped[Optional[int]] = mapped_column(Integer)
    highest_credit: Mapped[Optional[int]] = mapped_column(Integer)
    average_days_to_pay: Mapped[Optional[int]] = mapped_column(Integer)

    # Negative Items
    has_slow_pays: Mapped[bool] = mapped_column(Boolean, default=False)
    slow_pay_count: Mapped[Optional[int]] = mapped_column(Integer)

    # Report Date
    report_date: Mapped[Optional[date]] = mapped_column(Date)

    # Relationships
    business: Mapped["Business"] = relationship(back_populates="business_credit")

    def __repr__(self) -> str:
        return f"<BusinessCredit(id={self.id}, business_id={self.business_id}, paynet={self.paynet_score})>"

    @property
    def has_paynet(self) -> bool:
        """Check if PayNet score is available."""
        return self.paynet_score is not None

    @property
    def has_dnb(self) -> bool:
        """Check if D&B rating is available."""
        return self.dnb_rating is not None or self.paydex_score is not None
