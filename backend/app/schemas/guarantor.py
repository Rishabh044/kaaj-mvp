"""Pydantic schemas for PersonalGuarantor model."""

from datetime import date
from typing import Optional
from uuid import UUID

from pydantic import Field, field_validator, model_validator

from app.schemas.common import BankruptcyChapter, BaseSchema, IDSchema, TimestampSchema


class GuarantorBase(BaseSchema):
    """Base schema for personal guarantor data."""

    # Identity
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    ssn_last_four: Optional[str] = Field(None, min_length=4, max_length=4)

    # Contact
    email: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=20)

    # Credit Scores
    fico_score: Optional[int] = Field(None, ge=300, le=850)
    transunion_score: Optional[int] = Field(None, ge=300, le=850)
    experian_score: Optional[int] = Field(None, ge=300, le=850)
    equifax_score: Optional[int] = Field(None, ge=300, le=850)

    # Homeownership
    is_homeowner: bool = False

    # Citizenship
    is_us_citizen: bool = True

    # Credit History Flags
    has_bankruptcy: bool = False
    bankruptcy_discharge_date: Optional[date] = None
    bankruptcy_chapter: Optional[str] = None

    has_open_judgements: bool = False
    judgement_amount: Optional[int] = Field(None, ge=0)

    has_foreclosure: bool = False
    foreclosure_date: Optional[date] = None

    has_repossession: bool = False
    repossession_date: Optional[date] = None

    has_tax_liens: bool = False
    tax_lien_amount: Optional[int] = Field(None, ge=0)

    # Professional
    has_cdl: bool = False
    cdl_years: Optional[int] = Field(None, ge=0)
    industry_experience_years: Optional[int] = Field(None, ge=0)

    @field_validator("ssn_last_four")
    @classmethod
    def validate_ssn(cls, v: Optional[str]) -> Optional[str]:
        """Validate SSN last four digits."""
        if v is not None and (len(v) != 4 or not v.isdigit()):
            raise ValueError("SSN last four must be exactly 4 digits")
        return v

    @model_validator(mode="after")
    def validate_bankruptcy_fields(self) -> "GuarantorBase":
        """Validate bankruptcy-related fields are consistent."""
        if self.has_bankruptcy:
            if self.bankruptcy_chapter and self.bankruptcy_chapter not in ("7", "11", "13"):
                raise ValueError("Bankruptcy chapter must be 7, 11, or 13")
        else:
            # If no bankruptcy, these should be None
            self.bankruptcy_discharge_date = None
            self.bankruptcy_chapter = None
        return self

    @model_validator(mode="after")
    def validate_judgement_fields(self) -> "GuarantorBase":
        """Validate judgement-related fields."""
        if not self.has_open_judgements:
            self.judgement_amount = None
        return self

    @model_validator(mode="after")
    def validate_tax_lien_fields(self) -> "GuarantorBase":
        """Validate tax lien-related fields."""
        if not self.has_tax_liens:
            self.tax_lien_amount = None
        return self


class GuarantorCreate(GuarantorBase):
    """Schema for creating a new guarantor."""

    pass


class GuarantorUpdate(BaseSchema):
    """Schema for updating a guarantor."""

    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    ssn_last_four: Optional[str] = Field(None, min_length=4, max_length=4)
    email: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=20)
    fico_score: Optional[int] = Field(None, ge=300, le=850)
    transunion_score: Optional[int] = Field(None, ge=300, le=850)
    experian_score: Optional[int] = Field(None, ge=300, le=850)
    equifax_score: Optional[int] = Field(None, ge=300, le=850)
    is_homeowner: Optional[bool] = None
    is_us_citizen: Optional[bool] = None
    has_bankruptcy: Optional[bool] = None
    bankruptcy_discharge_date: Optional[date] = None
    bankruptcy_chapter: Optional[str] = None
    has_open_judgements: Optional[bool] = None
    judgement_amount: Optional[int] = Field(None, ge=0)
    has_foreclosure: Optional[bool] = None
    foreclosure_date: Optional[date] = None
    has_repossession: Optional[bool] = None
    repossession_date: Optional[date] = None
    has_tax_liens: Optional[bool] = None
    tax_lien_amount: Optional[int] = Field(None, ge=0)
    has_cdl: Optional[bool] = None
    cdl_years: Optional[int] = Field(None, ge=0)
    industry_experience_years: Optional[int] = Field(None, ge=0)


class GuarantorResponse(GuarantorBase, IDSchema, TimestampSchema):
    """Schema for guarantor response."""

    full_name: str
    bankruptcy_discharge_years: Optional[float] = None


class GuarantorSummary(IDSchema):
    """Abbreviated guarantor info for listings."""

    full_name: str
    fico_score: Optional[int] = None
    is_homeowner: bool
