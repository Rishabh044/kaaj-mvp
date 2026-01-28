"""Unit tests for application validation step."""

import pytest

from app.core.hatchet import MockHatchetContext
from app.workflows.evaluation import validate_application


class TestValidateCompleteApplication:
    """Tests for validating complete applications."""

    @pytest.mark.asyncio
    async def test_validate_complete_application(self):
        """Test validation passes for complete application."""
        context = MockHatchetContext({
            "application_data": {
                "fico_score": 720,
                "state": "TX",
                "loan_amount": 5000000,
                "equipment_category": "construction",
            }
        })

        result = await validate_application(context)

        assert result["is_valid"] is True
        assert len(result["errors"]) == 0
        assert "validated_at" in result


class TestValidateMissingFicoScore:
    """Tests for missing FICO score."""

    @pytest.mark.asyncio
    async def test_validate_missing_fico_score(self):
        """Test validation fails when FICO score is missing."""
        context = MockHatchetContext({
            "application_data": {
                "state": "TX",
                "loan_amount": 5000000,
                "equipment_category": "construction",
            }
        })

        result = await validate_application(context)

        assert result["is_valid"] is False
        errors = result["errors"]
        assert any(e["field"] == "fico_score" for e in errors)


class TestValidateMissingState:
    """Tests for missing state."""

    @pytest.mark.asyncio
    async def test_validate_missing_state(self):
        """Test validation fails when state is missing."""
        context = MockHatchetContext({
            "application_data": {
                "fico_score": 720,
                "loan_amount": 5000000,
                "equipment_category": "construction",
            }
        })

        result = await validate_application(context)

        assert result["is_valid"] is False
        errors = result["errors"]
        assert any(e["field"] == "state" for e in errors)

    @pytest.mark.asyncio
    async def test_validate_empty_state(self):
        """Test validation fails when state is empty string."""
        context = MockHatchetContext({
            "application_data": {
                "fico_score": 720,
                "state": "",
                "loan_amount": 5000000,
                "equipment_category": "construction",
            }
        })

        result = await validate_application(context)

        assert result["is_valid"] is False


class TestValidateMissingLoanAmount:
    """Tests for missing loan amount."""

    @pytest.mark.asyncio
    async def test_validate_missing_loan_amount(self):
        """Test validation fails when loan amount is missing."""
        context = MockHatchetContext({
            "application_data": {
                "fico_score": 720,
                "state": "TX",
                "equipment_category": "construction",
            }
        })

        result = await validate_application(context)

        assert result["is_valid"] is False
        errors = result["errors"]
        assert any(e["field"] == "loan_amount" for e in errors)


class TestValidateMissingEquipmentCategory:
    """Tests for missing equipment category."""

    @pytest.mark.asyncio
    async def test_validate_missing_equipment_category(self):
        """Test validation fails when equipment category is missing."""
        context = MockHatchetContext({
            "application_data": {
                "fico_score": 720,
                "state": "TX",
                "loan_amount": 5000000,
            }
        })

        result = await validate_application(context)

        assert result["is_valid"] is False
        errors = result["errors"]
        assert any(e["field"] == "equipment_category" for e in errors)


class TestValidateMultipleErrors:
    """Tests for multiple validation errors."""

    @pytest.mark.asyncio
    async def test_validate_multiple_errors(self):
        """Test validation returns all errors when multiple fields missing."""
        context = MockHatchetContext({
            "application_data": {}
        })

        result = await validate_application(context)

        assert result["is_valid"] is False
        errors = result["errors"]
        # Should have errors for all required fields
        assert len(errors) == 4
        error_fields = {e["field"] for e in errors}
        assert error_fields == {"fico_score", "state", "loan_amount", "equipment_category"}


class TestValidateFicoRange:
    """Tests for FICO score range validation."""

    @pytest.mark.asyncio
    async def test_validate_fico_below_minimum(self):
        """Test validation fails when FICO is below 300."""
        context = MockHatchetContext({
            "application_data": {
                "fico_score": 200,
                "state": "TX",
                "loan_amount": 5000000,
                "equipment_category": "construction",
            }
        })

        result = await validate_application(context)

        assert result["is_valid"] is False
        errors = result["errors"]
        assert any("300" in e["message"] for e in errors)

    @pytest.mark.asyncio
    async def test_validate_fico_above_maximum(self):
        """Test validation fails when FICO is above 850."""
        context = MockHatchetContext({
            "application_data": {
                "fico_score": 900,
                "state": "TX",
                "loan_amount": 5000000,
                "equipment_category": "construction",
            }
        })

        result = await validate_application(context)

        assert result["is_valid"] is False
        errors = result["errors"]
        assert any("850" in e["message"] for e in errors)


class TestValidateLoanAmountRange:
    """Tests for loan amount validation."""

    @pytest.mark.asyncio
    async def test_validate_negative_loan_amount(self):
        """Test validation fails for negative loan amount."""
        context = MockHatchetContext({
            "application_data": {
                "fico_score": 720,
                "state": "TX",
                "loan_amount": -5000,
                "equipment_category": "construction",
            }
        })

        result = await validate_application(context)

        assert result["is_valid"] is False
        errors = result["errors"]
        assert any(e["field"] == "loan_amount" for e in errors)

    @pytest.mark.asyncio
    async def test_validate_zero_loan_amount(self):
        """Test validation fails for zero loan amount."""
        context = MockHatchetContext({
            "application_data": {
                "fico_score": 720,
                "state": "TX",
                "loan_amount": 0,
                "equipment_category": "construction",
            }
        })

        result = await validate_application(context)

        assert result["is_valid"] is False
