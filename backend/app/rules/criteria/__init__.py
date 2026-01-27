"""Rule implementations for different criteria categories.

Import all rules here to trigger registration with the RuleRegistry.
"""

from app.rules.criteria.business import BusinessRequirementsRule
from app.rules.criteria.credit_history import CreditHistoryRule
from app.rules.criteria.credit_score import CreditScoreRule
from app.rules.criteria.equipment import EquipmentRule, TermMatrixRule
from app.rules.criteria.geographic import StateRestrictionRule
from app.rules.criteria.industry import IndustryExclusionRule
from app.rules.criteria.loan_amount import LoanAmountRule
from app.rules.criteria.transaction import TransactionTypeRule

__all__ = [
    "CreditScoreRule",
    "BusinessRequirementsRule",
    "CreditHistoryRule",
    "EquipmentRule",
    "TermMatrixRule",
    "StateRestrictionRule",
    "IndustryExclusionRule",
    "LoanAmountRule",
    "TransactionTypeRule",
]
