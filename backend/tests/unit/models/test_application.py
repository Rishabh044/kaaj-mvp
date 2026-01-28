"""Unit tests for LoanApplication model."""

import uuid
from datetime import datetime
from decimal import Decimal

import pytest

from app.models import Business, LoanApplication, PersonalGuarantor


class TestApplicationCreation:
    """Tests for creating LoanApplication instances."""

    def test_application_creation_with_required_fields(self):
        """Test creating an application with required fields."""
        app = LoanApplication(
            business_id=uuid.uuid4(),
            guarantor_id=uuid.uuid4(),
            loan_amount=10000000,  # $100,000 in cents
            transaction_type="purchase",
            equipment_category="class_8_truck",
            equipment_type="Sleeper Cab",
            equipment_year=2022,
            equipment_condition="used",
        )
        assert app.loan_amount == 10000000
        assert app.transaction_type == "purchase"
        assert app.equipment_category == "class_8_truck"
        assert app.status == "pending"
        assert app.is_private_party is False

    def test_application_creation_with_all_fields(self):
        """Test creating an application with all fields."""
        app = LoanApplication(
            business_id=uuid.uuid4(),
            guarantor_id=uuid.uuid4(),
            loan_amount=15000000,
            requested_term_months=60,
            down_payment_percent=Decimal("10.0"),
            transaction_type="refinance",
            is_private_party=True,
            equipment_category="trailer",
            equipment_type="Dry Van",
            equipment_make="Great Dane",
            equipment_model="Champion",
            equipment_year=2020,
            equipment_mileage=50000,
            equipment_condition="used",
        )
        assert app.requested_term_months == 60
        assert app.down_payment_percent == Decimal("10.0")
        assert app.is_private_party is True
        assert app.equipment_make == "Great Dane"


class TestApplicationNumberUniqueness:
    """Tests for application number generation."""

    def test_application_number_format(self):
        """Test that application number follows expected format."""
        from app.models.base import generate_application_number

        app_num = generate_application_number()
        assert app_num.startswith("APP-")
        # Should be like APP-20260128-ABC123
        parts = app_num.split("-")
        assert len(parts) == 3
        assert len(parts[1]) == 8  # Date part
        assert len(parts[2]) == 6  # Random part

    def test_application_numbers_are_unique(self):
        """Test that generated application numbers are unique."""
        from app.models.base import generate_application_number

        numbers = [generate_application_number() for _ in range(100)]
        assert len(set(numbers)) == 100  # All unique


class TestEquipmentAgeCalculation:
    """Tests for equipment age calculation."""

    def test_compute_equipment_age(self):
        """Test computing equipment age."""
        current_year = datetime.now().year
        app = LoanApplication(
            business_id=uuid.uuid4(),
            guarantor_id=uuid.uuid4(),
            loan_amount=10000000,
            transaction_type="purchase",
            equipment_category="class_8_truck",
            equipment_type="Day Cab",
            equipment_year=current_year - 5,
            equipment_condition="used",
        )
        assert app.compute_equipment_age() == 5

    def test_update_equipment_age(self):
        """Test updating equipment age field."""
        current_year = datetime.now().year
        app = LoanApplication(
            business_id=uuid.uuid4(),
            guarantor_id=uuid.uuid4(),
            loan_amount=10000000,
            transaction_type="purchase",
            equipment_category="class_8_truck",
            equipment_type="Day Cab",
            equipment_year=current_year - 3,
            equipment_condition="used",
        )
        app.update_equipment_age()
        assert app.equipment_age_years == 3

    def test_equipment_age_for_new_equipment(self):
        """Test equipment age for new (current year) equipment."""
        current_year = datetime.now().year
        app = LoanApplication(
            business_id=uuid.uuid4(),
            guarantor_id=uuid.uuid4(),
            loan_amount=20000000,
            transaction_type="purchase",
            equipment_category="class_8_truck",
            equipment_type="Sleeper",
            equipment_year=current_year,
            equipment_condition="new",
        )
        assert app.compute_equipment_age() == 0


