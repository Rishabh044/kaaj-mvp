"""Pydantic schemas for Business model."""

from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import Field, field_validator

from app.schemas.common import BaseSchema, EntityType, IDSchema, TimestampSchema

# Valid US state codes
US_STATE_CODES = {
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA",
    "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
    "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
    "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
    "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY",
    "DC", "PR", "VI", "GU", "AS", "MP",
}


class BusinessBase(BaseSchema):
    """Base schema for business data."""

    legal_name: str = Field(..., min_length=1, max_length=255)
    dba_name: Optional[str] = Field(None, max_length=255)
    entity_type: str = Field(..., max_length=50)
    industry_code: str = Field(..., min_length=2, max_length=10)
    industry_name: str = Field(..., min_length=1, max_length=255)
    state: str = Field(..., min_length=2, max_length=2)
    city: str = Field(..., min_length=1, max_length=100)
    zip_code: str = Field(..., min_length=5, max_length=10)
    years_in_business: Decimal = Field(..., ge=0, le=100)
    annual_revenue: Optional[int] = Field(None, ge=0)
    employee_count: Optional[int] = Field(None, ge=0)
    fleet_size: Optional[int] = Field(None, ge=0)

    @field_validator("state")
    @classmethod
    def validate_state(cls, v: str) -> str:
        """Validate that state is a valid US state code."""
        v = v.upper()
        if v not in US_STATE_CODES:
            raise ValueError(f"Invalid state code: {v}")
        return v

    @field_validator("zip_code")
    @classmethod
    def validate_zip_code(cls, v: str) -> str:
        """Validate zip code format."""
        # Remove spaces and hyphens for validation
        clean = v.replace(" ", "").replace("-", "")
        if not clean.isdigit():
            raise ValueError("Zip code must contain only digits")
        if len(clean) not in (5, 9):
            raise ValueError("Zip code must be 5 or 9 digits")
        return v


class BusinessCreate(BusinessBase):
    """Schema for creating a new business."""

    pass


class BusinessUpdate(BaseSchema):
    """Schema for updating a business."""

    legal_name: Optional[str] = Field(None, min_length=1, max_length=255)
    dba_name: Optional[str] = Field(None, max_length=255)
    entity_type: Optional[str] = Field(None, max_length=50)
    industry_code: Optional[str] = Field(None, min_length=2, max_length=10)
    industry_name: Optional[str] = Field(None, min_length=1, max_length=255)
    state: Optional[str] = Field(None, min_length=2, max_length=2)
    city: Optional[str] = Field(None, min_length=1, max_length=100)
    zip_code: Optional[str] = Field(None, min_length=5, max_length=10)
    years_in_business: Optional[Decimal] = Field(None, ge=0, le=100)
    annual_revenue: Optional[int] = Field(None, ge=0)
    employee_count: Optional[int] = Field(None, ge=0)
    fleet_size: Optional[int] = Field(None, ge=0)


class BusinessResponse(BusinessBase, IDSchema, TimestampSchema):
    """Schema for business response."""

    is_startup: bool


class BusinessSummary(IDSchema):
    """Abbreviated business info for listings."""

    legal_name: str
    state: str
    years_in_business: Decimal
