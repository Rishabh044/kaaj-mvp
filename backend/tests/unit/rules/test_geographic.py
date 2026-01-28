"""Unit tests for geographic restriction rules."""

import pytest

from app.rules.base import EvaluationContext
from app.rules.criteria.geographic import StateRestrictionRule


class TestStateAllowed:
    """Tests for allowed states."""

    def test_state_not_in_exclusion_list(self):
        """Test state not in exclusion list passes."""
        rule = StateRestrictionRule()
        context = EvaluationContext(application_id="test", state="TX")
        result = rule.evaluate(context, {"excluded_states": ["CA", "NY"]})

        assert result.passed is True
        assert "TX" in result.actual_value

    def test_state_in_allowed_list(self):
        """Test state in allowed list passes."""
        rule = StateRestrictionRule()
        context = EvaluationContext(application_id="test", state="TX")
        result = rule.evaluate(context, {"allowed_states": ["TX", "OK", "LA"]})

        assert result.passed is True


class TestStateExcluded:
    """Tests for excluded states."""

    def test_state_in_exclusion_list(self):
        """Test state in exclusion list fails."""
        rule = StateRestrictionRule()
        context = EvaluationContext(application_id="test", state="CA")
        result = rule.evaluate(context, {"excluded_states": ["CA", "NY"]})

        assert result.passed is False
        assert "CA" in result.message
        assert "excluded" in result.message.lower()

    def test_state_not_in_allowed_list(self):
        """Test state not in allowed list fails."""
        rule = StateRestrictionRule()
        context = EvaluationContext(application_id="test", state="FL")
        result = rule.evaluate(context, {"allowed_states": ["TX", "OK", "LA"]})

        assert result.passed is False
        assert "FL" in result.actual_value


class TestEmptyExclusionList:
    """Tests for empty exclusion list."""

    def test_empty_exclusion_list_allows_all(self):
        """Test empty exclusion list allows all states."""
        rule = StateRestrictionRule()
        context = EvaluationContext(application_id="test", state="CA")
        result = rule.evaluate(context, {"excluded_states": []})

        assert result.passed is True

    def test_no_exclusion_criteria_allows_all(self):
        """Test no exclusion criteria allows all states."""
        rule = StateRestrictionRule()
        context = EvaluationContext(application_id="test", state="NY")
        result = rule.evaluate(context, {})

        assert result.passed is True


class TestCaseInsensitiveState:
    """Tests for case insensitive state matching."""

    def test_lowercase_state_in_context(self):
        """Test lowercase state in context is normalized."""
        rule = StateRestrictionRule()
        context = EvaluationContext(application_id="test", state="ca")
        result = rule.evaluate(context, {"excluded_states": ["CA", "NY"]})

        assert result.passed is False

    def test_mixed_case_in_exclusion_list(self):
        """Test mixed case in exclusion list works."""
        rule = StateRestrictionRule()
        context = EvaluationContext(application_id="test", state="CA")
        result = rule.evaluate(context, {"excluded_states": ["ca", "ny"]})

        assert result.passed is False
