"""Loan Application model with equipment details."""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDMixin, generate_application_number

if TYPE_CHECKING:
    from app.models.business import Business
    from app.models.guarantor import PersonalGuarantor
    from app.models.match_result import MatchResult


class LoanApplication(Base, UUIDMixin, TimestampMixin):
    """Represents a loan application with equipment and loan details."""

    __tablename__ = "loan_applications"

    # SQLAlchemy's `default=` in mapped_column() only applies during database INSERT,
    # not at Python object instantiation. We override __init__ to set defaults so that
    # model instances have correct values immediately upon creation (e.g., in tests).
    def __init__(self, **kwargs: object) -> None:
        defaults = {
            "status": "pending",
            "is_private_party": False,
            "equipment_age_years": 0,
        }
        for key, value in defaults.items():
            if key not in kwargs:
                kwargs[key] = value
        super().__init__(**kwargs)

    application_number: Mapped[str] = mapped_column(
        String(30), unique=True, default=generate_application_number
    )

    # Foreign Keys
    business_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("businesses.id"))
    guarantor_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("personal_guarantors.id")
    )

    # Loan Details
    loan_amount: Mapped[int] = mapped_column(Integer)  # In cents for precision
    requested_term_months: Mapped[Optional[int]] = mapped_column(Integer)
    down_payment_percent: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))

    # Transaction Type
    transaction_type: Mapped[str] = mapped_column(
        String(50)
    )  # purchase, refinance, sale_leaseback
    is_private_party: Mapped[bool] = mapped_column(Boolean, default=False)

    # Equipment Details
    equipment_category: Mapped[str] = mapped_column(
        String(100)
    )  # class_8_truck, trailer, construction
    equipment_type: Mapped[str] = mapped_column(String(100))  # specific type
    equipment_make: Mapped[Optional[str]] = mapped_column(String(100))
    equipment_model: Mapped[Optional[str]] = mapped_column(String(100))
    equipment_year: Mapped[int] = mapped_column(Integer)
    equipment_mileage: Mapped[Optional[int]] = mapped_column(Integer)
    equipment_hours: Mapped[Optional[int]] = mapped_column(Integer)  # For construction

    # Derived Fields (computed on save)
    equipment_age_years: Mapped[int] = mapped_column(Integer, default=0)

    # Equipment Condition
    equipment_condition: Mapped[str] = mapped_column(
        String(20)
    )  # new, used, certified

    # Status
    status: Mapped[str] = mapped_column(
        String(20), default="pending"
    )  # pending, processing, completed, error

    # Timestamps
    submitted_at: Mapped[datetime] = mapped_column(default=func.now())
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # Relationships
    business: Mapped["Business"] = relationship(back_populates="loan_applications")
    guarantor: Mapped["PersonalGuarantor"] = relationship(
        back_populates="loan_applications"
    )
    match_results: Mapped[list["MatchResult"]] = relationship(
        back_populates="application", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<LoanApplication(id={self.id}, number='{self.application_number}', status='{self.status}')>"

    def compute_equipment_age(self) -> int:
        """Compute equipment age based on current year."""
        current_year = datetime.now().year
        return current_year - self.equipment_year

    def update_equipment_age(self) -> None:
        """Update the equipment_age_years field."""
        self.equipment_age_years = self.compute_equipment_age()

    @property
    def loan_amount_dollars(self) -> float:
        """Return loan amount in dollars."""
        return self.loan_amount / 100

    @property
    def is_trucking(self) -> bool:
        """Check if this is a trucking-related application."""
        trucking_categories = {"class_8_truck", "trailer", "semi", "truck"}
        return self.equipment_category.lower() in trucking_categories

    @property
    def is_completed(self) -> bool:
        """Check if application processing is complete."""
        return self.status == "completed"

    @property
    def is_processing(self) -> bool:
        """Check if application is currently being processed."""
        return self.status == "processing"

    def mark_processing(self) -> None:
        """Mark application as processing."""
        self.status = "processing"

    def mark_completed(self) -> None:
        """Mark application as completed."""
        self.status = "completed"
        self.processed_at = datetime.now()

    def mark_error(self) -> None:
        """Mark application as errored."""
        self.status = "error"
        self.processed_at = datetime.now()
