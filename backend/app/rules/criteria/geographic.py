"""Geographic restriction rules."""

from typing import Any, Optional

from app.rules.base import EvaluationContext, Rule, RuleResult
from app.rules.registry import RuleRegistry


@RuleRegistry.register("geographic")
class StateRestrictionRule(Rule):
    """Evaluates state/geographic restrictions."""

    @property
    def rule_type(self) -> str:
        return "geographic"

    def _normalize_state_list(self, states: list[str]) -> list[str]:
        """Normalize state codes to uppercase."""
        return [s.upper() for s in states]

    def _check_excluded_states(
        self, state: str, excluded_states: list[str]
    ) -> Optional[RuleResult]:
        """Check if state is in the exclusion list."""
        if not excluded_states:
            return None

        excluded_upper = self._normalize_state_list(excluded_states)
        if state in excluded_upper:
            return self._create_failed_result(
                rule_name="State Restriction",
                required_value=f"Not in {', '.join(excluded_upper)}",
                actual_value=state,
                message=f"State {state} is excluded from this program",
            )
        return None

    def _check_allowed_states(
        self, state: str, allowed_states: list[str]
    ) -> Optional[RuleResult]:
        """Check if state is in the allowed list."""
        if not allowed_states:
            return None

        allowed_upper = self._normalize_state_list(allowed_states)
        if state not in allowed_upper:
            return self._create_failed_result(
                rule_name="State Restriction",
                required_value=f"One of {', '.join(allowed_upper)}",
                actual_value=state,
                message=f"State {state} is not in the allowed states list",
            )
        return None

    def _create_success_result(self, state: str) -> RuleResult:
        """Create a success result for allowed state."""
        return self._create_passed_result(
            rule_name="State Restriction",
            required_value="Allowed state",
            actual_value=state,
            message=f"State {state} is allowed",
            score=100,
        )

    def evaluate(
        self, context: EvaluationContext, criteria: dict[str, Any]
    ) -> RuleResult:
        """Evaluate geographic restrictions.

        Args:
            context: The evaluation context.
            criteria: The criteria configuration containing any of:
                - excluded_states: List of state codes that are not allowed
                - allowed_states: List of state codes that are allowed (if set,
                  only these states are allowed)

        Returns:
            RuleResult with pass/fail.
        """
        state = context.state.upper()

        # Check excluded states first
        excluded_result = self._check_excluded_states(
            state, criteria.get("excluded_states", [])
        )
        if excluded_result:
            return excluded_result

        # Check allowed states if specified
        allowed_result = self._check_allowed_states(
            state, criteria.get("allowed_states", [])
        )
        if allowed_result:
            return allowed_result

        return self._create_success_result(state)


@RuleRegistry.register("state_exclusion")
class StateExclusionRule(StateRestrictionRule):
    """Alias for state restriction rule focusing on exclusions."""

    @property
    def rule_type(self) -> str:
        return "state_exclusion"
