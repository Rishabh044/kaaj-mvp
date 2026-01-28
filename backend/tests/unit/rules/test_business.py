"""Unit tests for business requirements rule."""

import pytest

from app.rules.base import EvaluationContext
from app.rules.criteria.business import BusinessRequirementsRule


class TestTimeInBusinessPasses:
    """Tests for time in business meeting requirements."""

    def test_time_in_business_meets_minimum(self):
        """Test TIB exactly at minimum passes."""
        rule = BusinessRequirementsRule()
        context = EvaluationContext(application_id="test", years_in_business=2.0)
        result = rule.evaluate(context, {"min_time_in_business_years": 2})

        assert result.passed is True

    def test_time_in_business_exceeds_minimum(self):
        """Test TIB above minimum passes."""
        rule = BusinessRequirementsRule()
        context = EvaluationContext(application_id="test", years_in_business=5.0)
        result = rule.evaluate(context, {"min_time_in_business_years": 2})

        assert result.passed is True


class TestTimeInBusinessFails:
    """Tests for time in business failing requirements."""

    def test_time_in_business_below_minimum(self):
        """Test TIB below minimum fails."""
        rule = BusinessRequirementsRule()
        context = EvaluationContext(application_id="test", years_in_business=1.5)
        result = rule.evaluate(context, {"min_time_in_business_years": 2})

        assert result.passed is False
        assert "1.5" in result.message
        assert "below" in result.message.lower()


class TestHomeownerRequiredPasses:
    """Tests for homeowner requirement passing."""

    def test_homeowner_required_and_is_homeowner(self):
        """Test homeowner requirement when applicant is homeowner."""
        rule = BusinessRequirementsRule()
        context = EvaluationContext(application_id="test", is_homeowner=True)
        result = rule.evaluate(context, {"requires_homeowner": True})

        assert result.passed is True


class TestHomeownerRequiredFails:
    """Tests for homeowner requirement failing."""

    def test_homeowner_required_but_not_homeowner(self):
        """Test homeowner requirement when applicant is not homeowner."""
        rule = BusinessRequirementsRule()
        context = EvaluationContext(application_id="test", is_homeowner=False)
        result = rule.evaluate(context, {"requires_homeowner": True})

        assert result.passed is False
        assert "homeowner" in result.message.lower()


class TestCDLConditionalTrucking:
    """Tests for conditional CDL requirement."""

    def test_cdl_conditional_trucking_has_cdl(self):
        """Test CDL conditional when trucking and has CDL."""
        rule = BusinessRequirementsRule()
        context = EvaluationContext(
            application_id="test",
            has_cdl=True,
            equipment_category="class_8_truck",
        )
        result = rule.evaluate(context, {"requires_cdl": "conditional"})

        assert result.passed is True

    def test_cdl_conditional_trucking_no_cdl(self):
        """Test CDL conditional when trucking but no CDL."""
        rule = BusinessRequirementsRule()
        context = EvaluationContext(
            application_id="test",
            has_cdl=False,
            equipment_category="class_8_truck",
        )
        result = rule.evaluate(context, {"requires_cdl": "conditional"})

        assert result.passed is False
        assert "cdl" in result.message.lower()


class TestCDLNotRequiredNonTrucking:
    """Tests for CDL not required for non-trucking."""

    def test_cdl_conditional_non_trucking(self):
        """Test CDL conditional for non-trucking equipment."""
        rule = BusinessRequirementsRule()
        context = EvaluationContext(
            application_id="test",
            has_cdl=False,
            equipment_category="construction",
        )
        result = rule.evaluate(context, {"requires_cdl": "conditional"})

        # Should pass because not trucking
        assert result.passed is True


class TestCDLYearsMinimum:
    """Tests for CDL years minimum requirement."""

    def test_cdl_years_meets_minimum(self):
        """Test CDL years meeting minimum."""
        rule = BusinessRequirementsRule()
        context = EvaluationContext(
            application_id="test",
            has_cdl=True,
            cdl_years=5,
        )
        result = rule.evaluate(context, {"min_cdl_years": 5})

        assert result.passed is True

    def test_cdl_years_below_minimum(self):
        """Test CDL years below minimum."""
        rule = BusinessRequirementsRule()
        context = EvaluationContext(
            application_id="test",
            has_cdl=True,
            cdl_years=2,
        )
        result = rule.evaluate(context, {"min_cdl_years": 5})

        assert result.passed is False


class TestIndustryExperienceMinimum:
    """Tests for industry experience minimum."""

    def test_industry_experience_meets_minimum(self):
        """Test industry experience meeting minimum."""
        rule = BusinessRequirementsRule()
        context = EvaluationContext(
            application_id="test",
            industry_experience_years=10,
        )
        result = rule.evaluate(context, {"min_industry_experience_years": 5})

        assert result.passed is True

    def test_industry_experience_below_minimum(self):
        """Test industry experience below minimum."""
        rule = BusinessRequirementsRule()
        context = EvaluationContext(
            application_id="test",
            industry_experience_years=3,
        )
        result = rule.evaluate(context, {"min_industry_experience_years": 5})

        assert result.passed is False


class TestFleetSizeMinimum:
    """Tests for fleet size minimum."""

    def test_fleet_size_meets_minimum(self):
        """Test fleet size meeting minimum."""
        rule = BusinessRequirementsRule()
        context = EvaluationContext(application_id="test", fleet_size=5)
        result = rule.evaluate(context, {"min_fleet_size": 3})

        assert result.passed is True

    def test_fleet_size_below_minimum(self):
        """Test fleet size below minimum."""
        rule = BusinessRequirementsRule()
        context = EvaluationContext(application_id="test", fleet_size=1)
        result = rule.evaluate(context, {"min_fleet_size": 3})

        assert result.passed is False


class TestMultipleRequirementsAllMustPass:
    """Tests for multiple requirements all needing to pass."""

    def test_all_requirements_pass(self):
        """Test when all requirements pass."""
        rule = BusinessRequirementsRule()
        context = EvaluationContext(
            application_id="test",
            years_in_business=5.0,
            is_homeowner=True,
            has_cdl=True,
        )
        result = rule.evaluate(
            context,
            {
                "min_time_in_business_years": 2,
                "requires_homeowner": True,
                "requires_cdl": True,
            },
        )

        assert result.passed is True

    def test_one_requirement_fails(self):
        """Test when one requirement fails."""
        rule = BusinessRequirementsRule()
        context = EvaluationContext(
            application_id="test",
            years_in_business=5.0,
            is_homeowner=False,  # This will fail
            has_cdl=True,
        )
        result = rule.evaluate(
            context,
            {
                "min_time_in_business_years": 2,
                "requires_homeowner": True,
                "requires_cdl": True,
            },
        )

        assert result.passed is False
        assert result.details is not None
        assert "failed_checks" in result.details
