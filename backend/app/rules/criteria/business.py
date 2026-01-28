"""Business requirements evaluation rules."""

from dataclasses import dataclass, field
from typing import Any

from app.rules.base import EvaluationContext, Rule, RuleResult
from app.rules.registry import RuleRegistry


@dataclass
class CheckResult:
    """Result of a single requirement check."""

    passed: bool
    score: float = 0.0
    max_score: float = 0.0
    message: str = ""
    check_name: str = ""
    required: str = ""
    actual: str = ""


@dataclass
class AggregatedChecks:
    """Aggregated results from all requirement checks."""

    failed_checks: list[dict[str, str]] = field(default_factory=list)
    passed_checks: list[str] = field(default_factory=list)
    total_score: float = 0.0
    max_possible: float = 0.0

    def add_result(self, result: CheckResult) -> None:
        """Add a check result to the aggregation."""
        self.max_possible += result.max_score
        if result.passed:
            self.total_score += result.score
            self.passed_checks.append(result.message)
        else:
            self.failed_checks.append({
                "check": result.check_name,
                "required": result.required,
                "actual": result.actual,
                "message": result.message,
            })


@RuleRegistry.register("business")
class BusinessRequirementsRule(Rule):
    """Evaluates business requirements (TIB, homeowner, CDL, etc.)."""

    @property
    def rule_type(self) -> str:
        return "business"

    def _check_time_in_business(
        self, context: EvaluationContext, min_tib: float
    ) -> CheckResult:
        """Check if business meets minimum time in business requirement."""
        if context.years_in_business >= min_tib:
            bonus = min(25, (context.years_in_business - min_tib) * 5)
            return CheckResult(
                passed=True,
                score=bonus,
                max_score=25,
                message=(
                    f"Time in business {context.years_in_business:.1f} years "
                    f"meets minimum {min_tib} years"
                ),
            )
        return CheckResult(
            passed=False,
            max_score=25,
            check_name="Time in Business",
            required=f"{min_tib} years",
            actual=f"{context.years_in_business:.1f} years",
            message=(
                f"Time in business {context.years_in_business:.1f} years "
                f"below minimum {min_tib} years"
            ),
        )

    def _check_homeowner(self, context: EvaluationContext) -> CheckResult:
        """Check if applicant meets homeowner requirement."""
        if context.is_homeowner:
            return CheckResult(
                passed=True,
                score=15,
                max_score=15,
                message="Homeowner requirement met",
            )
        return CheckResult(
            passed=False,
            max_score=15,
            check_name="Homeownership",
            required="Must be homeowner",
            actual="Not a homeowner",
            message="Applicant is not a homeowner (required)",
        )

    def _check_cdl(self, context: EvaluationContext) -> CheckResult:
        """Check if applicant has required CDL license."""
        if context.has_cdl:
            return CheckResult(
                passed=True,
                score=10,
                max_score=10,
                message="CDL requirement met",
            )
        return CheckResult(
            passed=False,
            max_score=10,
            check_name="CDL License",
            required="Must have CDL",
            actual="No CDL",
            message="CDL license required but not held",
        )

    def _check_cdl_years(
        self, context: EvaluationContext, min_cdl_years: int
    ) -> CheckResult:
        """Check if applicant has minimum CDL experience."""
        if context.cdl_years and context.cdl_years >= min_cdl_years:
            return CheckResult(
                passed=True,
                score=15,
                max_score=15,
                message=(
                    f"CDL experience {context.cdl_years} years "
                    f"meets minimum {min_cdl_years} years"
                ),
            )
        actual = f"{context.cdl_years} years" if context.cdl_years else "No CDL"
        return CheckResult(
            passed=False,
            max_score=15,
            check_name="CDL Experience",
            required=f"{min_cdl_years} years",
            actual=actual,
            message=f"CDL experience {actual} below minimum {min_cdl_years} years",
        )

    def _check_industry_experience(
        self, context: EvaluationContext, min_exp: int
    ) -> CheckResult:
        """Check if applicant has minimum industry experience."""
        if (
            context.industry_experience_years
            and context.industry_experience_years >= min_exp
        ):
            return CheckResult(
                passed=True,
                score=15,
                max_score=15,
                message=(
                    f"Industry experience {context.industry_experience_years} years "
                    f"meets minimum {min_exp} years"
                ),
            )
        actual = (
            f"{context.industry_experience_years} years"
            if context.industry_experience_years
            else "Not provided"
        )
        return CheckResult(
            passed=False,
            max_score=15,
            check_name="Industry Experience",
            required=f"{min_exp} years",
            actual=actual,
            message=f"Industry experience {actual} below minimum {min_exp} years",
        )

    def _check_fleet_size(
        self, context: EvaluationContext, min_fleet: int
    ) -> CheckResult:
        """Check if business has minimum fleet size."""
        if context.fleet_size and context.fleet_size >= min_fleet:
            return CheckResult(
                passed=True,
                score=10,
                max_score=10,
                message=f"Fleet size {context.fleet_size} meets minimum {min_fleet}",
            )
        actual = str(context.fleet_size) if context.fleet_size else "0"
        return CheckResult(
            passed=False,
            max_score=10,
            check_name="Fleet Size",
            required=f"Minimum {min_fleet}",
            actual=actual,
            message=f"Fleet size {actual} below minimum {min_fleet}",
        )

    def _check_annual_revenue(
        self, context: EvaluationContext, min_revenue: int
    ) -> CheckResult:
        """Check if business meets minimum annual revenue."""
        if context.annual_revenue and context.annual_revenue >= min_revenue:
            return CheckResult(
                passed=True,
                score=10,
                max_score=10,
                message=(
                    f"Annual revenue ${context.annual_revenue:,} "
                    f"meets minimum ${min_revenue:,}"
                ),
            )
        actual = (
            f"${context.annual_revenue:,}" if context.annual_revenue else "Not provided"
        )
        return CheckResult(
            passed=False,
            max_score=10,
            check_name="Annual Revenue",
            required=f"${min_revenue:,}",
            actual=actual,
            message=f"Annual revenue {actual} below minimum ${min_revenue:,}",
        )

    def _is_cdl_required(self, criteria: dict[str, Any], context: EvaluationContext) -> bool:
        """Determine if CDL is required based on criteria and context."""
        cdl_required = criteria.get("requires_cdl")
        if cdl_required == "conditional" and context.is_trucking:
            return True
        return cdl_required is True

    def evaluate(
        self, context: EvaluationContext, criteria: dict[str, Any]
    ) -> RuleResult:
        """Evaluate business requirements.

        Args:
            context: The evaluation context.
            criteria: The criteria configuration containing any of:
                - min_time_in_business_years: Minimum years in business
                - requires_homeowner: Whether homeownership is required
                - requires_cdl: True, False, or "conditional" (required for trucking)
                - min_cdl_years: Minimum years with CDL
                - min_industry_experience_years: Minimum industry experience
                - min_fleet_size: Minimum fleet size (for trucking)
                - min_annual_revenue: Minimum annual revenue

        Returns:
            RuleResult with pass/fail and score contribution.
        """
        checks = AggregatedChecks()

        # Run each applicable check
        if "min_time_in_business_years" in criteria:
            min_tib = float(criteria["min_time_in_business_years"])
            checks.add_result(self._check_time_in_business(context, min_tib))

        if criteria.get("requires_homeowner"):
            checks.add_result(self._check_homeowner(context))

        if self._is_cdl_required(criteria, context):
            checks.add_result(self._check_cdl(context))

        if "min_cdl_years" in criteria:
            min_cdl_years = int(criteria["min_cdl_years"])
            checks.add_result(self._check_cdl_years(context, min_cdl_years))

        if "min_industry_experience_years" in criteria:
            min_exp = int(criteria["min_industry_experience_years"])
            checks.add_result(self._check_industry_experience(context, min_exp))

        if "min_fleet_size" in criteria:
            min_fleet = int(criteria["min_fleet_size"])
            checks.add_result(self._check_fleet_size(context, min_fleet))

        if "min_annual_revenue" in criteria:
            min_revenue = int(criteria["min_annual_revenue"])
            checks.add_result(self._check_annual_revenue(context, min_revenue))

        return self._build_result(checks)

    def _build_result(self, checks: AggregatedChecks) -> RuleResult:
        """Build the final RuleResult from aggregated checks."""
        if checks.failed_checks:
            return self._create_failed_result(
                rule_name="Business Requirements",
                required_value="; ".join([f["required"] for f in checks.failed_checks]),
                actual_value="; ".join([f["actual"] for f in checks.failed_checks]),
                message=checks.failed_checks[0]["message"],
                details={
                    "failed_checks": checks.failed_checks,
                    "passed_checks": checks.passed_checks,
                },
            )

        normalized_score = (
            (checks.total_score / checks.max_possible * 100)
            if checks.max_possible > 0
            else 100
        )

        return self._create_passed_result(
            rule_name="Business Requirements",
            required_value="All met",
            actual_value="All met",
            message="All business requirements satisfied",
            score=normalized_score,
            details={"passed_checks": checks.passed_checks},
        )
