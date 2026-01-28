"""Unit tests for evaluation context builder."""

from datetime import datetime, timedelta

import pytest

from app.rules.context_builder import (
    build_evaluation_context,
)


class TestBuildContextFullApplication:
    """Tests for building context with full application data."""

    def test_build_context_full_application(self):
        """Test building context with all data provided."""
        context = build_evaluation_context(
            application_id="app-123",
            business={
                "name": "Test Business LLC",
                "years_in_business": 5.0,
                "industry_code": "trucking",
                "industry_name": "Transportation",
                "state": "TX",
                "annual_revenue": 100000000,  # $1M
                "fleet_size": 10,
            },
            guarantor={
                "fico_score": 720,
                "transunion_score": 710,
                "experian_score": 715,
                "equifax_score": 725,
                "is_homeowner": True,
                "is_us_citizen": True,
                "has_cdl": True,
                "cdl_years": 8,
                "industry_experience_years": 12,
                "has_bankruptcy": False,
            },
            business_credit={
                "paynet_score": 85,
                "paynet_master_score": 680,
                "paydex_score": 75,
            },
            loan_request={
                "loan_amount": 5000000,  # $50,000
                "requested_term_months": 48,
                "transaction_type": "purchase",
                "is_private_party": False,
            },
            equipment={
                "category": "class_8_truck",
                "type": "Day Cab",
                "year": 2021,
                "mileage": 150000,
                "condition": "used",
            },
        )

        # Application reference
        assert context.application_id == "app-123"

        # Personal credit scores
        assert context.fico_score == 720
        assert context.transunion_score == 710
        assert context.experian_score == 715
        assert context.equifax_score == 725

        # Business credit scores
        assert context.paynet_score == 85
        assert context.paynet_master_score == 680

        # Business info
        assert context.business_name == "Test Business LLC"
        assert context.years_in_business == 5.0
        assert context.state == "TX"
        assert context.fleet_size == 10

        # Guarantor info
        assert context.is_homeowner is True
        assert context.has_cdl is True
        assert context.cdl_years == 8

        # Loan request
        assert context.loan_amount == 5000000

        # Equipment
        assert context.equipment_category == "class_8_truck"
        assert context.equipment_year == 2021


class TestBuildContextMinimalApplication:
    """Tests for building context with minimal data."""

    def test_build_context_minimal_application(self):
        """Test building context with only required data."""
        context = build_evaluation_context(application_id="app-456")

        assert context.application_id == "app-456"
        # All optional fields should have defaults
        assert context.fico_score is None
        assert context.years_in_business == 0.0
        assert context.is_homeowner is False
        assert context.has_bankruptcy is False
        assert context.loan_amount == 0


class TestBuildContextWithBusinessCredit:
    """Tests for building context with business credit data."""

    def test_build_context_with_business_credit(self):
        """Test business credit scores are properly mapped."""
        context = build_evaluation_context(
            application_id="app-789",
            business_credit={
                "paynet_score": 90,
                "paynet_master_score": 700,
                "paydex_score": 80,
            },
        )

        assert context.paynet_score == 90
        assert context.paynet_master_score == 700
        assert context.paydex_score == 80


class TestDerivedFeaturesOverride:
    """Tests for derived features overriding calculated values."""

    def test_equipment_age_derived_feature(self):
        """Test derived equipment age overrides calculation."""
        context = build_evaluation_context(
            application_id="app-123",
            equipment={"year": 2020},
            derived_features={"equipment_age_years": 3},  # Override
        )

        # Should use derived value, not calculated
        assert context.equipment_age_years == 3

    def test_years_in_business_derived_feature(self):
        """Test derived years in business overrides business data."""
        context = build_evaluation_context(
            application_id="app-123",
            business={"years_in_business": 5.0},
            derived_features={"years_in_business": 7.5},
        )

        assert context.years_in_business == 7.5

    def test_bankruptcy_discharge_years_derived(self):
        """Test derived bankruptcy discharge years."""
        context = build_evaluation_context(
            application_id="app-123",
            guarantor={"has_bankruptcy": True},
            derived_features={"bankruptcy_discharge_years": 6.5},
        )

        assert context.bankruptcy_discharge_years == 6.5


class TestBuildContextNullHandling:
    """Tests for null/None value handling."""

    def test_null_credit_scores(self):
        """Test handling of null credit scores."""
        context = build_evaluation_context(
            application_id="app-123",
            guarantor={
                "fico_score": None,
                "transunion_score": None,
            },
        )

        assert context.fico_score is None
        assert context.transunion_score is None

    def test_null_business_data(self):
        """Test handling of null business data."""
        context = build_evaluation_context(
            application_id="app-123",
            business=None,
        )

        assert context.business_name == ""
        assert context.years_in_business == 0.0
        assert context.state == ""

    def test_empty_equipment_data(self):
        """Test handling of empty equipment data."""
        context = build_evaluation_context(
            application_id="app-123",
            equipment={},
        )

        assert context.equipment_category == ""
        assert context.equipment_year == 0
        assert context.equipment_age_years == 0


class TestEquipmentAgeCalculation:
    """Tests for automatic equipment age calculation."""

    def test_equipment_age_calculated(self):
        """Test equipment age is calculated from year."""
        current_year = datetime.now().year
        context = build_evaluation_context(
            application_id="app-123",
            equipment={"year": current_year - 5},
        )

        assert context.equipment_age_years == 5

    def test_new_equipment_age_zero(self):
        """Test new equipment has age of 0."""
        current_year = datetime.now().year
        context = build_evaluation_context(
            application_id="app-123",
            equipment={"year": current_year},
        )

        assert context.equipment_age_years == 0

    def test_missing_year_age_zero(self):
        """Test missing year results in age 0."""
        context = build_evaluation_context(
            application_id="app-123",
            equipment={"year": 0},
        )

        assert context.equipment_age_years == 0



class TestContextHelperMethods:
    """Tests for EvaluationContext helper methods."""

    def test_get_credit_score_fico(self):
        """Test getting FICO score."""
        context = build_evaluation_context(
            application_id="test",
            guarantor={"fico_score": 720},
        )

        assert context.get_credit_score("fico") == 720
        assert context.get_credit_score("FICO") == 720  # Case insensitive

    def test_get_credit_score_transunion(self):
        """Test getting TransUnion score."""
        context = build_evaluation_context(
            application_id="test",
            guarantor={"transunion_score": 710},
        )

        assert context.get_credit_score("transunion") == 710

    def test_get_credit_score_paynet(self):
        """Test getting PayNet score."""
        context = build_evaluation_context(
            application_id="test",
            business_credit={"paynet_score": 85},
        )

        assert context.get_credit_score("paynet") == 85

    def test_is_trucking_class_8(self):
        """Test trucking detection for Class 8."""
        context = build_evaluation_context(
            application_id="test",
            equipment={"category": "class_8_truck"},
        )

        assert context.is_trucking is True

    def test_is_trucking_construction(self):
        """Test trucking detection for non-trucking equipment."""
        context = build_evaluation_context(
            application_id="test",
            equipment={"category": "construction"},
        )

        assert context.is_trucking is False

    def test_is_startup_true(self):
        """Test startup detection for new business."""
        context = build_evaluation_context(
            application_id="test",
            business={"years_in_business": 1.5},
        )

        assert context.is_startup is True

    def test_is_startup_false(self):
        """Test startup detection for established business."""
        context = build_evaluation_context(
            application_id="test",
            business={"years_in_business": 5.0},
        )

        assert context.is_startup is False
