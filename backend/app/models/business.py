"""Business model for companies applying for financing."""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import BigInteger, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.application import LoanApplication
    from app.models.business_credit import BusinessCredit


class Business(Base, UUIDMixin, TimestampMixin):
    """Represents a business applying for equipment financing."""

    __tablename__ = "businesses"

    # Basic Info
    legal_name: Mapped[str] = mapped_column(String(255))
    dba_name: Mapped[Optional[str]] = mapped_column(String(255))
    entity_type: Mapped[str] = mapped_column(String(50))  # LLC, Corp, Sole Prop

    # Industry
    industry_code: Mapped[str] = mapped_column(String(10))  # NAICS or SIC
    industry_name: Mapped[str] = mapped_column(String(255))

    # Location
    state: Mapped[str] = mapped_column(String(2))
    city: Mapped[str] = mapped_column(String(100))
    zip_code: Mapped[str] = mapped_column(String(10))

    # Business Metrics
    years_in_business: Mapped[Decimal] = mapped_column(Numeric(4, 1))
    annual_revenue: Mapped[Optional[int]] = mapped_column(BigInteger)
    employee_count: Mapped[Optional[int]] = mapped_column(Integer)

    # Trucking-Specific
    fleet_size: Mapped[Optional[int]] = mapped_column(Integer)

    # Relationships
    loan_applications: Mapped[list["LoanApplication"]] = relationship(
        back_populates="business"
    )
    business_credit: Mapped[Optional["BusinessCredit"]] = relationship(
        back_populates="business", uselist=False
    )

    def __repr__(self) -> str:
        return f"<Business(id={self.id}, name='{self.legal_name}', state='{self.state}')>"

    @property
    def is_startup(self) -> bool:
        """Check if business is considered a startup (less than 2 years)."""
        return float(self.years_in_business) < 2.0
