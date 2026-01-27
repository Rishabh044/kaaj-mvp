"""Credit history evaluation rules."""

from dataclasses import dataclass, field
from typing import Any, Optional

from app.rules.base import EvaluationContext, Rule, RuleResult
from app.rules.registry import RuleRegistry


@dataclass
class FailedCheck:
    """Represents a failed credit history check."""

    check: str
    required: str
    actual: str
    message: str

    def to_dict(self) -> dict[str, str]:
        """Convert to dictionary format."""
        return {
            "check": self.check,
            "required": self.required,
            "actual": self.actual,
            "message": self.message,
        }


@RuleRegistry.register("credit_history")
class CreditHistoryRule(Rule):
    """Evaluates credit history (bankruptcy, judgements, etc.)."""

    @property
    def rule_type(self) -> str:
        return "credit_history"

    def _check_bankruptcy(
        self, context: EvaluationContext, criteria: dict[str, Any]
    ) -> Optional[FailedCheck]:
        """Check bankruptcy status and discharge period."""
        if not context.has_bankruptcy:
            return None

        max_bankruptcies = criteria.get("max_bankruptcies", 999)
        if max_bankruptcies == 0:
            return FailedCheck(
                check="Bankruptcy",
                required="No bankruptcy history",
                actual=f"Has bankruptcy (Chapter {context.bankruptcy_chapter or 'Unknown'})",
                message="Bankruptcy not allowed",
            )

        min_discharge_years = criteria.get("bankruptcy_min_discharge_years", 0)

        if context.bankruptcy_discharge_years is None:
            return FailedCheck(
                check="Bankruptcy",
                required="No active bankruptcy",
                actual="Active/undischarged bankruptcy",
                message="Active bankruptcy not allowed",
            )

        if context.bankruptcy_discharge_years < min_discharge_years:
            return FailedCheck(
                check="Bankruptcy Discharge Period",
                required=f"Discharged {min_discharge_years}+ years ago",
                actual=f"Discharged {context.bankruptcy_discharge_years:.1f} years ago",
                message=(
                    f"Bankruptcy discharged {context.bankruptcy_discharge_years:.1f} "
                    f"years ago, minimum {min_discharge_years} years required"
                ),
            )

        return None

    def _check_open_judgements(
        self, context: EvaluationContext, criteria: dict[str, Any]
    ) -> Optional[FailedCheck]:
        """Check open judgements status and amount."""
        if not context.has_open_judgements:
            return None

        max_judgements = criteria.get("max_open_judgements", 999)
        if max_judgements == 0:
            amount_str = (
                f" (${context.judgement_amount:,})" if context.judgement_amount else ""
            )
            return FailedCheck(
                check="Open Judgements",
                required="No open judgements",
                actual=f"Has open judgements{amount_str}",
                message="Open judgements not allowed",
            )

        if context.judgement_amount:
            max_amount = criteria.get("max_judgement_amount")
            if max_amount and context.judgement_amount > max_amount:
                return FailedCheck(
                    check="Judgement Amount",
                    required=f"Max ${max_amount:,}",
                    actual=f"${context.judgement_amount:,}",
                    message=(
                        f"Judgement amount ${context.judgement_amount:,} "
                        f"exceeds maximum ${max_amount:,}"
                    ),
                )

        return None

    def _check_tax_liens(
        self, context: EvaluationContext, criteria: dict[str, Any]
    ) -> Optional[FailedCheck]:
        """Check tax liens status and amount."""
        if not context.has_tax_liens:
            return None

        max_liens = criteria.get("max_tax_liens", 999)
        if max_liens == 0:
            amount_str = (
                f" (${context.tax_lien_amount:,})" if context.tax_lien_amount else ""
            )
            return FailedCheck(
                check="Tax Liens",
                required="No tax liens",
                actual=f"Has tax liens{amount_str}",
                message="Tax liens not allowed",
            )

        if context.tax_lien_amount:
            max_amount = criteria.get("max_tax_lien_amount")
            if max_amount and context.tax_lien_amount > max_amount:
                return FailedCheck(
                    check="Tax Lien Amount",
                    required=f"Max ${max_amount:,}",
                    actual=f"${context.tax_lien_amount:,}",
                    message=(
                        f"Tax lien amount ${context.tax_lien_amount:,} "
                        f"exceeds maximum ${max_amount:,}"
                    ),
                )

        return None

    def _check_foreclosure(
        self, context: EvaluationContext, criteria: dict[str, Any]
    ) -> Optional[FailedCheck]:
        """Check foreclosure history."""
        if context.has_foreclosure and not criteria.get("allows_foreclosure", True):
            return FailedCheck(
                check="Foreclosure",
                required="No foreclosure history",
                actual="Has foreclosure",
                message="Foreclosure history not allowed",
            )
        return None

    def _check_repossession(
        self, context: EvaluationContext, criteria: dict[str, Any]
    ) -> Optional[FailedCheck]:
        """Check repossession history."""
        if context.has_repossession and not criteria.get("allows_repossession", True):
            return FailedCheck(
                check="Repossession",
                required="No repossession history",
                actual="Has repossession",
                message="Repossession history not allowed",
            )
        return None

    def _calculate_score(self, context: EvaluationContext) -> float:
        """Calculate score based on credit history cleanliness."""
        score = 100.0
        if context.has_bankruptcy and context.bankruptcy_discharge_years:
            penalty = max(0, 30 - context.bankruptcy_discharge_years * 3)
            score -= penalty
        return max(60, score)

    def _collect_failed_checks(
        self, context: EvaluationContext, criteria: dict[str, Any]
    ) -> list[FailedCheck]:
        """Run all checks and collect failures."""
        checks = [
            self._check_bankruptcy(context, criteria),
            self._check_open_judgements(context, criteria),
            self._check_tax_liens(context, criteria),
            self._check_foreclosure(context, criteria),
            self._check_repossession(context, criteria),
        ]
        return [check for check in checks if check is not None]

    def evaluate(
        self, context: EvaluationContext, criteria: dict[str, Any]
    ) -> RuleResult:
        """Evaluate credit history requirements.

        Args:
            context: The evaluation context.
            criteria: The criteria configuration containing any of:
                - max_bankruptcies: Maximum allowed bankruptcies (0 = none)
                - bankruptcy_min_discharge_years: Min years since discharge
                - max_open_judgements: Maximum open judgements (0 = none)
                - max_judgement_amount: Maximum judgement amount allowed
                - max_tax_liens: Maximum tax liens (0 = none)
                - max_tax_lien_amount: Maximum tax lien amount allowed
                - allows_foreclosure: Whether foreclosure is allowed
                - allows_repossession: Whether repossession is allowed

        Returns:
            RuleResult with pass/fail and score contribution.
        """
        failed_checks = self._collect_failed_checks(context, criteria)

        if failed_checks:
            first_failure = failed_checks[0]
            return self._create_failed_result(
                rule_name="Credit History",
                required_value=first_failure.required,
                actual_value=first_failure.actual,
                message=first_failure.message,
                details={"failed_checks": [fc.to_dict() for fc in failed_checks]},
            )

        return self._create_passed_result(
            rule_name="Credit History",
            required_value="Clean history",
            actual_value="Acceptable",
            message="Credit history meets requirements",
            score=self._calculate_score(context),
        )
