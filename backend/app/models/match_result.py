"""Match Result model for storing evaluation results."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional

from sqlalchemy import Boolean, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import UUIDMixin

if TYPE_CHECKING:
    from app.models.application import LoanApplication
    from app.models.lender import Lender


class MatchResult(Base, UUIDMixin):
    """Persists evaluation results for audit trail and display."""

    __tablename__ = "match_results"

    # Foreign Keys
    application_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("loan_applications.id")
    )
    lender_id: Mapped[str] = mapped_column(ForeignKey("lenders.id"))

    # Eligibility
    is_eligible: Mapped[bool] = mapped_column(Boolean)
    matched_program_id: Mapped[Optional[str]] = mapped_column(String(50))
    matched_program_name: Mapped[Optional[str]] = mapped_column(String(255))

    # Scoring
    fit_score: Mapped[int] = mapped_column(Integer, default=0)  # 0-100
    rank: Mapped[Optional[int]] = mapped_column(Integer)  # 1 = best match

    # Detailed Results (JSON)
    criteria_results: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    # Structure:
    # {
    #   "credit_score": {
    #     "passed": false,
    #     "rule_name": "Minimum TransUnion Score",
    #     "required_value": 700,
    #     "actual_value": 650,
    #     "message": "TransUnion score 650 below minimum 700",
    #     "score_contribution": 0
    #   },
    #   ...
    # }

    # Summary
    rejection_reasons: Mapped[Optional[list[str]]] = mapped_column(JSONB, default=list)
    # ["Credit score 650 below minimum 700", "State CA is restricted"]

    # Timestamps
    evaluated_at: Mapped[datetime] = mapped_column(default=func.now())

    # Relationships
    application: Mapped["LoanApplication"] = relationship(back_populates="match_results")
    lender: Mapped["Lender"] = relationship(back_populates="match_results")

    def __repr__(self) -> str:
        return (
            f"<MatchResult(id={self.id}, lender='{self.lender_id}', "
            f"eligible={self.is_eligible}, score={self.fit_score})>"
        )

    @property
    def has_rejection_reasons(self) -> bool:
        """Check if there are rejection reasons."""
        return bool(self.rejection_reasons)

    @property
    def primary_rejection_reason(self) -> Optional[str]:
        """Get the primary rejection reason."""
        if self.rejection_reasons:
            return self.rejection_reasons[0]
        return None

    def get_failed_criteria(self) -> list[str]:
        """Get list of criteria that failed."""
        return [
            key
            for key, result in self.criteria_results.items()
            if not result.get("passed", True)
        ]

    def get_passed_criteria(self) -> list[str]:
        """Get list of criteria that passed."""
        return [
            key
            for key, result in self.criteria_results.items()
            if result.get("passed", False)
        ]
