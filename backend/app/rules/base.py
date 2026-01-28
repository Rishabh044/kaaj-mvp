"""Base classes for the rule engine."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class EvaluationContext:
    """Contains all data needed for rule evaluation.

    This dataclass assembles data from the database models into a flat
    structure that rules can easily access for evaluation.
    """

    # Application Reference
    application_id: str

    # Credit Scores (Personal)
    fico_score: Optional[int] = None
    transunion_score: Optional[int] = None
    experian_score: Optional[int] = None
    equifax_score: Optional[int] = None

    # Credit Scores (Business)
    paynet_score: Optional[int] = None
    paynet_master_score: Optional[int] = None
    paydex_score: Optional[int] = None

    # Business Info
    business_name: str = ""
    years_in_business: float = 0.0
    industry_code: str = ""
    industry_name: str = ""
    state: str = ""
    annual_revenue: Optional[int] = None
    fleet_size: Optional[int] = None

    # Guarantor Info
    is_homeowner: bool = False
    is_us_citizen: bool = True
    has_cdl: bool = False
    cdl_years: Optional[int] = None
    industry_experience_years: Optional[int] = None

    # Credit History
    has_bankruptcy: bool = False
    bankruptcy_discharge_years: Optional[float] = None
    bankruptcy_chapter: Optional[str] = None
    has_open_judgements: bool = False
    judgement_amount: Optional[int] = None
    has_foreclosure: bool = False
    has_repossession: bool = False
    has_tax_liens: bool = False
    tax_lien_amount: Optional[int] = None

    # Loan Request
    loan_amount: int = 0
    requested_term_months: Optional[int] = None
    down_payment_percent: Optional[float] = None
    transaction_type: str = "purchase"
    is_private_party: bool = False

    # Equipment
    equipment_category: str = ""
    equipment_type: str = ""
    equipment_year: int = 0
    equipment_age_years: int = 0
    equipment_mileage: Optional[int] = None
    equipment_hours: Optional[int] = None
    equipment_condition: str = "used"

    def get_credit_score(self, score_type: str) -> Optional[int]:
        """Get a specific credit score by type."""
        score_map = {
            "fico": self.fico_score,
            "transunion": self.transunion_score,
            "experian": self.experian_score,
            "equifax": self.equifax_score,
            "paynet": self.paynet_score,
        }
        return score_map.get(score_type.lower())

    @property
    def is_trucking(self) -> bool:
        """Check if this is a trucking-related application."""
        trucking_categories = {"class_8_truck", "trailer", "semi", "truck"}
        return self.equipment_category.lower() in trucking_categories

    @property
    def is_startup(self) -> bool:
        """Check if business is considered a startup (less than 2 years)."""
        return self.years_in_business < 2.0


@dataclass
class RuleResult:
    """Output of a rule evaluation.

    Contains all information about whether a rule passed and why.
    """

    passed: bool
    rule_name: str
    required_value: str
    actual_value: str
    message: str
    score: float = 0.0  # 0-100 score contribution
    details: Optional[dict[str, Any]] = None

    def __post_init__(self):
        """Validate score bounds."""
        if self.score < 0:
            self.score = 0
        elif self.score > 100:
            self.score = 100

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "passed": self.passed,
            "rule_name": self.rule_name,
            "required_value": self.required_value,
            "actual_value": self.actual_value,
            "message": self.message,
            "score_contribution": self.score,
            "details": self.details,
        }


class Rule(ABC):
    """Abstract base class for all rules.

    Each rule evaluates one category of criteria (credit score, business
    requirements, equipment limits, etc.) and returns a RuleResult.
    """

    @property
    @abstractmethod
    def rule_type(self) -> str:
        """Return the type identifier for this rule."""
        ...

    @property
    def rule_name(self) -> str:
        """Return a human-readable name for this rule."""
        return self.rule_type.replace("_", " ").title()

    @abstractmethod
    def evaluate(
        self, context: EvaluationContext, criteria: dict[str, Any]
    ) -> RuleResult:
        """Evaluate the rule against the given context and criteria.

        Args:
            context: The evaluation context with all application data.
            criteria: The criteria configuration from the lender policy.

        Returns:
            A RuleResult indicating pass/fail with details.
        """
        ...

    def _create_passed_result(
        self,
        rule_name: str,
        required_value: str,
        actual_value: str,
        message: str,
        score: float = 100.0,
        details: Optional[dict[str, Any]] = None,
    ) -> RuleResult:
        """Helper to create a passing RuleResult."""
        return RuleResult(
            passed=True,
            rule_name=rule_name,
            required_value=required_value,
            actual_value=actual_value,
            message=message,
            score=score,
            details=details,
        )

    def _create_failed_result(
        self,
        rule_name: str,
        required_value: str,
        actual_value: str,
        message: str,
        details: Optional[dict[str, Any]] = None,
    ) -> RuleResult:
        """Helper to create a failing RuleResult."""
        return RuleResult(
            passed=False,
            rule_name=rule_name,
            required_value=required_value,
            actual_value=actual_value,
            message=message,
            score=0.0,
            details=details,
        )
