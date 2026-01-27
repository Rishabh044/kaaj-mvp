"""Unit tests for application schemas."""

from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.schemas import (
    BusinessCreate,
    EquipmentInput,
    GuarantorCreate,
    LoanApplicationInput,
)


class TestLoanApplicationInputValidation:
    """Tests for LoanApplicationInput validation."""

    def test_valid_application_input(self):
        """Test valid application input passes validation."""
        input_data = LoanApplicationInput(
            business=BusinessCreate(
                legal_name="Test Trucking LLC",
                entity_type="LLC",
                industry_code="484121",
                industry_name="Trucking",
                state="TX",
                city="Houston",
                zip_code="77001",
                years_in_business=Decimal("5.0"),
            ),
            guarantor=GuarantorCreate(
                first_name="John",
                last_name="Doe",
                fico_score=720,
                is_homeowner=True,
            ),
            loan_amount=10000000,
            transaction_type="purchase",
            equipment=EquipmentInput(
                category="class_8_truck",
                type="Sleeper Cab",
                year=2022,
                condition="used",
            ),
        )
        assert input_data.loan_amount == 10000000
        assert input_data.transaction_type == "purchase"


class TestRequiredFieldsValidation:
    """Tests for required fields validation."""

    def test_missing_loan_amount_raises(self):
        """Test that missing loan_amount raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            LoanApplicationInput(
                business=BusinessCreate(
                    legal_name="Test",
                    entity_type="LLC",
                    industry_code="484121",
                    industry_name="Trucking",
                    state="TX",
                    city="Houston",
                    zip_code="77001",
                    years_in_business=Decimal("5.0"),
                ),
                guarantor=GuarantorCreate(
                    first_name="John",
                    last_name="Doe",
                ),
                # loan_amount missing
                transaction_type="purchase",
                equipment=EquipmentInput(
                    category="class_8_truck",
                    type="Truck",
                    year=2022,
                    condition="used",
                ),
            )
        assert "loan_amount" in str(exc_info.value)

    def test_missing_equipment_raises(self):
        """Test that missing equipment raises ValidationError."""
        with pytest.raises(ValidationError):
            LoanApplicationInput(
                business=BusinessCreate(
                    legal_name="Test",
                    entity_type="LLC",
                    industry_code="484121",
                    industry_name="Trucking",
                    state="TX",
                    city="Houston",
                    zip_code="77001",
                    years_in_business=Decimal("5.0"),
                ),
                guarantor=GuarantorCreate(
                    first_name="John",
                    last_name="Doe",
                ),
                loan_amount=10000000,
                transaction_type="purchase",
                # equipment missing
            )


class TestEquipmentCategoryValidation:
    """Tests for equipment category validation."""

    def test_valid_equipment_category(self):
        """Test valid equipment category."""
        equipment = EquipmentInput(
            category="class_8_truck",
            type="Sleeper",
            year=2022,
            condition="used",
        )
        assert equipment.category == "class_8_truck"

    def test_equipment_with_mileage(self):
        """Test equipment with mileage (for trucks)."""
        equipment = EquipmentInput(
            category="class_8_truck",
            type="Sleeper",
            year=2020,
            mileage=250000,
            condition="used",
        )
        assert equipment.mileage == 250000

    def test_equipment_with_hours(self):
        """Test equipment with hours (for construction)."""
        equipment = EquipmentInput(
            category="construction",
            type="Excavator",
            year=2019,
            hours=5000,
            condition="used",
        )
        assert equipment.hours == 5000


class TestTransactionTypeValidation:
    """Tests for transaction type validation."""

    def test_valid_transaction_type_purchase(self):
        """Test valid purchase transaction type."""
        input_data = LoanApplicationInput(
            business=BusinessCreate(
                legal_name="Test",
                entity_type="LLC",
                industry_code="484121",
                industry_name="Trucking",
                state="TX",
                city="Houston",
                zip_code="77001",
                years_in_business=Decimal("5.0"),
            ),
            guarantor=GuarantorCreate(first_name="John", last_name="Doe"),
            loan_amount=10000000,
            transaction_type="purchase",
            equipment=EquipmentInput(
                category="class_8_truck",
                type="Truck",
                year=2022,
                condition="used",
            ),
        )
        assert input_data.transaction_type == "purchase"

    def test_valid_transaction_type_refinance(self):
        """Test valid refinance transaction type."""
        input_data = LoanApplicationInput(
            business=BusinessCreate(
                legal_name="Test",
                entity_type="LLC",
                industry_code="484121",
                industry_name="Trucking",
                state="TX",
                city="Houston",
                zip_code="77001",
                years_in_business=Decimal("5.0"),
            ),
            guarantor=GuarantorCreate(first_name="John", last_name="Doe"),
            loan_amount=10000000,
            transaction_type="refinance",
            equipment=EquipmentInput(
                category="class_8_truck",
                type="Truck",
                year=2022,
                condition="used",
            ),
        )
        assert input_data.transaction_type == "refinance"

    def test_invalid_transaction_type_raises(self):
        """Test invalid transaction type raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            LoanApplicationInput(
                business=BusinessCreate(
                    legal_name="Test",
                    entity_type="LLC",
                    industry_code="484121",
                    industry_name="Trucking",
                    state="TX",
                    city="Houston",
                    zip_code="77001",
                    years_in_business=Decimal("5.0"),
                ),
                guarantor=GuarantorCreate(first_name="John", last_name="Doe"),
                loan_amount=10000000,
                transaction_type="invalid_type",
                equipment=EquipmentInput(
                    category="class_8_truck",
                    type="Truck",
                    year=2022,
                    condition="used",
                ),
            )
        assert "transaction_type" in str(exc_info.value).lower()


class TestEquipmentConditionValidation:
    """Tests for equipment condition validation."""

    def test_valid_condition_new(self):
        """Test valid 'new' condition."""
        equipment = EquipmentInput(
            category="class_8_truck",
            type="Sleeper",
            year=2025,
            condition="new",
        )
        assert equipment.condition == "new"

    def test_valid_condition_used(self):
        """Test valid 'used' condition."""
        equipment = EquipmentInput(
            category="class_8_truck",
            type="Sleeper",
            year=2022,
            condition="used",
        )
        assert equipment.condition == "used"

    def test_valid_condition_certified(self):
        """Test valid 'certified' condition."""
        equipment = EquipmentInput(
            category="class_8_truck",
            type="Sleeper",
            year=2023,
            condition="certified",
        )
        assert equipment.condition == "certified"

    def test_invalid_condition_raises(self):
        """Test invalid condition raises ValidationError."""
        with pytest.raises(ValidationError):
            EquipmentInput(
                category="class_8_truck",
                type="Sleeper",
                year=2022,
                condition="broken",
            )
