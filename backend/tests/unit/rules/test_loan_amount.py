"""Unit tests for loan amount rules."""

import pytest

from app.rules.base import EvaluationContext
from app.rules.criteria.loan_amount import LoanAmountRule


class TestAmountWithinRange:
    """Tests for loan amount within allowed range."""

    def test_amount_within_min_max(self):
        """Test amount within min and max passes."""
        rule = LoanAmountRule()
        context = EvaluationContext(
            application_id="test",
            loan_amount=5000000,  # $50,000
        )
        result = rule.evaluate(
            context,
            {
                "min_amount": 2500000,  # $25,000
                "max_amount": 10000000,  # $100,000
            },
        )

        assert result.passed is True
        assert "$50,000" in result.actual_value

    def test_amount_at_minimum(self):
        """Test amount exactly at minimum passes."""
        rule = LoanAmountRule()
        context = EvaluationContext(
            application_id="test",
            loan_amount=2500000,
        )
        result = rule.evaluate(context, {"min_amount": 2500000})

        assert result.passed is True

    def test_amount_at_maximum(self):
        """Test amount exactly at maximum passes."""
        rule = LoanAmountRule()
        context = EvaluationContext(
            application_id="test",
            loan_amount=10000000,
        )
        result = rule.evaluate(context, {"max_amount": 10000000})

        assert result.passed is True


class TestAmountBelowMinimum:
    """Tests for loan amount below minimum."""

    def test_amount_below_minimum(self):
        """Test amount below minimum fails."""
        rule = LoanAmountRule()
        context = EvaluationContext(
            application_id="test",
            loan_amount=1500000,  # $15,000
        )
        result = rule.evaluate(
            context,
            {"min_amount": 2500000},  # $25,000
        )

        assert result.passed is False
        assert "$15,000" in result.actual_value
        assert "$25,000" in result.required_value
        assert "below" in result.message.lower()


class TestAmountAboveMaximum:
    """Tests for loan amount above maximum."""

    def test_amount_above_maximum(self):
        """Test amount above maximum fails."""
        rule = LoanAmountRule()
        context = EvaluationContext(
            application_id="test",
            loan_amount=15000000,  # $150,000
        )
        result = rule.evaluate(
            context,
            {"max_amount": 10000000},  # $100,000
        )

        assert result.passed is False
        assert "$150,000" in result.actual_value
        assert "$100,000" in result.required_value
        assert "exceed" in result.message.lower()


class TestNoLimitsAlwaysPasses:
    """Tests for no limits always passing."""

    def test_no_limits_any_amount_passes(self):
        """Test any amount passes when no limits set."""
        rule = LoanAmountRule()
        context = EvaluationContext(
            application_id="test",
            loan_amount=100000000,  # $1,000,000
        )
        result = rule.evaluate(context, {})

        assert result.passed is True

    def test_only_min_limit(self):
        """Test with only minimum limit."""
        rule = LoanAmountRule()
        context = EvaluationContext(
            application_id="test",
            loan_amount=100000000,
        )
        result = rule.evaluate(context, {"min_amount": 1000000})

        assert result.passed is True

    def test_only_max_limit(self):
        """Test with only maximum limit."""
        rule = LoanAmountRule()
        context = EvaluationContext(
            application_id="test",
            loan_amount=5000000,
        )
        result = rule.evaluate(context, {"max_amount": 10000000})

        assert result.passed is True
