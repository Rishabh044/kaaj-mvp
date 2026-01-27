"""Pydantic schemas for LoanApplication model."""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import Field, field_validator, model_validator

from app.schemas.business import BusinessCreate, BusinessResponse, BusinessSummary
from app.schemas.common import (
    ApplicationStatus,
    BaseSchema,
    EquipmentCategory,
    EquipmentCondition,
    IDSchema,
    TimestampSchema,
    TransactionType,
)
from app.schemas.guarantor import (
    GuarantorCreate,
    GuarantorResponse,
    GuarantorSummary,
)


class EquipmentInput(BaseSchema):
    """Equipment details for loan application."""

    category: str = Field(..., description="Equipment category (e.g., class_8_truck)")
    type: str = Field(..., min_length=1, max_length=100, description="Specific equipment type")
    make: Optional[str] = Field(None, max_length=100)
    model: Optional[str] = Field(None, max_length=100)
    year: int = Field(..., ge=1900, le=2030)
    mileage: Optional[int] = Field(None, ge=0, description="Mileage for vehicles")
    hours: Optional[int] = Field(None, ge=0, description="Hours for construction equipment")
    condition: str = Field(..., description="Equipment condition (new, used, certified)")

    @field_validator("condition")
    @classmethod
    def validate_condition(cls, v: str) -> str:
        """Validate equipment condition."""
        valid = {"new", "used", "certified"}
        if v.lower() not in valid:
            raise ValueError(f"Condition must be one of: {valid}")
        return v.lower()


class CreditHistoryInput(BaseSchema):
    """Credit history flags for loan application."""

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


class LoanApplicationInput(BaseSchema):
    """Complete input for submitting a loan application."""

    # Business Info
    business: BusinessCreate

    # Guarantor Info
    guarantor: GuarantorCreate

    # Loan Details
    loan_amount: int = Field(..., gt=0, description="Loan amount in cents")
    requested_term_months: Optional[int] = Field(None, ge=12, le=84)
    down_payment_percent: Optional[Decimal] = Field(None, ge=0, le=100)

    # Transaction Type
    transaction_type: str = Field(..., description="purchase, refinance, or sale_leaseback")
    is_private_party: bool = False

    # Equipment
    equipment: EquipmentInput

    @field_validator("transaction_type")
    @classmethod
    def validate_transaction_type(cls, v: str) -> str:
        """Validate transaction type."""
        valid = {"purchase", "refinance", "sale_leaseback"}
        if v.lower() not in valid:
            raise ValueError(f"Transaction type must be one of: {valid}")
        return v.lower()


class LoanApplicationCreate(BaseSchema):
    """Internal schema for creating application after validation."""

    business_id: UUID
    guarantor_id: UUID
    loan_amount: int
    requested_term_months: Optional[int] = None
    down_payment_percent: Optional[Decimal] = None
    transaction_type: str
    is_private_party: bool = False
    equipment_category: str
    equipment_type: str
    equipment_make: Optional[str] = None
    equipment_model: Optional[str] = None
    equipment_year: int
    equipment_mileage: Optional[int] = None
    equipment_hours: Optional[int] = None
    equipment_condition: str


class LoanApplicationResponse(IDSchema, TimestampSchema):
    """Full loan application response."""

    application_number: str
    status: str

    # Related entities
    business: BusinessResponse
    guarantor: GuarantorResponse

    # Loan Details
    loan_amount: int
    loan_amount_dollars: float
    requested_term_months: Optional[int]
    down_payment_percent: Optional[Decimal]

    # Transaction
    transaction_type: str
    is_private_party: bool

    # Equipment
    equipment_category: str
    equipment_type: str
    equipment_make: Optional[str]
    equipment_model: Optional[str]
    equipment_year: int
    equipment_mileage: Optional[int]
    equipment_hours: Optional[int]
    equipment_age_years: int
    equipment_condition: str

    # Timestamps
    submitted_at: datetime
    processed_at: Optional[datetime]

    # Computed
    is_trucking: bool
    is_completed: bool


class LoanApplicationSummary(IDSchema):
    """Abbreviated application info for listings."""

    application_number: str
    status: str
    loan_amount_dollars: float
    equipment_category: str
    business: BusinessSummary
    guarantor: GuarantorSummary
    submitted_at: datetime


class ApplicationStatusResponse(BaseSchema):
    """Response for application status check."""

    application_id: UUID
    application_number: str
    status: str
    submitted_at: datetime
    processed_at: Optional[datetime]
    is_completed: bool
    is_processing: bool
