"""Personal Guarantor model for individuals guaranteeing loans."""

import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, Date, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.application import LoanApplication


class PersonalGuarantor(Base, UUIDMixin, TimestampMixin):
    """Represents the individual guaranteeing the loan with their credit profile."""

    __tablename__ = "personal_guarantors"

    # SQLAlchemy's `default=` in mapped_column() only applies during database INSERT,
    # not at Python object instantiation. We override __init__ to set defaults so that
    # model instances have correct values immediately upon creation (e.g., in tests).
    def __init__(self, **kwargs: object) -> None:
        defaults = {
            "is_homeowner": False,
            "is_us_citizen": True,
            "has_bankruptcy": False,
            "has_open_judgements": False,
            "has_foreclosure": False,
            "has_repossession": False,
            "has_tax_liens": False,
            "has_cdl": False,
        }
        for key, value in defaults.items():
            if key not in kwargs:
                kwargs[key] = value
        super().__init__(**kwargs)

    # Identity
    first_name: Mapped[str] = mapped_column(String(100))
    last_name: Mapped[str] = mapped_column(String(100))
    ssn_last_four: Mapped[Optional[str]] = mapped_column(String(4))  # For reference only

    # Contact
    email: Mapped[Optional[str]] = mapped_column(String(255))
    phone: Mapped[Optional[str]] = mapped_column(String(20))

    # Credit Scores
    fico_score: Mapped[Optional[int]] = mapped_column(Integer)
    transunion_score: Mapped[Optional[int]] = mapped_column(Integer)
    experian_score: Mapped[Optional[int]] = mapped_column(Integer)
    equifax_score: Mapped[Optional[int]] = mapped_column(Integer)

    # Homeownership
    is_homeowner: Mapped[bool] = mapped_column(Boolean, default=False)

    # Citizenship
    is_us_citizen: Mapped[bool] = mapped_column(Boolean, default=True)

    # Credit History Flags
    has_bankruptcy: Mapped[bool] = mapped_column(Boolean, default=False)
    bankruptcy_discharge_date: Mapped[Optional[date]] = mapped_column(Date)
    bankruptcy_chapter: Mapped[Optional[str]] = mapped_column(String(10))  # 7, 11, 13

    has_open_judgements: Mapped[bool] = mapped_column(Boolean, default=False)
    judgement_amount: Mapped[Optional[int]] = mapped_column(Integer)

    has_foreclosure: Mapped[bool] = mapped_column(Boolean, default=False)
    foreclosure_date: Mapped[Optional[date]] = mapped_column(Date)

    has_repossession: Mapped[bool] = mapped_column(Boolean, default=False)
    repossession_date: Mapped[Optional[date]] = mapped_column(Date)

    has_tax_liens: Mapped[bool] = mapped_column(Boolean, default=False)
    tax_lien_amount: Mapped[Optional[int]] = mapped_column(Integer)

    # Professional (for trucking)
    has_cdl: Mapped[bool] = mapped_column(Boolean, default=False)
    cdl_years: Mapped[Optional[int]] = mapped_column(Integer)
    industry_experience_years: Mapped[Optional[int]] = mapped_column(Integer)

    # Relationships
    loan_applications: Mapped[list["LoanApplication"]] = relationship(
        back_populates="guarantor"
    )

    def __repr__(self) -> str:
        return f"<PersonalGuarantor(id={self.id}, name='{self.first_name} {self.last_name}')>"

    @property
    def full_name(self) -> str:
        """Return the full name of the guarantor."""
        return f"{self.first_name} {self.last_name}"

    @property
    def bankruptcy_discharge_years(self) -> Optional[float]:
        """Calculate years since bankruptcy discharge."""
        if not self.has_bankruptcy or not self.bankruptcy_discharge_date:
            return None
        days_since = (date.today() - self.bankruptcy_discharge_date).days
        return days_since / 365.25

    def get_credit_score(self, score_type: str) -> Optional[int]:
        """Get a specific credit score by type."""
        score_map = {
            "fico": self.fico_score,
            "transunion": self.transunion_score,
            "experian": self.experian_score,
            "equifax": self.equifax_score,
        }
        return score_map.get(score_type.lower())
