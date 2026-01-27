"""Unit tests for feature derivation step."""

import pytest
from datetime import datetime

from app.core.hatchet import MockHatchetContext
from app.workflows.evaluation import derive_features


class TestDeriveEquipmentAge:
    """Tests for equipment age derivation."""

    @pytest.mark.asyncio
    async def test_derive_equipment_age(self):
        """Test equipment age is calculated from year."""
        current_year = datetime.now().year
        context = MockHatchetContext({
            "application_data": {
                "equipment_year": current_year - 5,
            }
        })
        context.set_step_output("validate_application", {"is_valid": True})

        result = await derive_features(context)

        assert result["equipment_age_years"] == 5

    @pytest.mark.asyncio
    async def test_derive_equipment_age_new(self):
        """Test new equipment has age 0."""
        current_year = datetime.now().year
        context = MockHatchetContext({
            "application_data": {
                "equipment_year": current_year,
            }
        })
        context.set_step_output("validate_application", {"is_valid": True})

        result = await derive_features(context)

        assert result["equipment_age_years"] == 0

    @pytest.mark.asyncio
    async def test_derive_equipment_age_missing_year(self):
        """Test missing equipment year defaults to 0."""
        context = MockHatchetContext({
            "application_data": {}
        })
        context.set_step_output("validate_application", {"is_valid": True})

        result = await derive_features(context)

        assert result["equipment_age_years"] == 0


class TestDeriveBankruptcyDischargeYears:
    """Tests for bankruptcy discharge years derivation."""

    @pytest.mark.asyncio
    async def test_derive_years_in_business(self):
        """Test years in business is passed through."""
        context = MockHatchetContext({
            "application_data": {
                "years_in_business": 5.5,
            }
        })
        context.set_step_output("validate_application", {"is_valid": True})

        result = await derive_features(context)

        assert result["years_in_business"] == 5.5


class TestDeriveIsStartup:
    """Tests for startup detection."""

    @pytest.mark.asyncio
    async def test_derive_is_startup_true(self):
        """Test business under 2 years is startup."""
        context = MockHatchetContext({
            "application_data": {
                "years_in_business": 1.5,
            }
        })
        context.set_step_output("validate_application", {"is_valid": True})

        result = await derive_features(context)

        assert result["is_startup"] is True

    @pytest.mark.asyncio
    async def test_derive_is_startup_false(self):
        """Test business over 2 years is not startup."""
        context = MockHatchetContext({
            "application_data": {
                "years_in_business": 5.0,
            }
        })
        context.set_step_output("validate_application", {"is_valid": True})

        result = await derive_features(context)

        assert result["is_startup"] is False


class TestDeriveIsTrucking:
    """Tests for trucking detection."""

    @pytest.mark.asyncio
    async def test_derive_is_trucking_class_8(self):
        """Test class_8_truck is trucking."""
        context = MockHatchetContext({
            "application_data": {
                "equipment_category": "class_8_truck",
            }
        })
        context.set_step_output("validate_application", {"is_valid": True})

        result = await derive_features(context)

        assert result["is_trucking"] is True

    @pytest.mark.asyncio
    async def test_derive_is_trucking_trailer(self):
        """Test trailer is trucking."""
        context = MockHatchetContext({
            "application_data": {
                "equipment_category": "trailer",
            }
        })
        context.set_step_output("validate_application", {"is_valid": True})

        result = await derive_features(context)

        assert result["is_trucking"] is True

    @pytest.mark.asyncio
    async def test_derive_is_trucking_construction(self):
        """Test construction is not trucking."""
        context = MockHatchetContext({
            "application_data": {
                "equipment_category": "construction",
            }
        })
        context.set_step_output("validate_application", {"is_valid": True})

        result = await derive_features(context)

        assert result["is_trucking"] is False


class TestDeriveSkipsOnValidationFailure:
    """Tests for skipping when validation fails."""

    @pytest.mark.asyncio
    async def test_derive_skips_on_validation_failure(self):
        """Test derivation is skipped when validation fails."""
        context = MockHatchetContext({
            "application_data": {}
        })
        context.set_step_output("validate_application", {"is_valid": False})

        result = await derive_features(context)

        assert result["skipped"] is True
        assert "reason" in result
