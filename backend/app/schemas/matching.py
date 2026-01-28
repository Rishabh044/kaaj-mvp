"""Pydantic schemas for matching results."""

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import Field

from app.schemas.common import BaseSchema, IDSchema


class CriterionResult(BaseSchema):
    """Result of evaluating a single criterion."""

    passed: bool
    rule_name: str
    required_value: str
    actual_value: str
    message: str
    score_contribution: float = 0.0
    details: Optional[dict[str, Any]] = None


class MatchResultResponse(IDSchema):
    """Response for a single lender match result."""

    application_id: UUID
    lender_id: str
    lender_name: str = ""  # Populated from lender

    # Eligibility
    is_eligible: bool
    matched_program_id: Optional[str] = None
    matched_program_name: Optional[str] = None

    # Scoring
    fit_score: int = Field(..., ge=0, le=100)
    rank: Optional[int] = None

    # Detailed Results
    criteria_results: dict[str, CriterionResult] = {}
    rejection_reasons: list[str] = []

    # Timestamp
    evaluated_at: datetime


class MatchResultSummary(BaseSchema):
    """Summary of a match result for listings."""

    lender_id: str
    lender_name: str
    is_eligible: bool
    fit_score: int
    rank: Optional[int]
    matched_program_name: Optional[str]
    primary_rejection_reason: Optional[str] = None


class MatchingResultsResponse(BaseSchema):
    """Complete matching results for an application."""

    application_id: UUID
    application_number: str

    # Summary
    total_lenders: int
    eligible_count: int
    ineligible_count: int

    # Best match
    best_match: Optional[MatchResultSummary] = None

    # All results
    matches: list[MatchResultResponse] = []

    # Categorized
    eligible_matches: list[MatchResultResponse] = []
    ineligible_matches: list[MatchResultResponse] = []


class LenderMatchResult(BaseSchema):
    """Internal result from matching engine for a single lender."""

    lender_id: str
    is_eligible: bool
    matched_program_id: Optional[str] = None
    matched_program_name: Optional[str] = None
    fit_score: int = 0
    criteria_results: dict[str, dict[str, Any]] = {}
    rejection_reasons: list[str] = []


class ProgramEvaluationResult(BaseSchema):
    """Result of evaluating a single program."""

    program_id: str
    is_eligible: bool
    fit_score: int = 0
    criteria_results: dict[str, dict[str, Any]] = {}
    rejection_reasons: list[str] = []


class RestrictionResult(BaseSchema):
    """Result of evaluating lender restrictions."""

    passed: bool
    details: dict[str, dict[str, Any]] = {}
    reasons: list[str] = []
