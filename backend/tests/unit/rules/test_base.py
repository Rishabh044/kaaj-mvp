"""Unit tests for rule engine base classes."""

import pytest

from app.rules.base import EvaluationContext, Rule, RuleResult


class TestEvaluationContextCreation:
    """Tests for creating EvaluationContext instances."""

    def test_evaluation_context_creation_minimal(self):
        """Test creating context with minimal fields."""
        context = EvaluationContext(application_id="test-123")
        assert context.application_id == "test-123"
        assert context.fico_score is None
        assert context.is_homeowner is False
        assert context.loan_amount == 0

    def test_evaluation_context_creation_full(self):
        """Test creating context with all fields."""
        context = EvaluationContext(
            application_id="test-456",
            fico_score=720,
            transunion_score=715,
            years_in_business=5.0,
            state="TX",
            is_homeowner=True,
            loan_amount=10000000,
            equipment_category="class_8_truck",
            equipment_age_years=3,
        )
        assert context.fico_score == 720
        assert context.transunion_score == 715
        assert context.years_in_business == 5.0
        assert context.is_homeowner is True


class TestEvaluationContextOptionalFields:
    """Tests for optional fields in EvaluationContext."""

    def test_optional_credit_scores_default_none(self):
        """Test that optional credit scores default to None."""
        context = EvaluationContext(application_id="test")
        assert context.fico_score is None
        assert context.transunion_score is None
        assert context.experian_score is None
        assert context.equifax_score is None
        assert context.paynet_score is None

    def test_optional_business_fields_default(self):
        """Test that optional business fields have correct defaults."""
        context = EvaluationContext(application_id="test")
        assert context.annual_revenue is None
        assert context.fleet_size is None
        assert context.cdl_years is None


class TestEvaluationContextGetCreditScore:
    """Tests for get_credit_score method."""

    def test_get_fico_score(self):
        """Test getting FICO score."""
        context = EvaluationContext(application_id="test", fico_score=720)
        assert context.get_credit_score("fico") == 720
        assert context.get_credit_score("FICO") == 720

    def test_get_transunion_score(self):
        """Test getting TransUnion score."""
        context = EvaluationContext(application_id="test", transunion_score=715)
        assert context.get_credit_score("transunion") == 715

    def test_get_paynet_score(self):
        """Test getting PayNet score."""
        context = EvaluationContext(application_id="test", paynet_score=85)
        assert context.get_credit_score("paynet") == 85

    def test_get_missing_score_returns_none(self):
        """Test that missing score returns None."""
        context = EvaluationContext(application_id="test")
        assert context.get_credit_score("fico") is None

    def test_get_invalid_score_type_returns_none(self):
        """Test that invalid score type returns None."""
        context = EvaluationContext(application_id="test", fico_score=720)
        assert context.get_credit_score("invalid") is None


class TestEvaluationContextIsTrucking:
    """Tests for is_trucking property."""

    def test_is_trucking_true_for_class_8(self):
        """Test is_trucking for class 8 truck."""
        context = EvaluationContext(
            application_id="test", equipment_category="class_8_truck"
        )
        assert context.is_trucking is True

    def test_is_trucking_true_for_trailer(self):
        """Test is_trucking for trailer."""
        context = EvaluationContext(application_id="test", equipment_category="trailer")
        assert context.is_trucking is True

    def test_is_trucking_false_for_construction(self):
        """Test is_trucking for construction equipment."""
        context = EvaluationContext(
            application_id="test", equipment_category="construction"
        )
        assert context.is_trucking is False


class TestEvaluationContextIsStartup:
    """Tests for is_startup property."""

    def test_is_startup_true(self):
        """Test is_startup for new business."""
        context = EvaluationContext(application_id="test", years_in_business=1.5)
        assert context.is_startup is True

    def test_is_startup_false(self):
        """Test is_startup for established business."""
        context = EvaluationContext(application_id="test", years_in_business=5.0)
        assert context.is_startup is False

    def test_is_startup_boundary(self):
        """Test is_startup at 2 year boundary."""
        context = EvaluationContext(application_id="test", years_in_business=2.0)
        assert context.is_startup is False


class TestRuleResultPassedProperty:
    """Tests for RuleResult passed property."""

    def test_passed_result(self):
        """Test creating a passed result."""
        result = RuleResult(
            passed=True,
            rule_name="Test Rule",
            required_value="100",
            actual_value="150",
            message="Test passed",
            score=85.0,
        )
        assert result.passed is True
        assert result.score == 85.0

    def test_failed_result(self):
        """Test creating a failed result."""
        result = RuleResult(
            passed=False,
            rule_name="Test Rule",
            required_value="100",
            actual_value="50",
            message="Test failed",
            score=0.0,
        )
        assert result.passed is False
        assert result.score == 0.0


class TestRuleResultScoreBounds:
    """Tests for RuleResult score bounds."""

    def test_score_at_minimum(self):
        """Test score at minimum (0)."""
        result = RuleResult(
            passed=False,
            rule_name="Test",
            required_value="X",
            actual_value="Y",
            message="Test",
            score=0,
        )
        assert result.score == 0

    def test_score_at_maximum(self):
        """Test score at maximum (100)."""
        result = RuleResult(
            passed=True,
            rule_name="Test",
            required_value="X",
            actual_value="Y",
            message="Test",
            score=100,
        )
        assert result.score == 100

    def test_score_below_minimum_clamped(self):
        """Test score below minimum is clamped to 0."""
        result = RuleResult(
            passed=False,
            rule_name="Test",
            required_value="X",
            actual_value="Y",
            message="Test",
            score=-10,
        )
        assert result.score == 0

    def test_score_above_maximum_clamped(self):
        """Test score above maximum is clamped to 100."""
        result = RuleResult(
            passed=True,
            rule_name="Test",
            required_value="X",
            actual_value="Y",
            message="Test",
            score=150,
        )
        assert result.score == 100


class TestRuleResultToDict:
    """Tests for RuleResult to_dict method."""

    def test_to_dict(self):
        """Test converting RuleResult to dict."""
        result = RuleResult(
            passed=True,
            rule_name="Test Rule",
            required_value="100",
            actual_value="150",
            message="Test passed",
            score=85.0,
            details={"extra": "info"},
        )
        d = result.to_dict()
        assert d["passed"] is True
        assert d["rule_name"] == "Test Rule"
        assert d["required_value"] == "100"
        assert d["actual_value"] == "150"
        assert d["message"] == "Test passed"
        assert d["score_contribution"] == 85.0
        assert d["details"] == {"extra": "info"}
