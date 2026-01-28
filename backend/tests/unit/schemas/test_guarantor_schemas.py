"""Unit tests for guarantor schemas."""

from datetime import date, timedelta

import pytest
from pydantic import ValidationError

from app.schemas import GuarantorCreate


class TestCreditScoreBounds:
    """Tests for credit score range validation."""

    def test_fico_score_at_minimum(self):
        """Test FICO score at minimum (300)."""
        guarantor = GuarantorCreate(
            first_name="Test",
            last_name="User",
            fico_score=300,
        )
        assert guarantor.fico_score == 300

    def test_fico_score_at_maximum(self):
        """Test FICO score at maximum (850)."""
        guarantor = GuarantorCreate(
            first_name="Test",
            last_name="User",
            fico_score=850,
        )
        assert guarantor.fico_score == 850

    def test_fico_score_below_minimum_raises(self):
        """Test FICO score below minimum raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            GuarantorCreate(
                first_name="Test",
                last_name="User",
                fico_score=299,
            )
        assert "fico_score" in str(exc_info.value).lower()

    def test_fico_score_above_maximum_raises(self):
        """Test FICO score above maximum raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            GuarantorCreate(
                first_name="Test",
                last_name="User",
                fico_score=851,
            )
        assert "fico_score" in str(exc_info.value).lower()

    def test_all_credit_scores_valid_range(self):
        """Test all credit scores accept valid range."""
        guarantor = GuarantorCreate(
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


class TestBankruptcyConditionalFields:
    """Tests for bankruptcy conditional field validation."""

    def test_bankruptcy_with_all_fields(self):
        """Test bankruptcy with all related fields."""
        discharge_date = date.today() - timedelta(days=365 * 3)
        guarantor = GuarantorCreate(
            first_name="Test",
            last_name="User",
            has_bankruptcy=True,
            bankruptcy_discharge_date=discharge_date,
            bankruptcy_chapter="7",
        )
        assert guarantor.has_bankruptcy is True
        assert guarantor.bankruptcy_discharge_date == discharge_date
        assert guarantor.bankruptcy_chapter == "7"

    def test_no_bankruptcy_clears_related_fields(self):
        """Test that no bankruptcy clears related fields."""
        guarantor = GuarantorCreate(
            first_name="Test",
            last_name="User",
            has_bankruptcy=False,
            bankruptcy_discharge_date=date.today(),  # Should be cleared
            bankruptcy_chapter="7",  # Should be cleared
        )
        assert guarantor.has_bankruptcy is False
        assert guarantor.bankruptcy_discharge_date is None
        assert guarantor.bankruptcy_chapter is None

    def test_valid_bankruptcy_chapters(self):
        """Test valid bankruptcy chapters."""
        for chapter in ["7", "11", "13"]:
            guarantor = GuarantorCreate(
                first_name="Test",
                last_name="User",
                has_bankruptcy=True,
                bankruptcy_chapter=chapter,
            )
            assert guarantor.bankruptcy_chapter == chapter


class TestJudgementConditionalFields:
    """Tests for judgement conditional field validation."""

    def test_judgement_with_amount(self):
        """Test judgement with amount."""
        guarantor = GuarantorCreate(
            first_name="Test",
            last_name="User",
            has_open_judgements=True,
            judgement_amount=5000,
        )
        assert guarantor.has_open_judgements is True
        assert guarantor.judgement_amount == 5000

    def test_no_judgement_clears_amount(self):
        """Test that no judgement clears amount."""
        guarantor = GuarantorCreate(
            first_name="Test",
            last_name="User",
            has_open_judgements=False,
            judgement_amount=5000,  # Should be cleared
        )
        assert guarantor.has_open_judgements is False
        assert guarantor.judgement_amount is None


class TestTaxLienConditionalFields:
    """Tests for tax lien conditional field validation."""

    def test_tax_lien_with_amount(self):
        """Test tax lien with amount."""
        guarantor = GuarantorCreate(
            first_name="Test",
            last_name="User",
            has_tax_liens=True,
            tax_lien_amount=10000,
        )
        assert guarantor.has_tax_liens is True
        assert guarantor.tax_lien_amount == 10000

    def test_no_tax_lien_clears_amount(self):
        """Test that no tax lien clears amount."""
        guarantor = GuarantorCreate(
            first_name="Test",
            last_name="User",
            has_tax_liens=False,
            tax_lien_amount=10000,  # Should be cleared
        )
        assert guarantor.has_tax_liens is False
        assert guarantor.tax_lien_amount is None


class TestSSNValidation:
    """Tests for SSN last four validation."""

    def test_valid_ssn_last_four(self):
        """Test valid SSN last four digits."""
        guarantor = GuarantorCreate(
            first_name="Test",
            last_name="User",
            ssn_last_four="1234",
        )
        assert guarantor.ssn_last_four == "1234"

    def test_ssn_too_short_raises(self):
        """Test SSN too short raises ValidationError."""
        with pytest.raises(ValidationError):
            GuarantorCreate(
                first_name="Test",
                last_name="User",
                ssn_last_four="123",
            )

    def test_ssn_too_long_raises(self):
        """Test SSN too long raises ValidationError."""
        with pytest.raises(ValidationError):
            GuarantorCreate(
                first_name="Test",
                last_name="User",
                ssn_last_four="12345",
            )

    def test_ssn_non_numeric_raises(self):
        """Test SSN with non-numeric characters raises ValidationError."""
        with pytest.raises(ValidationError):
            GuarantorCreate(
                first_name="Test",
                last_name="User",
                ssn_last_four="12ab",
            )
