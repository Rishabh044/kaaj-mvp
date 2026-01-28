"""Equipment evaluation rules."""

from dataclasses import dataclass
from typing import Any, Optional

from app.rules.base import EvaluationContext, Rule, RuleResult
from app.rules.registry import RuleRegistry


@dataclass
class EquipmentCheckResult:
    """Result of an equipment check."""

    passed: bool
    check_name: str = ""
    required: str = ""
    actual: str = ""
    message: str = ""


@RuleRegistry.register("equipment")
class EquipmentRule(Rule):
    """Evaluates equipment age, mileage, and hours requirements."""

    @property
    def rule_type(self) -> str:
        return "equipment"

    def _check_age(
        self, context: EvaluationContext, max_age: int
    ) -> EquipmentCheckResult:
        """Check if equipment age is within limit."""
        if context.equipment_age_years > max_age:
            return EquipmentCheckResult(
                passed=False,
                check_name="Equipment Age",
                required=f"Max {max_age} years",
                actual=f"{context.equipment_age_years} years",
                message=(
                    f"Equipment age {context.equipment_age_years} years "
                    f"exceeds maximum {max_age} years"
                ),
            )
        return EquipmentCheckResult(
            passed=True,
            message=(
                f"Equipment age {context.equipment_age_years} years "
                f"within limit of {max_age} years"
            ),
        )

    def _check_mileage(
        self, context: EvaluationContext, max_mileage: int
    ) -> Optional[EquipmentCheckResult]:
        """Check if equipment mileage is within limit."""
        if context.equipment_mileage is None:
            return None

        if context.equipment_mileage > max_mileage:
            return EquipmentCheckResult(
                passed=False,
                check_name="Equipment Mileage",
                required=f"Max {max_mileage:,} miles",
                actual=f"{context.equipment_mileage:,} miles",
                message=(
                    f"Equipment mileage {context.equipment_mileage:,} "
                    f"exceeds maximum {max_mileage:,}"
                ),
            )
        return EquipmentCheckResult(
            passed=True,
            message=(
                f"Equipment mileage {context.equipment_mileage:,} "
                f"within limit of {max_mileage:,}"
            ),
        )

    def _check_hours(
        self, context: EvaluationContext, max_hours: int
    ) -> Optional[EquipmentCheckResult]:
        """Check if equipment hours are within limit."""
        if context.equipment_hours is None:
            return None

        if context.equipment_hours > max_hours:
            return EquipmentCheckResult(
                passed=False,
                check_name="Equipment Hours",
                required=f"Max {max_hours:,} hours",
                actual=f"{context.equipment_hours:,} hours",
                message=(
                    f"Equipment hours {context.equipment_hours:,} "
                    f"exceeds maximum {max_hours:,}"
                ),
            )
        return EquipmentCheckResult(
            passed=True,
            message=(
                f"Equipment hours {context.equipment_hours:,} "
                f"within limit of {max_hours:,}"
            ),
        )

    def _calculate_score(
        self, context: EvaluationContext, criteria: dict[str, Any]
    ) -> float:
        """Calculate score based on how far under limits."""
        score = 100.0
        if "max_age_years" in criteria:
            max_age = int(criteria["max_age_years"])
            age_ratio = context.equipment_age_years / max_age if max_age > 0 else 0
            score -= age_ratio * 20
        return max(60, score)

    def evaluate(
        self, context: EvaluationContext, criteria: dict[str, Any]
    ) -> RuleResult:
        """Evaluate equipment requirements.

        Args:
            context: The evaluation context.
            criteria: The criteria configuration containing any of:
                - max_age_years: Maximum equipment age in years
                - max_mileage: Maximum mileage (for vehicles)
                - max_hours: Maximum hours (for construction equipment)

        Returns:
            RuleResult with pass/fail and score contribution.
        """
        failed_checks: list[dict[str, str]] = []
        passed_checks: list[str] = []

        # Run each applicable check
        if "max_age_years" in criteria:
            result = self._check_age(context, int(criteria["max_age_years"]))
            if result.passed:
                passed_checks.append(result.message)
            else:
                failed_checks.append({
                    "check": result.check_name,
                    "required": result.required,
                    "actual": result.actual,
                    "message": result.message,
                })

        if "max_mileage" in criteria:
            result = self._check_mileage(context, int(criteria["max_mileage"]))
            if result:
                if result.passed:
                    passed_checks.append(result.message)
                else:
                    failed_checks.append({
                        "check": result.check_name,
                        "required": result.required,
                        "actual": result.actual,
                        "message": result.message,
                    })

        if "max_hours" in criteria:
            result = self._check_hours(context, int(criteria["max_hours"]))
            if result:
                if result.passed:
                    passed_checks.append(result.message)
                else:
                    failed_checks.append({
                        "check": result.check_name,
                        "required": result.required,
                        "actual": result.actual,
                        "message": result.message,
                    })

        if failed_checks:
            return self._create_failed_result(
                rule_name="Equipment Requirements",
                required_value=failed_checks[0]["required"],
                actual_value=failed_checks[0]["actual"],
                message=failed_checks[0]["message"],
                details={"failed_checks": failed_checks, "passed_checks": passed_checks},
            )

        return self._create_passed_result(
            rule_name="Equipment Requirements",
            required_value="All met",
            actual_value="All met",
            message="Equipment meets all requirements",
            score=self._calculate_score(context, criteria),
            details={"passed_checks": passed_checks},
        )


