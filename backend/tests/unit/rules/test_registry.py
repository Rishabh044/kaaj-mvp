"""Unit tests for rule registry."""

import pytest

from app.rules.base import EvaluationContext, Rule, RuleResult
from app.rules.registry import RuleRegistry, get_rule


class MockRule(Rule):
    """Mock rule for testing."""

    @property
    def rule_type(self) -> str:
        return "mock"

    def evaluate(self, context: EvaluationContext, criteria: dict) -> RuleResult:
        return RuleResult(
            passed=True,
            rule_name="Mock Rule",
            required_value="Any",
            actual_value="Any",
            message="Mock passed",
            score=100,
        )


class TestRegisterDecorator:
    """Tests for register decorator."""

    def setup_method(self):
        """Clear registry before each test."""
        RuleRegistry.clear()

    def test_register_decorator(self):
        """Test registering a rule with decorator."""

        @RuleRegistry.register("test_rule")
        class TestRule(Rule):
            @property
            def rule_type(self) -> str:
                return "test_rule"

            def evaluate(self, context, criteria):
                return RuleResult(
                    passed=True,
                    rule_name="Test",
                    required_value="X",
                    actual_value="Y",
                    message="OK",
                )

        assert RuleRegistry.has_rule("test_rule")
        assert "test_rule" in RuleRegistry.list_rules()

    def test_register_non_rule_raises(self):
        """Test that registering a non-Rule class raises TypeError."""
        with pytest.raises(TypeError):

            @RuleRegistry.register("not_a_rule")
            class NotARule:
                pass


class TestGetRegisteredRule:
    """Tests for getting registered rules."""

    def setup_method(self):
        """Set up registry with a test rule."""
        RuleRegistry.clear()
        RuleRegistry.register("mock_rule")(MockRule)

    def test_get_registered_rule(self):
        """Test getting a registered rule."""
        rule = RuleRegistry.get_rule("mock_rule")
        assert isinstance(rule, MockRule)

    def test_get_rule_returns_same_instance(self):
        """Test that get_rule returns cached instance."""
        rule1 = RuleRegistry.get_rule("mock_rule")
        rule2 = RuleRegistry.get_rule("mock_rule")
        assert rule1 is rule2

    def test_get_rule_function(self):
        """Test convenience get_rule function."""
        rule = get_rule("mock_rule")
        assert isinstance(rule, MockRule)


class TestGetUnregisteredRuleRaises:
    """Tests for getting unregistered rules."""

    def setup_method(self):
        """Clear registry before each test."""
        RuleRegistry.clear()

    def test_get_unregistered_rule_raises(self):
        """Test that getting an unregistered rule raises KeyError."""
        with pytest.raises(KeyError) as exc_info:
            RuleRegistry.get_rule("nonexistent")
        assert "nonexistent" in str(exc_info.value)

    def test_get_rule_class_unregistered_raises(self):
        """Test that get_rule_class raises for unregistered rule."""
        with pytest.raises(KeyError):
            RuleRegistry.get_rule_class("nonexistent")


class TestListAllRules:
    """Tests for listing all rules."""

    def setup_method(self):
        """Clear and populate registry."""
        RuleRegistry.clear()

        @RuleRegistry.register("rule_a")
        class RuleA(MockRule):
            pass

        @RuleRegistry.register("rule_b")
        class RuleB(MockRule):
            pass

    def test_list_all_rules(self):
        """Test listing all registered rules."""
        rules = RuleRegistry.list_rules()
        assert "rule_a" in rules
        assert "rule_b" in rules
        assert len(rules) == 2

    def test_has_rule(self):
        """Test checking if rule exists."""
        assert RuleRegistry.has_rule("rule_a") is True
        assert RuleRegistry.has_rule("rule_c") is False


class TestClearRegistry:
    """Tests for clearing the registry."""

    def test_clear_removes_all_rules(self):
        """Test that clear removes all rules."""
        RuleRegistry.register("temp_rule")(MockRule)
        assert RuleRegistry.has_rule("temp_rule")

        RuleRegistry.clear()
        assert not RuleRegistry.has_rule("temp_rule")
        assert len(RuleRegistry.list_rules()) == 0
