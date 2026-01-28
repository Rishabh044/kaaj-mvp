"""Pydantic models for validating lender policy YAML files."""

from typing import Optional, Union, Literal
from pydantic import BaseModel, Field, field_validator


class CreditScoreCriteria(BaseModel):
    """Credit score requirements for a program."""

    type: Literal["fico", "transunion", "paynet", "experian", "equifax"] = "fico"
    min: int = Field(ge=300, le=850, description="Minimum credit score required")

    @field_validator("min")
    @classmethod
    def validate_score_range(cls, v: int, info) -> int:
        """Validate score is in appropriate range for type."""
        score_type = info.data.get("type", "fico")
        if score_type == "paynet" and v > 100:
            # PayNet uses 1-100 scale typically, but some use higher
            pass
        return v


class BusinessCriteria(BaseModel):
    """Business-related requirements."""

    min_time_in_business_years: Optional[float] = Field(
        default=None, ge=0, description="Minimum years in business"
    )
    requires_homeowner: Optional[bool] = Field(
        default=None, description="Whether homeownership is required"
    )
    requires_cdl: Optional[Union[bool, Literal["conditional"]]] = Field(
        default=None, description="CDL requirement: true, false, or conditional"
    )
    min_cdl_years: Optional[int] = Field(
        default=None, ge=0, description="Minimum years holding CDL"
    )
    min_industry_experience_years: Optional[int] = Field(
        default=None, ge=0, description="Minimum years of industry experience"
    )
    min_fleet_size: Optional[int] = Field(
        default=None, ge=0, description="Minimum fleet size for trucking"
    )
    requires_us_citizen: Optional[bool] = Field(
        default=None, description="Whether US citizenship is required"
    )


class CreditHistoryCriteria(BaseModel):
    """Credit history requirements."""

    max_bankruptcies: Optional[int] = Field(
        default=None, ge=0, description="Maximum allowed bankruptcies"
    )
    bankruptcy_min_discharge_years: Optional[float] = Field(
        default=None, ge=0, description="Minimum years since bankruptcy discharge"
    )
    allows_active_bankruptcy: bool = Field(
        default=False, description="Whether active bankruptcy is allowed"
    )
    max_open_judgements: Optional[int] = Field(
        default=None, ge=0, description="Maximum allowed open judgements"
    )
    max_judgement_amount: Optional[int] = Field(
        default=None, ge=0, description="Maximum total judgement amount in cents"
    )
    allows_foreclosure: Optional[bool] = Field(
        default=None, description="Whether foreclosure history is allowed"
    )
    allows_repossession: Optional[bool] = Field(
        default=None, description="Whether repossession history is allowed"
    )
    max_tax_liens: Optional[int] = Field(
        default=None, ge=0, description="Maximum allowed tax liens"
    )
    max_collections_years: Optional[int] = Field(
        default=None, ge=0, description="No collections within this many years"
    )


class EquipmentCriteria(BaseModel):
    """Equipment-related requirements."""

    max_age_years: Optional[int] = Field(
        default=None, ge=0, description="Maximum equipment age in years"
    )
    max_mileage: Optional[int] = Field(
        default=None, ge=0, description="Maximum mileage for vehicles"
    )
    max_hours: Optional[int] = Field(
        default=None, ge=0, description="Maximum hours for equipment"
    )
    allowed_categories: Optional[list[str]] = Field(
        default=None, description="List of allowed equipment categories"
    )
    excluded_categories: Optional[list[str]] = Field(
        default=None, description="List of excluded equipment categories"
    )


class GeographicCriteria(BaseModel):
    """Geographic restrictions."""

    allowed_states: Optional[list[str]] = Field(
        default=None, description="List of allowed US states (2-letter codes)"
    )
    excluded_states: Optional[list[str]] = Field(
        default=None, description="List of excluded US states (2-letter codes)"
    )

    @field_validator("allowed_states", "excluded_states")
    @classmethod
    def normalize_states(cls, v: Optional[list[str]]) -> Optional[list[str]]:
        """Normalize state codes to uppercase."""
        if v is None:
            return None
        return [s.upper() for s in v]


class IndustryCriteria(BaseModel):
    """Industry restrictions."""

    allowed_industries: Optional[list[str]] = Field(
        default=None, description="List of allowed industry codes/names"
    )
    excluded_industries: Optional[list[str]] = Field(
        default=None, description="List of excluded industry codes/names"
    )


class TransactionCriteria(BaseModel):
    """Transaction type restrictions."""

    allowed_types: Optional[list[str]] = Field(
        default=None, description="Allowed transaction types"
    )
    excluded_types: Optional[list[str]] = Field(
        default=None, description="Excluded transaction types"
    )
    allows_private_party: bool = Field(
        default=True, description="Whether private party sales are allowed"
    )
    allows_sale_leaseback: bool = Field(
        default=True, description="Whether sale-leaseback is allowed"
    )
    allows_refinance: bool = Field(
        default=True, description="Whether refinance transactions are allowed"
    )


