"""Pydantic schemas for Lender model."""

from datetime import datetime
from typing import Optional

from pydantic import Field

from app.schemas.common import BaseSchema, TimestampSchema


class LenderBase(BaseSchema):
    """Base schema for lender data."""

    name: str = Field(..., min_length=1, max_length=255)
    logo_url: Optional[str] = Field(None, max_length=500)
    contact_name: Optional[str] = Field(None, max_length=100)
    contact_email: Optional[str] = Field(None, max_length=255)
    contact_phone: Optional[str] = Field(None, max_length=20)
    is_active: bool = True
    policy_file: str = Field(..., min_length=1, max_length=255)


class LenderCreate(LenderBase):
    """Schema for creating a new lender."""

    id: str = Field(..., min_length=1, max_length=50, pattern=r"^[a-z][a-z0-9_]*$")


class LenderUpdate(BaseSchema):
    """Schema for updating a lender."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    logo_url: Optional[str] = Field(None, max_length=500)
    contact_name: Optional[str] = Field(None, max_length=100)
    contact_email: Optional[str] = Field(None, max_length=255)
    contact_phone: Optional[str] = Field(None, max_length=20)
    is_active: Optional[bool] = None
    policy_file: Optional[str] = Field(None, min_length=1, max_length=255)


class LenderResponse(LenderBase, TimestampSchema):
    """Schema for lender response."""

    id: str
    policy_version: int
    policy_last_updated: datetime


class LenderSummary(BaseSchema):
    """Abbreviated lender info for listings."""

    id: str
    name: str
    is_active: bool
    policy_version: int
    policy_last_updated: datetime
    programs_count: int = 0  # Populated from policy


class LenderDetail(LenderResponse):
    """Full lender details including policy info."""

    programs_count: int = 0
    # Policy details will be loaded separately from YAML
