"""Unit tests for PersonalGuarantor model."""

from datetime import date, timedelta

import pytest

from app.models import PersonalGuarantor


class TestGuarantorCreation:
    """Tests for creating PersonalGuarantor instances."""

    def test_guarantor_creation_with_required_fields(self):
        """Test creating a guarantor with only required fields."""
        guarantor = PersonalGuarantor(
            first_name="John",
            last_name="Doe",
        )
        assert guarantor.first_name == "John"
        assert guarantor.last_name == "Doe"
        assert guarantor.is_homeowner is False
        assert guarantor.is_us_citizen is True
        assert guarantor.fico_score is None

    def test_guarantor_creation_with_all_fields(self):
        """Test creating a guarantor with all fields."""
        guarantor = PersonalGuarantor(
            first_name="Jane",
            last_name="Smith",
            ssn_last_four="1234",
            email="jane@example.com",
            phone="555-123-4567",
            fico_score=750,
            transunion_score=745,
            experian_score=760,
            equifax_score=755,
            is_homeowner=True,
            is_us_citizen=True,
            has_cdl=True,
            cdl_years=10,
            industry_experience_years=15,
        )
        assert guarantor.fico_score == 750
        assert guarantor.is_homeowner is True
        assert guarantor.has_cdl is True
        assert guarantor.cdl_years == 10


class TestCreditScoreRangeValidation:
    """Tests for credit score ranges."""

    def test_fico_score_valid_range(self):
        """Test FICO score in valid range."""
        guarantor = PersonalGuarantor(
            first_name="Test",
            last_name="User",
            fico_score=720,
        )
        assert guarantor.fico_score == 720

    def test_fico_score_minimum(self):
        """Test FICO score at minimum."""
        guarantor = PersonalGuarantor(
            first_name="Test",
            last_name="User",
            fico_score=300,
        )
        assert guarantor.fico_score == 300

    def test_fico_score_maximum(self):
        """Test FICO score at maximum."""
        guarantor = PersonalGuarantor(
            first_name="Test",
            last_name="User",
            fico_score=850,
        )
        assert guarantor.fico_score == 850

    def test_all_credit_scores_can_be_set(self):
        """Test that all credit score types can be set."""
        guarantor = PersonalGuarantor(
            first_name="Test",
            last_name="User",
            fico_score=720,
            transunion_score=715,
            experian_score=725,
            equifax_score=710,
        )
        assert guarantor.fico_score == 720
        assert guarantor.transunion_score == 715
        assert guarantor.experian_score == 725
        assert guarantor.equifax_score == 710


class TestBankruptcyDateLogic:
    """Tests for bankruptcy discharge date logic."""

    def test_bankruptcy_discharge_years_calculation(self):
        """Test bankruptcy discharge years property."""
        discharge_date = date.today() - timedelta(days=365 * 3)  # 3 years ago
        guarantor = PersonalGuarantor(
            first_name="Test",
            last_name="User",
            has_bankruptcy=True,
            bankruptcy_discharge_date=discharge_date,
            bankruptcy_chapter="7",
        )
        # Should be approximately 3 years
        assert guarantor.bankruptcy_discharge_years is not None
        assert 2.9 < guarantor.bankruptcy_discharge_years < 3.1

    def test_bankruptcy_discharge_years_none_when_no_bankruptcy(self):
        """Test that discharge years is None when no bankruptcy."""
        guarantor = PersonalGuarantor(
            first_name="Test",
            last_name="User",
            has_bankruptcy=False,
        )
        assert guarantor.bankruptcy_discharge_years is None

    def test_bankruptcy_discharge_years_none_when_no_date(self):
        """Test that discharge years is None when no discharge date."""
        guarantor = PersonalGuarantor(
            first_name="Test",
            last_name="User",
            has_bankruptcy=True,
            bankruptcy_chapter="7",
            # No discharge date - active bankruptcy
        )
        assert guarantor.bankruptcy_discharge_years is None


class TestCreditHistoryFlags:
    """Tests for credit history flag combinations."""

    def test_clean_credit_history(self):
        """Test guarantor with clean credit history."""
        guarantor = PersonalGuarantor(
            first_name="Clean",
            last_name="Credit",
            has_bankruptcy=False,
            has_open_judgements=False,
            has_foreclosure=False,
            has_repossession=False,
            has_tax_liens=False,
        )
        assert guarantor.has_bankruptcy is False
        assert guarantor.has_open_judgements is False
        assert guarantor.has_foreclosure is False
        assert guarantor.has_repossession is False
        assert guarantor.has_tax_liens is False

    def test_credit_history_with_issues(self):
        """Test guarantor with credit issues."""
        guarantor = PersonalGuarantor(
            first_name="Issues",
            last_name="Credit",
            has_bankruptcy=True,
            bankruptcy_chapter="7",
            bankruptcy_discharge_date=date.today() - timedelta(days=365 * 5),
            has_open_judgements=True,
            judgement_amount=5000,
            has_tax_liens=True,
            tax_lien_amount=10000,
        )
        assert guarantor.has_bankruptcy is True
        assert guarantor.judgement_amount == 5000
        assert guarantor.tax_lien_amount == 10000


class TestGetCreditScore:
    """Tests for get_credit_score method."""

    def test_get_fico_score(self):
        """Test getting FICO score."""
        guarantor = PersonalGuarantor(
            first_name="Test",
            last_name="User",
            fico_score=720,
        )
        assert guarantor.get_credit_score("fico") == 720
        assert guarantor.get_credit_score("FICO") == 720

    def test_get_transunion_score(self):
        """Test getting TransUnion score."""
        guarantor = PersonalGuarantor(
            first_name="Test",
            last_name="User",
            transunion_score=715,
        )
        assert guarantor.get_credit_score("transunion") == 715

    def test_get_missing_score_returns_none(self):
        """Test that missing score returns None."""
        guarantor = PersonalGuarantor(
            first_name="Test",
            last_name="User",
        )
        assert guarantor.get_credit_score("fico") is None

    def test_get_invalid_score_type_returns_none(self):
        """Test that invalid score type returns None."""
        guarantor = PersonalGuarantor(
            first_name="Test",
            last_name="User",
            fico_score=720,
        )
        assert guarantor.get_credit_score("invalid") is None


class TestFullName:
    """Tests for full_name property."""

    def test_full_name(self):
        """Test full name property."""
        guarantor = PersonalGuarantor(
            first_name="John",
            last_name="Doe",
        )
        assert guarantor.full_name == "John Doe"