class LoanAmountCriteria(BaseModel):
    """Loan amount limits."""

    min_amount: Optional[int] = Field(
        default=None, ge=0, description="Minimum loan amount in cents"
    )
    max_amount: Optional[int] = Field(
        default=None, ge=0, description="Maximum loan amount in cents"
    )


class ProgramCriteria(BaseModel):
    """All criteria for evaluating a program."""

    credit_score: Optional[CreditScoreCriteria] = None
    business: Optional[BusinessCriteria] = None
    credit_history: Optional[CreditHistoryCriteria] = None
    equipment: Optional[EquipmentCriteria] = None
    geographic: Optional[GeographicCriteria] = None
    industry: Optional[IndustryCriteria] = None
    transaction: Optional[TransactionCriteria] = None
    loan_amount: Optional[LoanAmountCriteria] = None


class LenderProgram(BaseModel):
    """A specific lending program offered by a lender."""

    id: str = Field(description="Unique program identifier")
    name: str = Field(description="Human-readable program name")
    description: Optional[str] = Field(
        default=None, description="Detailed program description"
    )
    is_app_only: bool = Field(
        default=False, description="Whether this is an application-only program"
    )
    min_amount: Optional[int] = Field(
        default=None, ge=0, description="Program minimum loan amount in cents"
    )
    max_amount: Optional[int] = Field(
        default=None, ge=0, description="Program maximum loan amount in cents"
    )
    max_term_months: Optional[int] = Field(
        default=None, ge=1, description="Maximum loan term in months"
    )
    criteria: ProgramCriteria = Field(
        default_factory=ProgramCriteria, description="Program eligibility criteria"
    )

    @field_validator("id")
    @classmethod
    def validate_program_id(cls, v: str) -> str:
        """Validate program ID format."""
        if not v.replace("_", "").replace("-", "").isalnum():
            raise ValueError("Program ID must be alphanumeric with underscores/hyphens")
        return v.lower()


class EquipmentTermEntry(BaseModel):
    """Single entry in equipment term matrix."""

    min_year: Optional[int] = Field(default=None, description="Minimum model year")
    max_year: Optional[int] = Field(default=None, description="Maximum model year")
    min_mileage: Optional[int] = Field(default=None, ge=0, description="Min mileage")
    max_mileage: Optional[int] = Field(default=None, ge=0, description="Max mileage")
    term_months: int = Field(ge=1, description="Maximum term in months")


class EquipmentTermMatrix(BaseModel):
    """Term matrix for equipment categories."""

    category: str = Field(description="Equipment category name")
    entries: list[EquipmentTermEntry] = Field(
        description="List of term entries for this category"
    )


class LenderRestrictions(BaseModel):
    """Global restrictions that apply to all programs."""

    geographic: Optional[GeographicCriteria] = None
    industry: Optional[IndustryCriteria] = None
    transaction: Optional[TransactionCriteria] = None
    equipment: Optional[EquipmentCriteria] = None


class ScoringConfig(BaseModel):
    """Configuration for fit score calculation."""

    credit_score_weight: float = Field(
        default=0.3, ge=0, le=1, description="Weight for credit score in fit score"
    )
    time_in_business_weight: float = Field(
        default=0.2, ge=0, le=1, description="Weight for TIB in fit score"
    )
    loan_amount_weight: float = Field(
        default=0.2, ge=0, le=1, description="Weight for loan amount fit"
    )
    equipment_fit_weight: float = Field(
        default=0.15, ge=0, le=1, description="Weight for equipment fit"
    )
    credit_history_weight: float = Field(
        default=0.15, ge=0, le=1, description="Weight for credit history"
    )


class LenderPolicy(BaseModel):
    """Complete lender policy configuration."""

    id: str = Field(description="Unique lender identifier")
    name: str = Field(description="Lender display name")
    version: int = Field(ge=1, description="Policy version number")
    description: Optional[str] = Field(
        default=None, description="Lender description"
    )
    contact_email: Optional[str] = Field(
        default=None, description="Contact email for submissions"
    )
    contact_phone: Optional[str] = Field(
        default=None, description="Contact phone number"
    )
    programs: list[LenderProgram] = Field(
        description="List of lending programs offered"
    )
    equipment_matrices: Optional[list[EquipmentTermMatrix]] = Field(
        default=None, description="Equipment term matrices"
    )
    restrictions: Optional[LenderRestrictions] = Field(
        default=None, description="Global restrictions for all programs"
    )
    scoring: Optional[ScoringConfig] = Field(
        default=None, description="Custom scoring configuration"
    )

    @field_validator("id")
    @classmethod
    def validate_lender_id(cls, v: str) -> str:
        """Validate lender ID format (matches YAML filename)."""
        if not v.replace("_", "").isalnum():
            raise ValueError("Lender ID must be alphanumeric with underscores")
        return v.lower()

    @field_validator("programs")
    @classmethod
    def validate_unique_program_ids(
        cls, v: list[LenderProgram]
    ) -> list[LenderProgram]:
        """Ensure program IDs are unique within lender."""
        ids = [p.id for p in v]
        if len(ids) != len(set(ids)):
            raise ValueError("Program IDs must be unique within a lender")
        return v
