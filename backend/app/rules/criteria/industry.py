"""Industry restriction rules."""

from typing import Any, Optional

from app.rules.base import EvaluationContext, Rule, RuleResult
from app.rules.registry import RuleRegistry


@RuleRegistry.register("industry")
class IndustryExclusionRule(Rule):
    """Evaluates industry exclusions."""

    @property
    def rule_type(self) -> str:
        return "industry"

    def _normalize_list(self, items: list[str]) -> list[str]:
        """Normalize list items to lowercase."""
        return [i.lower() for i in items]

    def _matches_any(
        self, industry_code: str, industry_name: str, patterns: list[str]
    ) -> bool:
        """Check if industry code or name matches any pattern."""
        for pattern in patterns:
            if pattern in industry_code or pattern in industry_name:
                return True
        return False

    def _check_excluded_industries(
        self,
        industry_code: str,
        industry_name: str,
        original_name: str,
        excluded_industries: list[str],
    ) -> Optional[RuleResult]:
        """Check if industry is in the exclusion list."""
        if not excluded_industries:
            return None

        excluded_lower = self._normalize_list(excluded_industries)
        if self._matches_any(industry_code, industry_name, excluded_lower):
            return self._create_failed_result(
                rule_name="Industry Restriction",
                required_value="Not in excluded industries",
                actual_value=original_name,
                message=f"Industry '{original_name}' is excluded from this program",
            )
        return None

    def _check_allowed_industries(
        self,
        industry_code: str,
        industry_name: str,
        original_name: str,
        allowed_industries: list[str],
    ) -> Optional[RuleResult]:
        """Check if industry is in the allowed list."""
        if not allowed_industries:
            return None

        allowed_lower = self._normalize_list(allowed_industries)
        if not self._matches_any(industry_code, industry_name, allowed_lower):
            return self._create_failed_result(
                rule_name="Industry Restriction",
                required_value=f"One of: {', '.join(allowed_industries)}",
                actual_value=original_name,
                message=f"Industry '{original_name}' is not in the allowed list",
            )
        return None

    def _create_success_result(self, industry_name: str) -> RuleResult:
        """Create a success result for allowed industry."""
        return self._create_passed_result(
            rule_name="Industry Restriction",
            required_value="Allowed industry",
            actual_value=industry_name,
            message=f"Industry '{industry_name}' is allowed",
            score=100,
        )

    def evaluate(
        self, context: EvaluationContext, criteria: dict[str, Any]
    ) -> RuleResult:
        """Evaluate industry restrictions.

        Args:
            context: The evaluation context.
            criteria: The criteria configuration containing any of:
                - excluded_industries: List of industry names or codes excluded
                - allowed_industries: List of industry names or codes allowed

        Returns:
            RuleResult with pass/fail.
        """
        industry_code = context.industry_code.lower()
        industry_name = context.industry_name.lower()
        original_name = context.industry_name

        # Check excluded industries
        excluded_result = self._check_excluded_industries(
            industry_code,
            industry_name,
            original_name,
            criteria.get("excluded_industries", []),
        )
        if excluded_result:
            return excluded_result

        # Check allowed industries if specified
        allowed_result = self._check_allowed_industries(
            industry_code,
            industry_name,
            original_name,
            criteria.get("allowed_industries", []),
        )
        if allowed_result:
            return allowed_result

        return self._create_success_result(original_name)


# Common excluded industries for convenience
COMMON_EXCLUDED_INDUSTRIES = [
    "cannabis",
    "marijuana",
    "gambling",
    "casino",
    "adult_entertainment",
    "adult",
    "firearms",
    "weapons",
    "tobacco",
    "payday_lending",
]
