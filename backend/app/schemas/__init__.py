"""Pydantic schemas for API request/response validation."""

from app.schemas.api import (
    # Application API schemas
    ApplicantInput,
    ApplicationListItem,
    ApplicationStatusResponse as ApiApplicationStatusResponse,
    ApplicationSubmitRequest,
    ApplicationSubmitResponse,
    BusinessCreditInput,
    BusinessInput,
    CreditHistoryInput as ApiCreditHistoryInput,
    CriterionResultResponse,
    EquipmentInput as ApiEquipmentInput,
    LenderMatchResponse,
    LoanRequestInput,
    MatchingResultsResponse as ApiMatchingResultsResponse,
    PaginatedListResponse,
    # Lender API schemas
    CriteriaDetail,
    LenderCreateRequest,
    LenderDetailResponse,
    LenderListItem,
    LenderStatusResponse,
    LenderUpdateRequest,
    ProgramDetail,
    ProgramSummary,
    RestrictionsDetail,
)
from app.schemas.application import (
    ApplicationStatusResponse,
    CreditHistoryInput,
    EquipmentInput,
    LoanApplicationCreate,
    LoanApplicationInput,
    LoanApplicationResponse,
    LoanApplicationSummary,
)
from app.schemas.business import (
    BusinessCreate,
    BusinessResponse,
    BusinessSummary,
    BusinessUpdate,
)
from app.schemas.common import (
    ApplicationStatus,
    BankruptcyChapter,
    BaseSchema,
    EntityType,
    EquipmentCategory,
    EquipmentCondition,
    IDSchema,
    PaginatedResponse,
    TimestampSchema,
    TransactionType,
)
from app.schemas.guarantor import (
    GuarantorCreate,
    GuarantorResponse,
    GuarantorSummary,
    GuarantorUpdate,
)
from app.schemas.lender import (
    LenderCreate,
    LenderDetail,
    LenderResponse,
    LenderSummary,
    LenderUpdate,
)
from app.schemas.matching import (
    CriterionResult,
    LenderMatchResult,
    MatchingResultsResponse,
    MatchResultResponse,
    MatchResultSummary,
    ProgramEvaluationResult,
    RestrictionResult,
)

__all__ = [
    # Common
    "BaseSchema",
    "IDSchema",
    "TimestampSchema",
    "PaginatedResponse",
    "TransactionType",
    "EquipmentCategory",
    "EquipmentCondition",
    "ApplicationStatus",
    "EntityType",
    "BankruptcyChapter",
    # Business
    "BusinessCreate",
    "BusinessUpdate",
    "BusinessResponse",
    "BusinessSummary",
    # Guarantor
    "GuarantorCreate",
    "GuarantorUpdate",
    "GuarantorResponse",
    "GuarantorSummary",
    # Application (Domain)
    "EquipmentInput",
    "CreditHistoryInput",
    "LoanApplicationInput",
    "LoanApplicationCreate",
    "LoanApplicationResponse",
    "LoanApplicationSummary",
    "ApplicationStatusResponse",
    # Lender
    "LenderCreate",
    "LenderUpdate",
    "LenderResponse",
    "LenderSummary",
    "LenderDetail",
    # Matching (Domain)
    "CriterionResult",
    "MatchResultResponse",
    "MatchResultSummary",
    "MatchingResultsResponse",
    "LenderMatchResult",
    "ProgramEvaluationResult",
    "RestrictionResult",
    # API Request/Response - Applications
    "ApplicantInput",
    "BusinessInput",
    "ApiCreditHistoryInput",
    "ApiEquipmentInput",
    "LoanRequestInput",
    "BusinessCreditInput",
    "ApplicationSubmitRequest",
    "ApplicationSubmitResponse",
    "ApplicationListItem",
    "ApiApplicationStatusResponse",
    "CriterionResultResponse",
    "LenderMatchResponse",
    "ApiMatchingResultsResponse",
    "PaginatedListResponse",
    # API Request/Response - Lenders
    "ProgramSummary",
    "LenderListItem",
    "CriteriaDetail",
    "ProgramDetail",
    "RestrictionsDetail",
    "LenderDetailResponse",
    "LenderCreateRequest",
    "LenderUpdateRequest",
    "LenderStatusResponse",
]