@dataclass
class TermMatrixEntry:
    """Result of term matrix lookup."""

    max_term: Optional[int]
    rejection_reason: Optional[str]


@RuleRegistry.register("term_matrix")
class TermMatrixRule(Rule):
    """Evaluates equipment against term matrix to determine max term."""

    @property
    def rule_type(self) -> str:
        return "term_matrix"

    def _get_lookup_value(
        self, context: EvaluationContext, lookup_field: str
    ) -> Optional[int]:
        """Get the value to use for term matrix lookup."""
        field_map = {
            "mileage": context.equipment_mileage,
            "age": context.equipment_age_years,
            "hours": context.equipment_hours,
        }
        return field_map.get(lookup_field)

    def _find_matching_entry(
        self, lookup_value: int, entries: list[dict[str, Any]]
    ) -> TermMatrixEntry:
        """Find the matching term matrix entry for the lookup value."""
        for entry in entries:
            entry_min = entry.get("min", 0)
            entry_max = entry.get("max", float("inf"))

            if entry_min <= lookup_value <= entry_max:
                return TermMatrixEntry(
                    max_term=entry.get("max_term_months", 0),
                    rejection_reason=entry.get("rejection_reason"),
                )

        return TermMatrixEntry(max_term=None, rejection_reason=None)

    def _handle_missing_lookup_value(self, lookup_field: str) -> RuleResult:
        """Handle case when lookup value is not available."""
        return self._create_passed_result(
            rule_name="Term Matrix",
            required_value="N/A",
            actual_value=f"{lookup_field.title()} not provided",
            message=f"No {lookup_field} data available for term matrix lookup",
            score=80,
        )

    def _handle_equipment_not_desired(
        self,
        lookup_field: str,
        lookup_value: int,
        rejection_reason: Optional[str],
    ) -> RuleResult:
        """Handle case when equipment is not desired."""
        return self._create_failed_result(
            rule_name="Term Matrix",
            required_value="Equipment desired",
            actual_value=f"{lookup_field.title()}: {lookup_value:,}",
            message=rejection_reason
            or f"Equipment {lookup_field} not within desired range",
        )

    def _handle_no_matching_entry(
        self, lookup_field: str, lookup_value: int
    ) -> RuleResult:
        """Handle case when no term matrix entry matches."""
        return self._create_passed_result(
            rule_name="Term Matrix",
            required_value="N/A",
            actual_value=f"{lookup_field.title()}: {lookup_value:,}",
            message="No term matrix entry matched, using default terms",
            score=70,
        )

    def _handle_term_exceeded(
        self,
        max_term: int,
        requested_term: int,
        lookup_value: int,
    ) -> RuleResult:
        """Handle case when requested term exceeds maximum."""
        return self._create_failed_result(
            rule_name="Term Matrix",
            required_value=f"Max {max_term} months",
            actual_value=f"Requested {requested_term} months",
            message=(
                f"Requested term {requested_term} months "
                f"exceeds maximum {max_term} months for this equipment"
            ),
            details={"max_term_months": max_term, "lookup_value": lookup_value},
        )

    def _handle_success(
        self, lookup_field: str, lookup_value: int, max_term: int
    ) -> RuleResult:
        """Handle successful term matrix evaluation."""
        return self._create_passed_result(
            rule_name="Term Matrix",
            required_value=f"Max {max_term} months",
            actual_value=f"{lookup_field.title()}: {lookup_value:,}",
            message=f"Equipment qualifies for up to {max_term} month term",
            score=85,
            details={"max_term_months": max_term, "lookup_value": lookup_value},
        )

    def evaluate(
        self, context: EvaluationContext, criteria: dict[str, Any]
    ) -> RuleResult:
        """Evaluate equipment against term matrix.

        The term matrix looks up the maximum allowed term based on
        equipment mileage, age, or hours.

        Args:
            context: The evaluation context.
            criteria: The term matrix configuration containing:
                - lookup_field: "mileage", "age", or "hours"
                - entries: List of entries with min/max and max_term_months

        Returns:
            RuleResult with pass/fail and the determined max term.
        """
        lookup_field = criteria.get("lookup_field", "mileage")
        entries = criteria.get("entries", [])

        lookup_value = self._get_lookup_value(context, lookup_field)
        if lookup_value is None:
            return self._handle_missing_lookup_value(lookup_field)

        entry = self._find_matching_entry(lookup_value, entries)

        if entry.max_term == 0 or entry.rejection_reason:
            return self._handle_equipment_not_desired(
                lookup_field, lookup_value, entry.rejection_reason
            )

        if entry.max_term is None:
            return self._handle_no_matching_entry(lookup_field, lookup_value)

        if (
            context.requested_term_months
            and context.requested_term_months > entry.max_term
        ):
            return self._handle_term_exceeded(
                entry.max_term, context.requested_term_months, lookup_value
            )

        return self._handle_success(lookup_field, lookup_value, entry.max_term)