class TestLoanAmountValidation:
    """Tests for loan amount handling."""

    def test_loan_amount_in_cents(self):
        """Test that loan amount is stored in cents."""
        app = LoanApplication(
            business_id=uuid.uuid4(),
            guarantor_id=uuid.uuid4(),
            loan_amount=15000000,  # $150,000
            transaction_type="purchase",
            equipment_category="class_8_truck",
            equipment_type="Truck",
            equipment_year=2022,
            equipment_condition="used",
        )
        assert app.loan_amount == 15000000

    def test_loan_amount_dollars_property(self):
        """Test loan_amount_dollars conversion property."""
        app = LoanApplication(
            business_id=uuid.uuid4(),
            guarantor_id=uuid.uuid4(),
            loan_amount=10050000,  # $100,500
            transaction_type="purchase",
            equipment_category="class_8_truck",
            equipment_type="Truck",
            equipment_year=2022,
            equipment_condition="used",
        )
        assert app.loan_amount_dollars == 100500.0


class TestStatusTransitions:
    """Tests for application status transitions."""

    def test_initial_status_is_pending(self):
        """Test that initial status is pending."""
        app = LoanApplication(
            business_id=uuid.uuid4(),
            guarantor_id=uuid.uuid4(),
            loan_amount=10000000,
            transaction_type="purchase",
            equipment_category="class_8_truck",
            equipment_type="Truck",
            equipment_year=2022,
            equipment_condition="used",
        )
        assert app.status == "pending"
        assert app.is_completed is False
        assert app.is_processing is False

    def test_mark_processing(self):
        """Test marking application as processing."""
        app = LoanApplication(
            business_id=uuid.uuid4(),
            guarantor_id=uuid.uuid4(),
            loan_amount=10000000,
            transaction_type="purchase",
            equipment_category="class_8_truck",
            equipment_type="Truck",
            equipment_year=2022,
            equipment_condition="used",
        )
        app.mark_processing()
        assert app.status == "processing"
        assert app.is_processing is True

    def test_mark_completed(self):
        """Test marking application as completed."""
        app = LoanApplication(
            business_id=uuid.uuid4(),
            guarantor_id=uuid.uuid4(),
            loan_amount=10000000,
            transaction_type="purchase",
            equipment_category="class_8_truck",
            equipment_type="Truck",
            equipment_year=2022,
            equipment_condition="used",
        )
        app.mark_completed()
        assert app.status == "completed"
        assert app.is_completed is True
        assert app.processed_at is not None

    def test_mark_error(self):
        """Test marking application as error."""
        app = LoanApplication(
            business_id=uuid.uuid4(),
            guarantor_id=uuid.uuid4(),
            loan_amount=10000000,
            transaction_type="purchase",
            equipment_category="class_8_truck",
            equipment_type="Truck",
            equipment_year=2022,
            equipment_condition="used",
        )
        app.mark_error()
        assert app.status == "error"
        assert app.processed_at is not None


class TestIsTrucking:
    """Tests for is_trucking property."""

    def test_is_trucking_true_for_class_8(self):
        """Test is_trucking for class 8 truck."""
        app = LoanApplication(
            business_id=uuid.uuid4(),
            guarantor_id=uuid.uuid4(),
            loan_amount=10000000,
            transaction_type="purchase",
            equipment_category="class_8_truck",
            equipment_type="Truck",
            equipment_year=2022,
            equipment_condition="used",
        )
        assert app.is_trucking is True

    def test_is_trucking_true_for_trailer(self):
        """Test is_trucking for trailer."""
        app = LoanApplication(
            business_id=uuid.uuid4(),
            guarantor_id=uuid.uuid4(),
            loan_amount=5000000,
            transaction_type="purchase",
            equipment_category="trailer",
            equipment_type="Dry Van",
            equipment_year=2020,
            equipment_condition="used",
        )
        assert app.is_trucking is True

    def test_is_trucking_false_for_construction(self):
        """Test is_trucking for construction equipment."""
        app = LoanApplication(
            business_id=uuid.uuid4(),
            guarantor_id=uuid.uuid4(),
            loan_amount=20000000,
            transaction_type="purchase",
            equipment_category="construction",
            equipment_type="Excavator",
            equipment_year=2021,
            equipment_condition="used",
        )
        assert app.is_trucking is False
