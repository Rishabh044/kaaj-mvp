"""Pydantic schemas for API request/response validation."""

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
    # Application
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
    # Matching
    "CriterionResult",
    "MatchResultResponse",
    "MatchResultSummary",
    "MatchingResultsResponse",
    "LenderMatchResult",
    "ProgramEvaluationResult",
    "RestrictionResult",
]
