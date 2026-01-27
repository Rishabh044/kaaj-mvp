"""Matching engine for evaluating applications against lender policies."""

from dataclasses import dataclass, field
from typing import Any, Optional

from app.policies.schema import (
    LenderPolicy,
    LenderProgram,
    ProgramCriteria,
    LenderRestrictions,
)
from app.rules.base import EvaluationContext, RuleResult
from app.rules.registry import RuleRegistry


@dataclass
class ProgramMatchResult:
    """Result of evaluating an application against a single program."""

    program_id: str
    program_name: str
    is_eligible: bool
    fit_score: float = 0.0
    criteria_results: list[RuleResult] = field(default_factory=list)
    rejection_reasons: list[str] = field(default_factory=list)
    max_term_months: Optional[int] = None

    @property
    def passed_criteria_count(self) -> int:
        """Count of criteria that passed."""
        return sum(1 for r in self.criteria_results if r.passed)

    @property
    def failed_criteria_count(self) -> int:
        """Count of criteria that failed."""
        return sum(1 for r in self.criteria_results if not r.passed)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "program_id": self.program_id,
            "program_name": self.program_name,
            "is_eligible": self.is_eligible,
            "fit_score": self.fit_score,
            "criteria_results": [r.to_dict() for r in self.criteria_results],
            "rejection_reasons": self.rejection_reasons,
            "max_term_months": self.max_term_months,
            "passed_criteria_count": self.passed_criteria_count,
            "failed_criteria_count": self.failed_criteria_count,
        }


@dataclass
class LenderMatchResult:
    """Result of evaluating an application against a lender."""

    lender_id: str
    lender_name: str
    is_eligible: bool
    best_program: Optional[ProgramMatchResult] = None
    fit_score: float = 0.0
    program_results: list[ProgramMatchResult] = field(default_factory=list)
    global_rejection_reasons: list[str] = field(default_factory=list)
    rank: Optional[int] = None

    @property
    def eligible_program_count(self) -> int:
        """Count of programs the application qualifies for."""
        return sum(1 for p in self.program_results if p.is_eligible)

    @property
    def primary_rejection_reason(self) -> Optional[str]:
        """Get the primary (first) rejection reason."""
        if self.global_rejection_reasons:
            return self.global_rejection_reasons[0]
        if self.best_program and self.best_program.rejection_reasons:
            return self.best_program.rejection_reasons[0]
        return None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "lender_id": self.lender_id,
            "lender_name": self.lender_name,
            "is_eligible": self.is_eligible,
            "best_program": self.best_program.to_dict() if self.best_program else None,
            "fit_score": self.fit_score,
            "program_results": [p.to_dict() for p in self.program_results],
            "global_rejection_reasons": self.global_rejection_reasons,
            "eligible_program_count": self.eligible_program_count,
            "primary_rejection_reason": self.primary_rejection_reason,
            "rank": self.rank,
        }


