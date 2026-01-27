"""Unit tests for MatchResult model."""

import uuid
from datetime import datetime

import pytest

from app.models import MatchResult


class TestMatchResultCreation:
    """Tests for creating MatchResult instances."""

    def test_match_result_creation_eligible(self):
        """Test creating an eligible match result."""
        result = MatchResult(
            application_id=uuid.uuid4(),
            lender_id="citizens_bank",
            is_eligible=True,
            matched_program_id="tier_1_app_only",
            matched_program_name="Tier 1 - App Only",
            fit_score=85,
            rank=1,
            criteria_results={
                "credit_score": {
                    "passed": True,
                    "rule_name": "Minimum TransUnion Score",
                    "required_value": "700",
                    "actual_value": "750",
                    "message": "TransUnion score 750 meets minimum 700",
                    "score_contribution": 25,
                }
            },
            rejection_reasons=[],
        )
        assert result.is_eligible is True
        assert result.fit_score == 85
        assert result.rank == 1
        assert result.matched_program_id == "tier_1_app_only"

    def test_match_result_creation_ineligible(self):
        """Test creating an ineligible match result."""
        result = MatchResult(
            application_id=uuid.uuid4(),
            lender_id="citizens_bank",
            is_eligible=False,
            fit_score=0,
            criteria_results={
                "credit_score": {
                    "passed": False,
                    "rule_name": "Minimum TransUnion Score",
                    "required_value": "700",
                    "actual_value": "650",
                    "message": "TransUnion score 650 below minimum 700",
                    "score_contribution": 0,
                }
            },
            rejection_reasons=["TransUnion score 650 below minimum 700"],
        )
        assert result.is_eligible is False
        assert result.fit_score == 0
        assert result.rank is None
        assert len(result.rejection_reasons) == 1


class TestCriteriaResultsJsonStructure:
    """Tests for criteria_results JSON structure."""

    def test_criteria_results_structure(self):
        """Test that criteria_results has expected structure."""
        criteria = {
            "credit_score": {
                "passed": True,
                "rule_name": "Minimum FICO Score",
                "required_value": "680",
                "actual_value": "720",
                "message": "FICO score 720 meets minimum 680",
                "score_contribution": 20,
            },
            "time_in_business": {
                "passed": True,
                "rule_name": "Minimum Time in Business",
                "required_value": "2 years",
                "actual_value": "5 years",
                "message": "Time in business 5 years exceeds minimum 2 years",
                "score_contribution": 15,
            },
        }
        result = MatchResult(
            application_id=uuid.uuid4(),
            lender_id="test_lender",
            is_eligible=True,
            fit_score=75,
            criteria_results=criteria,
        )
        assert "credit_score" in result.criteria_results
        assert "time_in_business" in result.criteria_results
        assert result.criteria_results["credit_score"]["passed"] is True

    def test_empty_criteria_results(self):
        """Test with empty criteria results."""
        result = MatchResult(
            application_id=uuid.uuid4(),
            lender_id="test_lender",
            is_eligible=False,
            fit_score=0,
            criteria_results={},
        )
        assert result.criteria_results == {}


class TestRejectionReasonsList:
    """Tests for rejection_reasons list."""

    def test_multiple_rejection_reasons(self):
        """Test with multiple rejection reasons."""
        result = MatchResult(
            application_id=uuid.uuid4(),
            lender_id="test_lender",
            is_eligible=False,
            fit_score=0,
            criteria_results={},
            rejection_reasons=[
                "Credit score 650 below minimum 700",
                "State CA is restricted",
                "Time in business 1 year below minimum 2 years",
            ],
        )
        assert len(result.rejection_reasons) == 3
        assert result.has_rejection_reasons is True

    def test_no_rejection_reasons(self):
        """Test with no rejection reasons."""
        result = MatchResult(
            application_id=uuid.uuid4(),
            lender_id="test_lender",
            is_eligible=True,
            fit_score=85,
            criteria_results={},
            rejection_reasons=[],
        )
        assert result.has_rejection_reasons is False

    def test_primary_rejection_reason(self):
        """Test getting primary rejection reason."""
        result = MatchResult(
            application_id=uuid.uuid4(),
            lender_id="test_lender",
            is_eligible=False,
            fit_score=0,
            criteria_results={},
            rejection_reasons=[
                "Credit score too low",
                "State restricted",
            ],
        )
        assert result.primary_rejection_reason == "Credit score too low"

    def test_primary_rejection_reason_none_when_empty(self):
        """Test that primary_rejection_reason is None when no reasons."""
        result = MatchResult(
            application_id=uuid.uuid4(),
            lender_id="test_lender",
            is_eligible=True,
            fit_score=85,
            criteria_results={},
            rejection_reasons=[],
        )
        assert result.primary_rejection_reason is None


class TestGetFailedPassedCriteria:
    """Tests for get_failed_criteria and get_passed_criteria methods."""

    def test_get_failed_criteria(self):
        """Test getting list of failed criteria."""
        result = MatchResult(
            application_id=uuid.uuid4(),
            lender_id="test_lender",
            is_eligible=False,
            fit_score=0,
            criteria_results={
                "credit_score": {"passed": False},
                "time_in_business": {"passed": True},
                "state": {"passed": False},
            },
        )
        failed = result.get_failed_criteria()
        assert len(failed) == 2
        assert "credit_score" in failed
        assert "state" in failed
        assert "time_in_business" not in failed

    def test_get_passed_criteria(self):
        """Test getting list of passed criteria."""
        result = MatchResult(
            application_id=uuid.uuid4(),
            lender_id="test_lender",
            is_eligible=True,
            fit_score=85,
            criteria_results={
                "credit_score": {"passed": True},
                "time_in_business": {"passed": True},
                "state": {"passed": True},
            },
        )
        passed = result.get_passed_criteria()
        assert len(passed) == 3
        assert "credit_score" in passed
        assert "time_in_business" in passed
        assert "state" in passed


class TestMatchResultRepr:
    """Tests for MatchResult __repr__."""

    def test_repr_format(self):
        """Test that __repr__ returns expected format."""
        result = MatchResult(
            application_id=uuid.uuid4(),
            lender_id="citizens_bank",
            is_eligible=True,
            fit_score=85,
            criteria_results={},
        )
        repr_str = repr(result)
        assert "MatchResult" in repr_str
        assert "citizens_bank" in repr_str
        assert "eligible=True" in repr_str
        assert "score=85" in repr_str
