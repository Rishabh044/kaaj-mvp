"""Loan amount evaluation rules."""

from typing import Any, Optional

from app.rules.base import EvaluationContext, Rule, RuleResult
from app.rules.registry import RuleRegistry


@RuleRegistry.register("loan_amount")
class LoanAmountRule(Rule):
    """Evaluates loan amount requirements."""

    @property
    def rule_type(self) -> str:
        return "loan_amount"

    def _cents_to_dollars(self, cents: int) -> float:
        """Convert cents to dollars."""
        return cents / 100

    def _format_dollars(self, dollars: float) -> str:
        """Format dollar amount for display."""
        return f"${dollars:,.0f}"

    def _check_minimum(
        self, loan_amount: int, loan_dollars: float, min_amount: Optional[int]
    ) -> Optional[RuleResult]:
        """Check if loan amount meets minimum requirement."""
        if min_amount is None or loan_amount >= min_amount:
            return None

        min_dollars = self._cents_to_dollars(min_amount)
        return self._create_failed_result(
            rule_name="Minimum Loan Amount",
            required_value=self._format_dollars(min_dollars),
            actual_value=self._format_dollars(loan_dollars),
            message=f"Loan amount {self._format_dollars(loan_dollars)} below minimum {self._format_dollars(min_dollars)}",
        )

    def _check_maximum(
        self, loan_amount: int, loan_dollars: float, max_amount: Optional[int]
    ) -> Optional[RuleResult]:
        """Check if loan amount is within maximum limit."""
        if max_amount is None or loan_amount <= max_amount:
            return None

        max_dollars = self._cents_to_dollars(max_amount)
        return self._create_failed_result(
            rule_name="Maximum Loan Amount",
            required_value=self._format_dollars(max_dollars),
            actual_value=self._format_dollars(loan_dollars),
            message=f"Loan amount {self._format_dollars(loan_dollars)} exceeds maximum {self._format_dollars(max_dollars)}",
        )

    def _build_range_string(
        self, min_amount: Optional[int], max_amount: Optional[int]
    ) -> str:
        """Build a formatted range string for display."""
        min_str = (
            self._format_dollars(self._cents_to_dollars(min_amount))
            if min_amount is not None
            else "$0"
        )
        max_str = (
            self._format_dollars(self._cents_to_dollars(max_amount))
            if max_amount is not None
            else "unlimited"
        )
        return f"{min_str} - {max_str}"

    def _create_success_result(
        self,
        loan_dollars: float,
        min_amount: Optional[int],
        max_amount: Optional[int],
    ) -> RuleResult:
        """Create a success result for valid loan amount."""
        return self._create_passed_result(
            rule_name="Loan Amount",
            required_value=self._build_range_string(min_amount, max_amount),
            actual_value=self._format_dollars(loan_dollars),
            message=f"Loan amount {self._format_dollars(loan_dollars)} within allowed range",
            score=100,
        )

    def evaluate(
        self, context: EvaluationContext, criteria: dict[str, Any]
    ) -> RuleResult:
        """Evaluate loan amount requirements.

        Args:
            context: The evaluation context.
            criteria: The criteria configuration containing any of:
                - min_amount: Minimum loan amount in cents
                - max_amount: Maximum loan amount in cents

        Returns:
            RuleResult with pass/fail.
        """
        loan_amount = context.loan_amount
        loan_dollars = self._cents_to_dollars(loan_amount)
        min_amount = criteria.get("min_amount")
        max_amount = criteria.get("max_amount")

        # Check minimum
        min_result = self._check_minimum(loan_amount, loan_dollars, min_amount)
        if min_result:
            return min_result

        # Check maximum
        max_result = self._check_maximum(loan_amount, loan_dollars, max_amount)
        if max_result:
            return max_result

        return self._create_success_result(loan_dollars, min_amount, max_amount)


@RuleRegistry.register("min_amount")
class MinAmountRule(LoanAmountRule):
    """Minimum loan amount rule."""

    @property
    def rule_type(self) -> str:
        return "min_amount"


@RuleRegistry.register("max_amount")
class MaxAmountRule(LoanAmountRule):
    """Maximum loan amount rule."""

    @property
    def rule_type(self) -> str:
        return "max_amount"