class MatchingEngine:
    """Engine for evaluating applications against lender policies.

    The engine orchestrates the evaluation of a loan application against
    a lender's policy, checking global restrictions first, then evaluating
    each program's criteria.
    """

    def __init__(self, registry: Optional[RuleRegistry] = None):
        """Initialize the matching engine.

        Args:
            registry: Rule registry to use. If not provided, uses the
                     default global registry.
        """
        self.registry = registry or RuleRegistry

    def evaluate_lender(
        self, context: EvaluationContext, policy: LenderPolicy
    ) -> LenderMatchResult:
        """Evaluate an application against a single lender's policy.

        Args:
            context: The evaluation context with all application data.
            policy: The lender's policy to evaluate against.

        Returns:
            LenderMatchResult with eligibility, programs, and scores.
        """
        result = LenderMatchResult(
            lender_id=policy.id,
            lender_name=policy.name,
            is_eligible=False,
        )

        # First check global restrictions
        if policy.restrictions:
            restriction_results = self._evaluate_restrictions(
                context, policy.restrictions
            )
            for r in restriction_results:
                if not r.passed:
                    result.global_rejection_reasons.append(r.message)

            if result.global_rejection_reasons:
                # Failed global restrictions - can't qualify for any program
                return result

        # Evaluate each program
        for program in policy.programs:
            program_result = self._evaluate_program(context, program)
            result.program_results.append(program_result)

        # Find eligible programs and best match
        eligible_programs = [p for p in result.program_results if p.is_eligible]

        if eligible_programs:
            result.is_eligible = True
            # Best program is the one with highest fit score
            result.best_program = max(eligible_programs, key=lambda p: p.fit_score)
            result.fit_score = result.best_program.fit_score
        else:
            # Find the program that came closest (fewest failures)
            if result.program_results:
                closest = min(
                    result.program_results, key=lambda p: p.failed_criteria_count
                )
                result.best_program = closest
                result.fit_score = closest.fit_score

        return result

    def _evaluate_restrictions(
        self, context: EvaluationContext, restrictions: LenderRestrictions
    ) -> list[RuleResult]:
        """Evaluate global lender restrictions.

        Args:
            context: The evaluation context.
            restrictions: Global restrictions to check.

        Returns:
            List of RuleResults for restriction checks.
        """
        results = []

        # Geographic restrictions
        if restrictions.geographic:
            result = self._evaluate_geographic_restriction(
                context, restrictions.geographic
            )
            if result:
                results.append(result)

        # Industry restrictions
        if restrictions.industry:
            result = self._evaluate_industry_restriction(
                context, restrictions.industry
            )
            if result:
                results.append(result)

        # Transaction type restrictions
        if restrictions.transaction:
            result = self._evaluate_transaction_restriction(
                context, restrictions.transaction
            )
            if result:
                results.append(result)

        # Equipment restrictions
        if restrictions.equipment:
            result = self._evaluate_equipment_restriction(
                context, restrictions.equipment
            )
            if result:
                results.append(result)

        return results

    def _evaluate_geographic_restriction(
        self, context: EvaluationContext, geo_criteria
    ) -> Optional[RuleResult]:
        """Evaluate geographic restrictions."""
        state = context.state.upper() if context.state else ""

        # Check excluded states
        if geo_criteria.excluded_states:
            excluded = [s.upper() for s in geo_criteria.excluded_states]
            if state in excluded:
                return RuleResult(
                    passed=False,
                    rule_name="State Restriction",
                    required_value=f"Not in: {', '.join(excluded)}",
                    actual_value=state,
                    message=f"State {state} is excluded by this lender",
                    score=0,
                )

        # Check allowed states
        if geo_criteria.allowed_states:
            allowed = [s.upper() for s in geo_criteria.allowed_states]
            if state not in allowed:
                return RuleResult(
                    passed=False,
                    rule_name="State Restriction",
                    required_value=f"Must be in: {', '.join(allowed)}",
                    actual_value=state,
                    message=f"State {state} is not in the allowed list",
                    score=0,
                )

        return None  # No restriction failed

    def _evaluate_industry_restriction(
        self, context: EvaluationContext, industry_criteria
    ) -> Optional[RuleResult]:
        """Evaluate industry restrictions."""
        industry = context.industry_code.lower() if context.industry_code else ""
        industry_name = context.industry_name.lower() if context.industry_name else ""

        if industry_criteria.excluded_industries:
            excluded = [i.lower() for i in industry_criteria.excluded_industries]
            for exc in excluded:
                if exc in industry or exc in industry_name:
                    return RuleResult(
                        passed=False,
                        rule_name="Industry Restriction",
                        required_value=f"Not: {exc}",
                        actual_value=industry or industry_name,
                        message=f"Industry '{exc}' is excluded by this lender",
                        score=0,
                    )

        return None

    def _evaluate_transaction_restriction(
        self, context: EvaluationContext, txn_criteria
    ) -> Optional[RuleResult]:
        """Evaluate transaction type restrictions."""
        # Check private party
        if context.is_private_party and not txn_criteria.allows_private_party:
            return RuleResult(
                passed=False,
                rule_name="Transaction Type",
                required_value="No private party sales",
                actual_value="Private party sale",
                message="Private party sales are not allowed by this lender",
                score=0,
            )

        # Check sale-leaseback
        if (
            context.transaction_type == "sale_leaseback"
            and not txn_criteria.allows_sale_leaseback
        ):
            return RuleResult(
                passed=False,
                rule_name="Transaction Type",
                required_value="No sale-leaseback",
                actual_value="Sale-leaseback",
                message="Sale-leaseback transactions are not allowed",
                score=0,
            )

        # Check refinance
        if (
            context.transaction_type == "refinance"
            and not txn_criteria.allows_refinance
        ):
            return RuleResult(
                passed=False,
                rule_name="Transaction Type",
                required_value="No refinance",
                actual_value="Refinance",
                message="Refinance transactions are not allowed",
                score=0,
            )

        return None

    def _evaluate_equipment_restriction(
        self, context: EvaluationContext, equip_criteria
    ) -> Optional[RuleResult]:
        """Evaluate equipment restrictions."""
        category = context.equipment_category.lower()

        if equip_criteria.excluded_categories:
            excluded = [c.lower() for c in equip_criteria.excluded_categories]
            if category in excluded:
                return RuleResult(
                    passed=False,
                    rule_name="Equipment Restriction",
                    required_value=f"Not: {category}",
                    actual_value=category,
                    message=f"Equipment category '{category}' is not allowed",
                    score=0,
                )

        if equip_criteria.max_age_years is not None:
            if context.equipment_age_years > equip_criteria.max_age_years:
                return RuleResult(
                    passed=False,
                    rule_name="Equipment Age",
                    required_value=f"Max {equip_criteria.max_age_years} years",
                    actual_value=f"{context.equipment_age_years} years",
                    message=f"Equipment is too old ({context.equipment_age_years} years)",
                    score=0,
                )

        return None

    def _evaluate_program(
        self, context: EvaluationContext, program: LenderProgram
    ) -> ProgramMatchResult:
        """Evaluate an application against a single program.

        Args:
            context: The evaluation context.
            program: The program to evaluate.

        Returns:
            ProgramMatchResult with eligibility and criteria results.
        """
        result = ProgramMatchResult(
            program_id=program.id,
            program_name=program.name,
            is_eligible=True,  # Assume eligible until proven otherwise
            max_term_months=program.max_term_months,
        )

        # Check loan amount bounds first
        if program.min_amount is not None and context.loan_amount < program.min_amount:
            result.is_eligible = False
            result.rejection_reasons.append(
                f"Loan amount ${context.loan_amount/100:,.0f} below minimum "
                f"${program.min_amount/100:,.0f}"
            )
            result.criteria_results.append(
                RuleResult(
                    passed=False,
                    rule_name="Minimum Loan Amount",
                    required_value=f"${program.min_amount/100:,.0f}",
                    actual_value=f"${context.loan_amount/100:,.0f}",
                    message="Loan amount below program minimum",
                    score=0,
                )
            )

        if program.max_amount is not None and context.loan_amount > program.max_amount:
            result.is_eligible = False
            result.rejection_reasons.append(
                f"Loan amount ${context.loan_amount/100:,.0f} exceeds maximum "
                f"${program.max_amount/100:,.0f}"
            )
            result.criteria_results.append(
                RuleResult(
                    passed=False,
                    rule_name="Maximum Loan Amount",
                    required_value=f"${program.max_amount/100:,.0f}",
                    actual_value=f"${context.loan_amount/100:,.0f}",
                    message="Loan amount exceeds program maximum",
                    score=0,
                )
            )

        # Evaluate program criteria
        if program.criteria:
            criteria_results = self._evaluate_criteria(context, program.criteria)
            result.criteria_results.extend(criteria_results)

            # Check if any criteria failed
            for cr in criteria_results:
                if not cr.passed:
                    result.is_eligible = False
                    result.rejection_reasons.append(cr.message)

        # Calculate fit score
        if result.criteria_results:
            passed_scores = [r.score for r in result.criteria_results if r.passed]
            if passed_scores:
                result.fit_score = sum(passed_scores) / len(result.criteria_results)
            else:
                result.fit_score = 0.0
        else:
            result.fit_score = 100.0 if result.is_eligible else 0.0

        return result

    def _evaluate_criteria(
        self, context: EvaluationContext, criteria: ProgramCriteria
    ) -> list[RuleResult]:
        """Evaluate all program criteria.

        Args:
            context: The evaluation context.
            criteria: The program criteria to evaluate.

        Returns:
            List of RuleResults for each criteria check.
        """
        results = []

        # Credit score criteria
        if criteria.credit_score:
            rule = self.registry.get_rule("credit_score")
            if rule:
                result = rule.evaluate(
                    context,
                    {
                        "type": criteria.credit_score.type,
                        "min": criteria.credit_score.min,
                    },
                )
                results.append(result)

        # Business criteria
        if criteria.business:
            rule = self.registry.get_rule("business")
            if rule:
                business_dict = {}
                if criteria.business.min_time_in_business_years is not None:
                    business_dict[
                        "min_time_in_business_years"
                    ] = criteria.business.min_time_in_business_years
                if criteria.business.requires_homeowner is not None:
                    business_dict[
                        "requires_homeowner"
                    ] = criteria.business.requires_homeowner
                if criteria.business.requires_cdl is not None:
                    business_dict["requires_cdl"] = criteria.business.requires_cdl
                if criteria.business.min_cdl_years is not None:
                    business_dict["min_cdl_years"] = criteria.business.min_cdl_years
                if criteria.business.min_industry_experience_years is not None:
                    business_dict[
                        "min_industry_experience_years"
                    ] = criteria.business.min_industry_experience_years
                if criteria.business.min_fleet_size is not None:
                    business_dict["min_fleet_size"] = criteria.business.min_fleet_size

                if business_dict:
                    result = rule.evaluate(context, business_dict)
                    results.append(result)

        # Credit history criteria
        if criteria.credit_history:
            rule = self.registry.get_rule("credit_history")
            if rule:
                history_dict = {}
                if criteria.credit_history.max_bankruptcies is not None:
                    history_dict[
                        "max_bankruptcies"
                    ] = criteria.credit_history.max_bankruptcies
                if criteria.credit_history.bankruptcy_min_discharge_years is not None:
                    history_dict[
                        "bankruptcy_min_discharge_years"
                    ] = criteria.credit_history.bankruptcy_min_discharge_years
                if criteria.credit_history.max_open_judgements is not None:
                    history_dict[
                        "max_open_judgements"
                    ] = criteria.credit_history.max_open_judgements
                if criteria.credit_history.allows_foreclosure is not None:
                    history_dict[
                        "allows_foreclosure"
                    ] = criteria.credit_history.allows_foreclosure
                if criteria.credit_history.allows_repossession is not None:
                    history_dict[
                        "allows_repossession"
                    ] = criteria.credit_history.allows_repossession
                if criteria.credit_history.max_tax_liens is not None:
                    history_dict["max_tax_liens"] = criteria.credit_history.max_tax_liens

                if history_dict:
                    result = rule.evaluate(context, history_dict)
                    results.append(result)

        # Equipment criteria
        if criteria.equipment:
            rule = self.registry.get_rule("equipment")
            if rule:
                equip_dict = {}
                if criteria.equipment.max_age_years is not None:
                    equip_dict["max_age_years"] = criteria.equipment.max_age_years
                if criteria.equipment.max_mileage is not None:
                    equip_dict["max_mileage"] = criteria.equipment.max_mileage

                if equip_dict:
                    result = rule.evaluate(context, equip_dict)
                    results.append(result)

        # Loan amount criteria (program-level, already checked above)
        if criteria.loan_amount:
            rule = self.registry.get_rule("loan_amount")
            if rule:
                amount_dict = {}
                if criteria.loan_amount.min_amount is not None:
                    amount_dict["min_amount"] = criteria.loan_amount.min_amount
                if criteria.loan_amount.max_amount is not None:
                    amount_dict["max_amount"] = criteria.loan_amount.max_amount

                if amount_dict:
                    result = rule.evaluate(context, amount_dict)
                    results.append(result)

        # Geographic criteria (at program level)
        if criteria.geographic:
            geo_result = self._evaluate_geographic_restriction(
                context, criteria.geographic
            )
            if geo_result:
                results.append(geo_result)

        # Industry criteria (at program level)
        if criteria.industry:
            ind_result = self._evaluate_industry_restriction(context, criteria.industry)
            if ind_result:
                results.append(ind_result)

        # Transaction criteria (at program level)
        if criteria.transaction:
            txn_result = self._evaluate_transaction_restriction(
                context, criteria.transaction
            )
            if txn_result:
                results.append(txn_result)

        return results
