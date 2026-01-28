"""Common schema components shared across the application."""

from datetime import date, datetime
from enum import Enum
from typing import Generic, Optional, TypeVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class TransactionType(str, Enum):
    """Types of financing transactions."""

    PURCHASE = "purchase"
    REFINANCE = "refinance"
    SALE_LEASEBACK = "sale_leaseback"


class EquipmentCategory(str, Enum):
    """Categories of equipment for financing."""

    CLASS_8_TRUCK = "class_8_truck"
    TRAILER = "trailer"
    CONSTRUCTION = "construction"
    VOCATIONAL = "vocational"
    MEDICAL = "medical"
    OTHER = "other"


class EquipmentCondition(str, Enum):
    """Condition of equipment."""

    NEW = "new"
    USED = "used"
    CERTIFIED = "certified"


class ApplicationStatus(str, Enum):
    """Status of a loan application."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    ERROR = "error"


class EntityType(str, Enum):
    """Types of business entities."""

    LLC = "LLC"
    CORPORATION = "Corporation"
    SOLE_PROP = "Sole Proprietorship"
    PARTNERSHIP = "Partnership"
    S_CORP = "S Corporation"


class BankruptcyChapter(str, Enum):
    """Bankruptcy chapter types."""

    CHAPTER_7 = "7"
    CHAPTER_11 = "11"
    CHAPTER_13 = "13"


# Generic type for paginated responses
T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response wrapper."""

    items: list[T]
    total: int
    page: int
    page_size: int
    total_pages: int

    @classmethod
    def create(
        cls, items: list[T], total: int, page: int, page_size: int
    ) -> "PaginatedResponse[T]":
        """Create a paginated response."""
        total_pages = (total + page_size - 1) // page_size
        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )


class BaseSchema(BaseModel):
    """Base schema with common configuration."""

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
    )


class TimestampSchema(BaseSchema):
    """Schema with timestamp fields."""

    created_at: datetime
    updated_at: datetime


class IDSchema(BaseSchema):
    """Schema with UUID id field."""

    id: UUID
