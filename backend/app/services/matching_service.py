"""Lender matching service for coordinating application evaluation."""

import asyncio
from dataclasses import dataclass, field
from typing import Any, Optional

from app.policies.loader import PolicyLoader
from app.rules.base import EvaluationContext
from app.rules.engine import LenderMatchResult, MatchingEngine


@dataclass
class MatchingResult:
    """Result of matching an application against all lenders."""

    matches: list[LenderMatchResult] = field(default_factory=list)
    best_match: Optional[LenderMatchResult] = None
    total_evaluated: int = 0
    total_eligible: int = 0

    @property
    def has_eligible_lender(self) -> bool:
        """Check if at least one lender is eligible."""
        return self.total_eligible > 0

    @property
    def eligible_matches(self) -> list[LenderMatchResult]:
        """Get only the eligible matches, ranked by fit score."""
        return [m for m in self.matches if m.is_eligible]

    @property
    def ineligible_matches(self) -> list[LenderMatchResult]:
        """Get only the ineligible matches."""
        return [m for m in self.matches if not m.is_eligible]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "matches": [m.to_dict() for m in self.matches],
            "best_match": self.best_match.to_dict() if self.best_match else None,
            "total_evaluated": self.total_evaluated,
            "total_eligible": self.total_eligible,
            "has_eligible_lender": self.has_eligible_lender,
        }


class LenderMatchingService:
    """Service for matching loan applications against lender policies.

    This service coordinates the evaluation of a loan application against
    all (or specified) lenders, ranks results, and provides comprehensive
    matching output.
    """

    def __init__(
        self,
        engine: Optional[MatchingEngine] = None,
        policy_loader: Optional[PolicyLoader] = None,
    ):
        """Initialize the matching service.

        Args:
            engine: The matching engine to use for evaluation.
            policy_loader: The policy loader for loading lender configurations.
        """
        self.engine = engine or MatchingEngine()
        self.policy_loader = policy_loader or PolicyLoader()

    def match_application(
        self,
        context: EvaluationContext,
        lender_ids: Optional[list[str]] = None,
    ) -> MatchingResult:
        """Evaluate an application against lenders synchronously.

        Args:
            context: The evaluation context with all application data.
            lender_ids: Optional list of specific lender IDs to evaluate.
                       If None, evaluates against all active lenders.

        Returns:
            MatchingResult with all lender evaluations and rankings.
        """
        # Load policies
        if lender_ids:
            policies = [
                self.policy_loader.load_policy(lid)
                for lid in lender_ids
            ]
        else:
            policies = self.policy_loader.get_active_policies()

        # Evaluate each lender
        matches = []
        for policy in policies:
            result = self.engine.evaluate_lender(context, policy)
            matches.append(result)

        return self._build_result(matches)

    async def match_application_async(
        self,
        context: EvaluationContext,
        lender_ids: Optional[list[str]] = None,
    ) -> MatchingResult:
        """Evaluate an application against lenders asynchronously.

        This method runs evaluations in parallel for better performance
        when evaluating against many lenders.

        Args:
            context: The evaluation context with all application data.
            lender_ids: Optional list of specific lender IDs to evaluate.

        Returns:
            MatchingResult with all lender evaluations and rankings.
        """
        # Load policies
        if lender_ids:
            policies = [
                self.policy_loader.load_policy(lid)
                for lid in lender_ids
            ]
        else:
            policies = self.policy_loader.get_active_policies()

        # Evaluate lenders in parallel
        async def evaluate_lender(policy):
            # The engine is synchronous but we can run multiple in parallel
            return self.engine.evaluate_lender(context, policy)

        tasks = [evaluate_lender(policy) for policy in policies]
        matches = await asyncio.gather(*tasks)

        return self._build_result(list(matches))

    def match_single_lender(
        self,
        context: EvaluationContext,
        lender_id: str,
    ) -> LenderMatchResult:
        """Evaluate an application against a single lender.

        Args:
            context: The evaluation context.
            lender_id: The ID of the lender to evaluate.

        Returns:
            LenderMatchResult for the specified lender.
        """
        policy = self.policy_loader.load_policy(lender_id)
        return self.engine.evaluate_lender(context, policy)

    def _build_result(self, matches: list[LenderMatchResult]) -> MatchingResult:
        """Build the final matching result from individual lender results.

        Args:
            matches: List of LenderMatchResult from evaluations.

        Returns:
            Aggregated MatchingResult with rankings.
        """
        # Sort by eligibility first, then by fit score
        sorted_matches = sorted(
            matches,
            key=lambda m: (m.is_eligible, m.fit_score),
            reverse=True,
        )

        # Assign ranks
        for rank, match in enumerate(sorted_matches, start=1):
            match.rank = rank

        # Find best match
        eligible_matches = [m for m in sorted_matches if m.is_eligible]
        best_match = eligible_matches[0] if eligible_matches else None

        return MatchingResult(
            matches=sorted_matches,
            best_match=best_match,
            total_evaluated=len(matches),
            total_eligible=len(eligible_matches),
        )

    def get_available_lenders(self) -> list[str]:
        """Get list of available lender IDs.

        Returns:
            List of lender IDs that have valid policies.
        """
        return self.policy_loader.get_all_lender_ids()

    def get_eligible_lenders(self, context: EvaluationContext) -> list[str]:
        """Get list of lender IDs that the application qualifies for.

        This is a quick filter without detailed evaluation.

        Args:
            context: The evaluation context.

        Returns:
            List of lender IDs where the application is eligible.
        """
        result = self.match_application(context)
        return [m.lender_id for m in result.matches if m.is_eligible]

    def explain_rejection(
        self,
        context: EvaluationContext,
        lender_id: str,
    ) -> dict[str, Any]:
        """Get detailed explanation of why an application was rejected.

        Args:
            context: The evaluation context.
            lender_id: The lender to explain rejection for.

        Returns:
            Dictionary with rejection details and suggestions.
        """
        result = self.match_single_lender(context, lender_id)

        if result.is_eligible:
            return {
                "is_rejected": False,
                "message": "Application qualifies for this lender",
                "best_program": result.best_program.program_name if result.best_program else None,
            }

        # Compile rejection details
        global_reasons = result.global_rejection_reasons
        program_reasons = {}

        for prog_result in result.program_results:
            if not prog_result.is_eligible:
                program_reasons[prog_result.program_name] = {
                    "rejection_reasons": prog_result.rejection_reasons,
                    "failed_criteria": [
                        {
                            "rule": r.rule_name,
                            "required": r.required_value,
                            "actual": r.actual_value,
                            "message": r.message,
                        }
                        for r in prog_result.criteria_results
                        if not r.passed
                    ],
                }

        return {
            "is_rejected": True,
            "global_rejection_reasons": global_reasons,
            "program_rejections": program_reasons,
            "primary_reason": result.primary_rejection_reason,
        }
