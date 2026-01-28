"""Credit score evaluation rules."""

from typing import Any, Optional

from app.rules.base import EvaluationContext, Rule, RuleResult
from app.rules.registry import RuleRegistry


@RuleRegistry.register("credit_score")
class CreditScoreRule(Rule):
    """Evaluates personal and business credit score requirements."""

    @property
    def rule_type(self) -> str:
        return "credit_score"

    def _get_score_from_context(
        self, context: EvaluationContext, score_type: str
    ) -> Optional[int]:
        """Retrieve the credit score from context based on type."""
        return context.get_credit_score(score_type)

    def _calculate_bonus_score(self, actual_score: int, min_score: int) -> float:
        """Calculate bonus points for exceeding the minimum score."""
        excess = actual_score - min_score
        bonus = min(30, excess * 0.3)  # Up to 30 bonus points
        return 70 + bonus

    def _build_rule_name(self, score_type: str) -> str:
        """Build the rule name for display."""
        return f"Minimum {score_type.title()} Score"

    def _handle_missing_score(
        self, rule_name: str, score_type: str, min_score: int
    ) -> RuleResult:
        """Handle the case when credit score is not provided."""
        return self._create_failed_result(
            rule_name=rule_name,
            required_value=str(min_score),
            actual_value="Not provided",
            message=f"{score_type.title()} credit score not provided",
        )

    def _handle_score_pass(
        self, rule_name: str, score_type: str, actual_score: int, min_score: int
    ) -> RuleResult:
        """Handle the case when credit score meets minimum."""
        score = self._calculate_bonus_score(actual_score, min_score)
        return self._create_passed_result(
            rule_name=rule_name,
            required_value=str(min_score),
            actual_value=str(actual_score),
            message=f"{score_type.title()} credit score {actual_score} meets minimum {min_score}",
            score=score,
        )

    def _handle_score_fail(
        self, rule_name: str, score_type: str, actual_score: int, min_score: int
    ) -> RuleResult:
        """Handle the case when credit score is below minimum."""
        return self._create_failed_result(
            rule_name=rule_name,
            required_value=str(min_score),
            actual_value=str(actual_score),
            message=f"{score_type.title()} credit score {actual_score} below minimum {min_score}",
        )

    def evaluate(
        self, context: EvaluationContext, criteria: dict[str, Any]
    ) -> RuleResult:
        """Evaluate credit score requirement.

        Args:
            context: The evaluation context.
            criteria: The criteria configuration containing:
                - type: The type of score to check (fico, transunion, paynet, etc.)
                - min: The minimum required score

        Returns:
            RuleResult with pass/fail and score contribution.
        """
        score_type = criteria.get("type", "fico")
        min_score = criteria.get("min", 0)
        rule_name = self._build_rule_name(score_type)

        actual_score = self._get_score_from_context(context, score_type)

        if actual_score is None:
            return self._handle_missing_score(rule_name, score_type, min_score)

        if actual_score >= min_score:
            return self._handle_score_pass(rule_name, score_type, actual_score, min_score)

        return self._handle_score_fail(rule_name, score_type, actual_score, min_score)