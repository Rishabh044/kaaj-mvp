"""Rule engine for policy evaluation.

This module provides the core abstractions and implementations for
evaluating loan applications against lender policies.
"""

from app.rules.base import EvaluationContext, Rule, RuleResult
from app.rules.registry import RuleRegistry, get_rule
from app.rules.context_builder import (
    build_evaluation_context,
)
from app.rules.engine import (
    MatchingEngine,
    LenderMatchResult,
    ProgramMatchResult,
)

# Import criteria to register all rules
from app.rules.criteria import (
    BusinessRequirementsRule,
    CreditHistoryRule,
    CreditScoreRule,
    EquipmentRule,
    IndustryExclusionRule,
    LoanAmountRule,
    StateRestrictionRule,
    TermMatrixRule,
    TransactionTypeRule,
)

__all__ = [
    # Base classes
    "EvaluationContext",
    "Rule",
    "RuleResult",
    # Registry
    "RuleRegistry",
    "get_rule",
    # Context builder
    "build_evaluation_context",
    # Matching engine
    "MatchingEngine",
    "LenderMatchResult",
    "ProgramMatchResult",
    # Rule implementations
    "CreditScoreRule",
    "BusinessRequirementsRule",
    "CreditHistoryRule",
    "EquipmentRule",
    "TermMatrixRule",
    "StateRestrictionRule",
    "IndustryExclusionRule",
    "TransactionTypeRule",
    "LoanAmountRule",
]
