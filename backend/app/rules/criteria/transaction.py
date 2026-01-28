"""Transaction type evaluation rules."""

from typing import Any, Optional

from app.rules.base import EvaluationContext, Rule, RuleResult
from app.rules.registry import RuleRegistry


@RuleRegistry.register("transaction")
class TransactionTypeRule(Rule):
    """Evaluates transaction type and private party restrictions."""

    @property
    def rule_type(self) -> str:
        return "transaction"

    def _format_transaction_type(self, transaction_type: str) -> str:
        """Format transaction type for display."""
        return transaction_type.replace("_", " ").title()

    def _get_allowed_types_map(self, criteria: dict[str, Any]) -> dict[str, bool]:
        """Build map of transaction types to their allowed status."""
        return {
            "purchase": criteria.get("purchase", True),
            "refinance": criteria.get("refinance", True),
            "sale_leaseback": criteria.get("sale_leaseback", True),
        }

    def _check_transaction_type(
        self, transaction_type: str, criteria: dict[str, Any]
    ) -> Optional[RuleResult]:
        """Check if the transaction type is allowed."""
        type_map = self._get_allowed_types_map(criteria)
        formatted_type = self._format_transaction_type(transaction_type)

        if transaction_type not in type_map:
            return self._create_failed_result(
                rule_name="Transaction Type",
                required_value="Valid transaction type",
                actual_value=transaction_type,
                message=f"Unknown transaction type: {transaction_type}",
            )

        if not type_map[transaction_type]:
            return self._create_failed_result(
                rule_name="Transaction Type",
                required_value="Allowed transaction type",
                actual_value=formatted_type,
                message=f"{formatted_type} transactions not allowed",
            )

        return None

    def _check_private_party(
        self, is_private_party: bool, criteria: dict[str, Any]
    ) -> Optional[RuleResult]:
        """Check if private party sale is allowed."""
        if not is_private_party:
            return None

        allows_private_party = criteria.get("private_party", True)
        if not allows_private_party:
            return self._create_failed_result(
                rule_name="Private Party Restriction",
                required_value="Not private party sale",
                actual_value="Private party sale",
                message="Private party sales are not allowed",
            )

        return None

    def _create_success_result(self, transaction_type: str) -> RuleResult:
        """Create a success result for allowed transaction."""
        formatted_type = self._format_transaction_type(transaction_type)
        return self._create_passed_result(
            rule_name="Transaction Type",
            required_value="Valid transaction",
            actual_value=formatted_type,
            message=f"{formatted_type} transaction is allowed",
            score=100,
        )

    def evaluate(
        self, context: EvaluationContext, criteria: dict[str, Any]
    ) -> RuleResult:
        """Evaluate transaction type requirements.

        Args:
            context: The evaluation context.
            criteria: The criteria configuration containing any of:
                - purchase: Whether purchase transactions are allowed
                - refinance: Whether refinance transactions are allowed
                - sale_leaseback: Whether sale-leaseback transactions are allowed
                - private_party: Whether private party sales are allowed

        Returns:
            RuleResult with pass/fail.
        """
        transaction_type = context.transaction_type.lower()

        # Check transaction type
        type_result = self._check_transaction_type(transaction_type, criteria)
        if type_result:
            return type_result

        # Check private party restriction
        private_result = self._check_private_party(context.is_private_party, criteria)
        if private_result:
            return private_result

        return self._create_success_result(transaction_type)


@RuleRegistry.register("private_party")
class PrivatePartyRule(Rule):
    """Evaluates private party sale restrictions specifically."""

    @property
    def rule_type(self) -> str:
        return "private_party"

    def _get_sale_type_display(self, is_private_party: bool) -> str:
        """Get display string for sale type."""
        return "Private party" if is_private_party else "Dealer"

    def _check_private_party_allowed(
        self, is_private_party: bool, allowed: bool
    ) -> Optional[RuleResult]:
        """Check if private party sale is allowed when applicable."""
        if is_private_party and not allowed:
            return self._create_failed_result(
                rule_name="Private Party Restriction",
                required_value="Dealer sale only",
                actual_value="Private party sale",
                message="Private party sales are not allowed for this program",
            )
        return None

    def _create_success_result(self, is_private_party: bool) -> RuleResult:
        """Create success result for acceptable sale type."""
        return self._create_passed_result(
            rule_name="Private Party Restriction",
            required_value="Any sale type",
            actual_value=self._get_sale_type_display(is_private_party),
            message="Sale type is acceptable",
            score=100,
        )

    def evaluate(
        self, context: EvaluationContext, criteria: dict[str, Any]
    ) -> RuleResult:
        """Evaluate private party restrictions.

        Args:
            context: The evaluation context.
            criteria: The criteria configuration containing:
                - allowed: Whether private party sales are allowed

        Returns:
            RuleResult with pass/fail.
        """
        allowed = criteria.get("allowed", True)

        failure = self._check_private_party_allowed(context.is_private_party, allowed)
        if failure:
            return failure

        return self._create_success_result(context.is_private_party)
