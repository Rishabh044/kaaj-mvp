"""Unit tests for Business model."""

from decimal import Decimal

import pytest

from app.models import Business


class TestBusinessCreation:
    """Tests for creating Business instances."""

    def test_business_creation_with_required_fields(self):
        """Test creating a business with only required fields."""
        business = Business(
            legal_name="Acme Trucking LLC",
            entity_type="LLC",
            industry_code="484121",
            industry_name="General Freight Trucking, Long-Distance",
            state="TX",
            city="Houston",
            zip_code="77001",
            years_in_business=Decimal("5.5"),
        )
        assert business.legal_name == "Acme Trucking LLC"
        assert business.entity_type == "LLC"
        assert business.state == "TX"
        assert business.years_in_business == Decimal("5.5")
        assert business.dba_name is None
        assert business.annual_revenue is None

    def test_business_creation_with_all_fields(self):
        """Test creating a business with all fields."""
        business = Business(
            legal_name="Big Rig Transport Inc",
            dba_name="BRT",
            entity_type="Corporation",
            industry_code="484121",
            industry_name="General Freight Trucking, Long-Distance",
            state="CA",
            city="Los Angeles",
            zip_code="90001",
            years_in_business=Decimal("10.0"),
            annual_revenue=5000000,
            employee_count=50,
            fleet_size=25,
        )
        assert business.dba_name == "BRT"
        assert business.annual_revenue == 5000000
        assert business.employee_count == 50
        assert business.fleet_size == 25


class TestBusinessYearsInBusinessValidation:
    """Tests for years_in_business field validation."""

    def test_years_in_business_decimal_precision(self):
        """Test that years_in_business handles decimal precision."""
        business = Business(
            legal_name="Test Co",
            entity_type="LLC",
            industry_code="484121",
            industry_name="Trucking",
            state="TX",
            city="Dallas",
            zip_code="75001",
            years_in_business=Decimal("2.5"),
        )
        assert business.years_in_business == Decimal("2.5")

    def test_years_in_business_zero(self):
        """Test that zero years is valid for startups."""
        business = Business(
            legal_name="New Startup LLC",
            entity_type="LLC",
            industry_code="484121",
            industry_name="Trucking",
            state="TX",
            city="Austin",
            zip_code="78701",
            years_in_business=Decimal("0.0"),
        )
        assert business.years_in_business == Decimal("0.0")


class TestBusinessStateCodeValidation:
    """Tests for state code validation."""

    def test_state_code_valid(self):
        """Test valid state code."""
        business = Business(
            legal_name="Test Co",
            entity_type="LLC",
            industry_code="484121",
            industry_name="Trucking",
            state="TX",
            city="Houston",
            zip_code="77001",
            years_in_business=Decimal("5.0"),
        )
        assert business.state == "TX"

    def test_state_code_uppercase(self):
        """Test that state code is stored as provided."""
        business = Business(
            legal_name="Test Co",
            entity_type="LLC",
            industry_code="484121",
            industry_name="Trucking",
            state="CA",
            city="San Francisco",
            zip_code="94102",
            years_in_business=Decimal("3.0"),
        )
        assert business.state == "CA"


class TestBusinessIsStartup:
    """Tests for the is_startup property."""

    def test_is_startup_true_for_new_business(self):
        """Test that business with less than 2 years is a startup."""
        business = Business(
            legal_name="New Company",
            entity_type="LLC",
            industry_code="484121",
            industry_name="Trucking",
            state="TX",
            city="Dallas",
            zip_code="75001",
            years_in_business=Decimal("1.5"),
        )
        assert business.is_startup is True

    def test_is_startup_false_for_established_business(self):
        """Test that business with 2+ years is not a startup."""
        business = Business(
            legal_name="Established Corp",
            entity_type="Corporation",
            industry_code="484121",
            industry_name="Trucking",
            state="TX",
            city="Houston",
            zip_code="77001",
            years_in_business=Decimal("5.0"),
        )
        assert business.is_startup is False

    def test_is_startup_boundary_at_2_years(self):
        """Test that exactly 2 years is not a startup."""
        business = Business(
            legal_name="Two Year Company",
            entity_type="LLC",
            industry_code="484121",
            industry_name="Trucking",
            state="TX",
            city="Austin",
            zip_code="78701",
            years_in_business=Decimal("2.0"),
        )
        assert business.is_startup is False


class TestBusinessRepr:
    """Tests for Business __repr__."""

    def test_repr_format(self):
        """Test that __repr__ returns expected format."""
        business = Business(
            legal_name="Test Trucking",
            entity_type="LLC",
            industry_code="484121",
            industry_name="Trucking",
            state="TX",
            city="Houston",
            zip_code="77001",
            years_in_business=Decimal("5.0"),
        )
        repr_str = repr(business)
        assert "Business" in repr_str
        assert "Test Trucking" in repr_str
        assert "TX" in repr_str
