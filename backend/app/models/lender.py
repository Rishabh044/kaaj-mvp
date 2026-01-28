"""Lender model for managing lender metadata in the database."""

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin

if TYPE_CHECKING:
    from app.models.match_result import MatchResult


class Lender(Base, TimestampMixin):
    """Represents a lender with policy file reference."""

    __tablename__ = "lenders"

    # SQLAlchemy's `default=` in mapped_column() only applies during database INSERT,
    # not at Python object instantiation. We override __init__ to set defaults so that
    # model instances have correct values immediately upon creation (e.g., in tests).
    def __init__(self, **kwargs: object) -> None:
        if "is_active" not in kwargs:
            kwargs["is_active"] = True
        if "policy_version" not in kwargs:
            kwargs["policy_version"] = 1
        super().__init__(**kwargs)

    # Use string ID (e.g., "citizens_bank")
    id: Mapped[str] = mapped_column(String(50), primary_key=True)

    # Display Info
    name: Mapped[str] = mapped_column(String(255))
    logo_url: Mapped[Optional[str]] = mapped_column(String(500))

    # Contact
    contact_name: Mapped[Optional[str]] = mapped_column(String(100))
    contact_email: Mapped[Optional[str]] = mapped_column(String(255))
    contact_phone: Mapped[Optional[str]] = mapped_column(String(20))

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Policy File Reference
    policy_file: Mapped[str] = mapped_column(String(255))  # Path to YAML file
    policy_version: Mapped[int] = mapped_column(Integer, default=1)
    policy_last_updated: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    # Relationships
    match_results: Mapped[list["MatchResult"]] = relationship(back_populates="lender")

    def __repr__(self) -> str:
        return f"<Lender(id='{self.id}', name='{self.name}', active={self.is_active})>"

    def toggle_status(self) -> None:
        """Toggle the active status of the lender."""
        self.is_active = not self.is_active

    def update_policy_version(self) -> None:
        """Increment policy version and update timestamp."""
        self.policy_version += 1
        self.policy_last_updated = datetime.now()
