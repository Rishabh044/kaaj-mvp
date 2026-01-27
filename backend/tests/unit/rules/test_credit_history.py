"""Unit tests for credit history rules."""

import pytest

from app.rules.base import EvaluationContext
from app.rules.criteria.credit_history import CreditHistoryRule


class TestNoBankruptcyPasses:
    """Tests for no bankruptcy passing."""

    def test_no_bankruptcy_passes(self):
        """Test no bankruptcy passes when not allowed."""
        rule = CreditHistoryRule()
        context = EvaluationContext(application_id="test", has_bankruptcy=False)
        result = rule.evaluate(context, {"max_bankruptcies": 0})

        assert result.passed is True


class TestBankruptcyWithinDischargePeriod:
    """Tests for bankruptcy within discharge period."""

    def test_bankruptcy_meets_discharge_requirement(self):
        """Test bankruptcy discharged long enough ago."""
        rule = CreditHistoryRule()
        context = EvaluationContext(
            application_id="test",
            has_bankruptcy=True,
            bankruptcy_discharge_years=5.5,
            bankruptcy_chapter="7",
        )
        result = rule.evaluate(
            context,
            {"max_bankruptcies": 1, "bankruptcy_min_discharge_years": 5},
        )

        assert result.passed is True


class TestBankruptcyOutsideDischargePeriod:
    """Tests for bankruptcy outside required discharge period."""

    def test_bankruptcy_too_recent(self):
        """Test bankruptcy discharged too recently fails."""
        rule = CreditHistoryRule()
        context = EvaluationContext(
            application_id="test",
            has_bankruptcy=True,
            bankruptcy_discharge_years=3.0,
            bankruptcy_chapter="7",
        )
        result = rule.evaluate(
            context,
            {"max_bankruptcies": 1, "bankruptcy_min_discharge_years": 5},
        )

        assert result.passed is False
        assert "3.0" in result.message
        assert "5" in result.message


class TestActiveBankruptcyFails:
    """Tests for active bankruptcy failing."""

    def test_active_bankruptcy_no_discharge_date(self):
        """Test active bankruptcy (no discharge) fails."""
        rule = CreditHistoryRule()
        context = EvaluationContext(
            application_id="test",
            has_bankruptcy=True,
            bankruptcy_discharge_years=None,  # No discharge
            bankruptcy_chapter="7",
        )
        result = rule.evaluate(context, {"max_bankruptcies": 1})

        assert result.passed is False
        assert "active" in result.message.lower()


class TestOpenJudgementsNotAllowed:
    """Tests for open judgements not allowed."""

    def test_open_judgements_not_allowed(self):
        """Test open judgements when not allowed fails."""
        rule = CreditHistoryRule()
        context = EvaluationContext(
            application_id="test",
            has_open_judgements=True,
            judgement_amount=5000,
        )
        result = rule.evaluate(context, {"max_open_judgements": 0})

        assert result.passed is False
        assert "judgement" in result.message.lower()


class TestOpenJudgementsAllowedWithLimit:
    """Tests for open judgements allowed with limit."""

    def test_judgement_amount_within_limit(self):
        """Test judgement amount within allowed limit."""
        rule = CreditHistoryRule()
        context = EvaluationContext(
            application_id="test",
            has_open_judgements=True,
            judgement_amount=3000,
        )
        result = rule.evaluate(
            context,
            {"max_open_judgements": 1, "max_judgement_amount": 5000},
        )

        assert result.passed is True

    def test_judgement_amount_exceeds_limit(self):
        """Test judgement amount exceeding limit fails."""
        rule = CreditHistoryRule()
        context = EvaluationContext(
            application_id="test",
            has_open_judgements=True,
            judgement_amount=10000,
        )
        result = rule.evaluate(
            context,
            {"max_open_judgements": 1, "max_judgement_amount": 5000},
        )

        assert result.passed is False
        assert "$10,000" in result.actual_value


class TestForeclosureCheck:
    """Tests for foreclosure check."""

    def test_no_foreclosure_passes(self):
        """Test no foreclosure passes."""
        rule = CreditHistoryRule()
        context = EvaluationContext(
            application_id="test",
            has_foreclosure=False,
        )
        result = rule.evaluate(context, {"allows_foreclosure": False})

        assert result.passed is True

    def test_foreclosure_not_allowed(self):
        """Test foreclosure when not allowed fails."""
        rule = CreditHistoryRule()
        context = EvaluationContext(
            application_id="test",
            has_foreclosure=True,
        )
        result = rule.evaluate(context, {"allows_foreclosure": False})

        assert result.passed is False
        assert "foreclosure" in result.message.lower()


class TestRepossessionCheck:
    """Tests for repossession check."""

    def test_repossession_not_allowed(self):
        """Test repossession when not allowed fails."""
        rule = CreditHistoryRule()
        context = EvaluationContext(
            application_id="test",
            has_repossession=True,
        )
        result = rule.evaluate(context, {"allows_repossession": False})

        assert result.passed is False
        assert "repossession" in result.message.lower()

    def test_repossession_allowed_by_default(self):
        """Test repossession allowed by default."""
        rule = CreditHistoryRule()
        context = EvaluationContext(
            application_id="test",
            has_repossession=True,
        )
        result = rule.evaluate(context, {})

        assert result.passed is True


class TestTaxLiensCheck:
    """Tests for tax liens check."""

    def test_tax_liens_not_allowed(self):
        """Test tax liens when not allowed fails."""
        rule = CreditHistoryRule()
        context = EvaluationContext(
            application_id="test",
            has_tax_liens=True,
            tax_lien_amount=5000,
        )
        result = rule.evaluate(context, {"max_tax_liens": 0})

        assert result.passed is False
        assert "tax lien" in result.message.lower()


class TestMultipleCreditIssues:
    """Tests for multiple credit issues."""

    def test_multiple_issues_fail_on_first(self):
        """Test multiple issues fails on first encountered."""
        rule = CreditHistoryRule()
        context = EvaluationContext(
            application_id="test",
            has_bankruptcy=True,
            bankruptcy_discharge_years=2.0,
            has_open_judgements=True,
            has_tax_liens=True,
        )
        result = rule.evaluate(
            context,
            {
                "max_bankruptcies": 1,
                "bankruptcy_min_discharge_years": 5,
                "max_open_judgements": 0,
                "max_tax_liens": 0,
            },
        )

        assert result.passed is False
        # Should fail on bankruptcy discharge period first
        assert "bankruptcy" in result.message.lower()
