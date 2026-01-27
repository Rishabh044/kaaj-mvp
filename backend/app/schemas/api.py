"""API-specific request/response schemas.

These schemas are designed for the REST API endpoints and may differ slightly
from the internal domain schemas to provide a better API experience.
"""

from typing import Optional

from pydantic import Field

from app.schemas.common import BaseSchema


# =============================================================================
# Application Submission Schemas
# =============================================================================


class ApplicantInput(BaseSchema):
    """Applicant/guarantor information for API submission.

    A simplified version of GuarantorCreate focused on the fields needed
    for the matching engine evaluation.
    """

    # Credit Scores
    fico_score: int = Field(..., ge=300, le=850, description="FICO credit score")
    transunion_score: Optional[int] = Field(None, ge=300, le=850)
    experian_score: Optional[int] = Field(None, ge=300, le=850)
    equifax_score: Optional[int] = Field(None, ge=300, le=850)

    # Personal
    is_homeowner: bool = False
    is_us_citizen: bool = True

    # Professional (for trucking)
    has_cdl: bool = False
    cdl_years: Optional[int] = Field(None, ge=0)
    industry_experience_years: Optional[int] = Field(None, ge=0)


class BusinessInput(BaseSchema):
    """Business information for API submission.

    A simplified version of BusinessCreate focused on fields needed
    for matching engine evaluation.
    """

    name: str = Field(..., min_length=1, max_length=255)
    state: str = Field(..., min_length=2, max_length=2)
    industry_code: Optional[str] = None
    industry_name: Optional[str] = None
    years_in_business: float = Field(..., ge=0)
    annual_revenue: Optional[int] = Field(None, ge=0)
    fleet_size: Optional[int] = Field(None, ge=0)


class CreditHistoryInput(BaseSchema):
    """Credit history information for API submission."""

    has_bankruptcy: bool = False
    bankruptcy_discharge_years: Optional[float] = None
    bankruptcy_chapter: Optional[str] = None

    has_open_judgements: bool = False
    judgement_amount: Optional[int] = Field(None, ge=0)

    has_foreclosure: bool = False
    has_repossession: bool = False

    has_tax_liens: bool = False
    tax_lien_amount: Optional[int] = Field(None, ge=0)


class EquipmentInput(BaseSchema):
    """Equipment information for API submission."""

    category: str = Field(..., description="Equipment category")
    type: Optional[str] = None
    year: int = Field(..., ge=1900, le=2100)
    mileage: Optional[int] = Field(None, ge=0)
    hours: Optional[int] = Field(None, ge=0)
    condition: str = "used"


class LoanRequestInput(BaseSchema):
    """Loan request details for API submission."""

    amount: int = Field(..., gt=0, description="Loan amount in cents")
    requested_term_months: Optional[int] = Field(None, ge=1, le=84)
    down_payment_percent: Optional[float] = Field(None, ge=0, le=100)
    transaction_type: str = "purchase"
    is_private_party: bool = False


class BusinessCreditInput(BaseSchema):
    """Business credit information for API submission."""

    paynet_score: Optional[int] = Field(None, ge=0, le=100)
    paynet_master_score: Optional[int] = Field(None, ge=300, le=850)
    paydex_score: Optional[int] = Field(None, ge=0, le=100)


class ApplicationSubmitRequest(BaseSchema):
    """Complete request for submitting a new loan application."""

    applicant: ApplicantInput
    business: BusinessInput
    credit_history: CreditHistoryInput
    equipment: EquipmentInput
    loan_request: LoanRequestInput
    business_credit: Optional[BusinessCreditInput] = None


# =============================================================================
# Application Response Schemas
# =============================================================================


class ApplicationSubmitResponse(BaseSchema):
    """Response after submitting an application."""

    id: str
    application_number: str
    status: str
    workflow_run_id: Optional[str] = None
    message: str


class ApplicationListItem(BaseSchema):
    """Summary of an application for list views."""

    id: str
    application_number: str
    business_name: str
    loan_amount: int
    status: str
    created_at: str
    total_eligible: Optional[int] = None


class ApplicationStatusResponse(BaseSchema):
    """Application processing status."""

    application_id: str
    status: str
    workflow_run_id: Optional[str] = None
    total_evaluated: Optional[int] = None
    total_eligible: Optional[int] = None
    best_match: Optional[str] = None
    processed_at: Optional[str] = None


# =============================================================================
# Matching Results Schemas
# =============================================================================


class CriterionResultResponse(BaseSchema):
    """Result of a single criterion evaluation."""

    rule_name: str
    passed: bool
    required_value: str
    actual_value: str
    message: str


class LenderMatchResponse(BaseSchema):
    """Response for a single lender match."""

    lender_id: str
    lender_name: str
    is_eligible: bool
    fit_score: float
    rank: Optional[int] = None
    best_program: Optional[str] = None
    rejection_reasons: list[str] = []
    criteria_results: list[CriterionResultResponse] = []


class MatchingResultsResponse(BaseSchema):
    """Complete matching results for an application."""

    application_id: str
    total_evaluated: int
    total_eligible: int
    best_match: Optional[LenderMatchResponse] = None
    matches: list[LenderMatchResponse]


# =============================================================================
# Pagination
# =============================================================================


class PaginatedListResponse(BaseSchema):
    """Paginated response wrapper for list endpoints."""

    items: list
    total: int
    skip: int
    limit: int


# =============================================================================
# Lender API Schemas
# =============================================================================


class ProgramSummary(BaseSchema):
    """Summary of a lending program."""

    id: str
    name: str
    is_app_only: bool
    min_amount: Optional[int] = None
    max_amount: Optional[int] = None


class LenderListItem(BaseSchema):
    """Summary of a lender for list views."""

    id: str
    name: str
    version: int
    program_count: int
    is_active: bool = True


class CriteriaDetail(BaseSchema):
    """Detailed criteria configuration."""

    credit_score: Optional[dict] = None
    business: Optional[dict] = None
    credit_history: Optional[dict] = None
    equipment: Optional[dict] = None
    geographic: Optional[dict] = None
    industry: Optional[dict] = None
    transaction: Optional[dict] = None


class ProgramDetail(BaseSchema):
    """Detailed program information."""

    id: str
    name: str
    description: Optional[str] = None
    is_app_only: bool = False
    min_amount: Optional[int] = None
    max_amount: Optional[int] = None
    max_term_months: Optional[int] = None
    criteria: Optional[CriteriaDetail] = None


class RestrictionsDetail(BaseSchema):
    """Global restrictions detail."""

    geographic: Optional[dict] = None
    industry: Optional[dict] = None
    transaction: Optional[dict] = None
    equipment: Optional[dict] = None


class LenderDetailResponse(BaseSchema):
    """Detailed lender information with full policy."""

    id: str
    name: str
    version: int
    description: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    programs: list[ProgramDetail]
    restrictions: Optional[RestrictionsDetail] = None
    is_active: bool = True


class LenderCreateRequest(BaseSchema):
    """Input for creating a new lender."""

    id: str = Field(..., min_length=1, pattern=r"^[a-z0-9_]+$")
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None


class LenderUpdateRequest(BaseSchema):
    """Input for updating a lender."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    is_active: Optional[bool] = None


class LenderStatusResponse(BaseSchema):
    """Response for lender status toggle."""

    id: str
    name: str
    is_active: bool
    message: str
