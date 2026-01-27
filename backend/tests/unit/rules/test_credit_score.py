"""Unit tests for credit score rules."""

import pytest

from app.rules.base import EvaluationContext
from app.rules.criteria.credit_score import CreditScoreRule


class TestFicoScorePassesWhenMeetsMinimum:
    """Tests for FICO score meeting minimum."""

    def test_fico_meets_minimum(self):
        """Test FICO score exactly at minimum passes."""
        rule = CreditScoreRule()
        context = EvaluationContext(application_id="test", fico_score=700)
        result = rule.evaluate(context, {"type": "fico", "min": 700})

        assert result.passed is True
        assert "700" in result.message
        assert result.score >= 70

    def test_fico_exceeds_minimum(self):
        """Test FICO score above minimum passes with bonus."""
        rule = CreditScoreRule()
        context = EvaluationContext(application_id="test", fico_score=750)
        result = rule.evaluate(context, {"type": "fico", "min": 700})

        assert result.passed is True
        assert result.score > 70  # Should have bonus for exceeding


class TestFicoScoreFailsWhenBelowMinimum:
    """Tests for FICO score below minimum."""

    def test_fico_below_minimum(self):
        """Test FICO score below minimum fails."""
        rule = CreditScoreRule()
        context = EvaluationContext(application_id="test", fico_score=650)
        result = rule.evaluate(context, {"type": "fico", "min": 700})

        assert result.passed is False
        assert "650" in result.message
        assert "below" in result.message.lower()
        assert result.score == 0


class TestFicoScoreNotProvided:
    """Tests for missing FICO score."""

    def test_fico_not_provided(self):
        """Test missing FICO score fails."""
        rule = CreditScoreRule()
        context = EvaluationContext(application_id="test")  # No fico_score
        result = rule.evaluate(context, {"type": "fico", "min": 700})

        assert result.passed is False
        assert "not provided" in result.message.lower()
        assert result.score == 0


class TestFicoScoreBonusCalculation:
    """Tests for FICO score bonus calculation."""

    def test_bonus_for_high_score(self):
        """Test bonus for significantly exceeding minimum."""
        rule = CreditScoreRule()
        context = EvaluationContext(application_id="test", fico_score=800)
        result = rule.evaluate(context, {"type": "fico", "min": 700})

        assert result.passed is True
        # Excess is 100, bonus should be 30 (capped)
        assert result.score == 100  # 70 base + 30 bonus

    def test_small_bonus_for_slight_excess(self):
        """Test small bonus for slightly exceeding minimum."""
        rule = CreditScoreRule()
        context = EvaluationContext(application_id="test", fico_score=710)
        result = rule.evaluate(context, {"type": "fico", "min": 700})

        assert result.passed is True
        # Excess is 10, bonus should be 3
        assert 70 < result.score < 80


class TestTransUnionScoreEvaluation:
    """Tests for TransUnion score evaluation."""

    def test_transunion_meets_minimum(self):
        """Test TransUnion score meeting minimum."""
        rule = CreditScoreRule()
        context = EvaluationContext(application_id="test", transunion_score=720)
        result = rule.evaluate(context, {"type": "transunion", "min": 700})

        assert result.passed is True
        assert "transunion" in result.rule_name.lower()

    def test_transunion_below_minimum(self):
        """Test TransUnion score below minimum."""
        rule = CreditScoreRule()
        context = EvaluationContext(application_id="test", transunion_score=680)
        result = rule.evaluate(context, {"type": "transunion", "min": 700})

        assert result.passed is False


class TestPayNetScoreEvaluation:
    """Tests for PayNet (business) score evaluation."""

    def test_paynet_meets_minimum(self):
        """Test PayNet score meeting minimum."""
        rule = CreditScoreRule()
        context = EvaluationContext(application_id="test", paynet_score=85)
        result = rule.evaluate(context, {"type": "paynet", "min": 75})

        assert result.passed is True

    def test_paynet_below_minimum(self):
        """Test PayNet score below minimum."""
        rule = CreditScoreRule()
        context = EvaluationContext(application_id="test", paynet_score=65)
        result = rule.evaluate(context, {"type": "paynet", "min": 75})

        assert result.passed is False


class TestScoreTypeSelection:
    """Tests for score type selection."""

    def test_defaults_to_fico(self):
        """Test that default score type is FICO."""
        rule = CreditScoreRule()
        context = EvaluationContext(
            application_id="test",
            fico_score=720,
            transunion_score=700,  # Lower but shouldn't be used
        )
        result = rule.evaluate(context, {"min": 710})  # No type specified

        assert result.passed is True
        assert "fico" in result.rule_name.lower()

