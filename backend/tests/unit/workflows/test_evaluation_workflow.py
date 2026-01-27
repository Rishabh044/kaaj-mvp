"""Unit tests for the complete evaluation workflow."""

import pytest
from pathlib import Path

from app.core.hatchet import MockHatchetContext
from app.workflows.evaluation import ApplicationEvaluationWorkflow


LENDERS_DIR = Path(__file__).parent.parent.parent.parent / "app" / "policies" / "lenders"


class TestEvaluationWorkflowComplete:
    """Tests for the complete evaluation workflow."""

    @pytest.mark.asyncio
    async def test_full_workflow_success(self):
        """Test complete workflow with valid application."""
        from app.policies.loader import PolicyLoader

        policy_loader = PolicyLoader(LENDERS_DIR)
        workflow = ApplicationEvaluationWorkflow(policy_loader=policy_loader)

        application_data = {
            "application_id": "test-123",
            "fico_score": 720,
            "state": "TX",
            "loan_amount": 5000000,
            "equipment_category": "construction",
            "equipment_year": 2022,
            "years_in_business": 5.0,
            "guarantor": {
                "fico_score": 720,
                "is_homeowner": True,
            },
        }

        result = await workflow.run(application_data)

        assert result["status"] == "completed"
        assert "total_evaluated" in result
        assert "ranked_matches" in result

    @pytest.mark.asyncio
    async def test_workflow_validation_failure(self):
        """Test workflow with invalid application."""
        workflow = ApplicationEvaluationWorkflow()

        application_data = {
            # Missing required fields
        }

        result = await workflow.run(application_data)

        assert result["status"] == "validation_failed"
        assert "errors" in result
        assert len(result["errors"]) > 0


class TestEvaluateAllLenders:
    """Tests for the evaluate all lenders step."""

    @pytest.mark.asyncio
    async def test_evaluate_returns_all_lenders(self):
        """Test evaluation returns results for all lenders."""
        from app.policies.loader import PolicyLoader

        policy_loader = PolicyLoader(LENDERS_DIR)
        workflow = ApplicationEvaluationWorkflow(policy_loader=policy_loader)

        context = MockHatchetContext({
            "application_data": {
                "application_id": "test-123",
                "fico_score": 720,
                "state": "TX",
                "loan_amount": 5000000,
                "equipment_category": "construction",
                "equipment_year": 2022,
                "guarantor": {
                    "fico_score": 720,
                    "is_homeowner": True,
                },
            }
        })
        context.set_step_output("validate_application", {"is_valid": True})
        context.set_step_output("derive_features", {
            "equipment_age_years": 3,
            "years_in_business": 5.0,
            "is_startup": False,
            "is_trucking": False,
        })

        result = await workflow.evaluate_all_lenders(context)

        assert result["total_evaluated"] == 5
        assert "matches" in result
        assert len(result["matches"]) == 5

    @pytest.mark.asyncio
    async def test_evaluate_skips_on_derive_failure(self):
        """Test evaluation is skipped when derivation was skipped."""
        workflow = ApplicationEvaluationWorkflow()

        context = MockHatchetContext({
            "application_data": {}
        })
        context.set_step_output("validate_application", {"is_valid": False})
        context.set_step_output("derive_features", {"skipped": True, "reason": "Validation failed"})

        result = await workflow.evaluate_all_lenders(context)

        assert result["skipped"] is True


class TestPersistAndRankResults:
    """Tests for the persist and rank step."""

    @pytest.mark.asyncio
    async def test_rank_eligible_lenders(self):
        """Test eligible lenders are ranked by score."""
        workflow = ApplicationEvaluationWorkflow()

        context = MockHatchetContext({})
        context.set_step_output("evaluate_all_lenders", {
            "total_evaluated": 3,
            "total_eligible": 2,
            "matches": [
                {"lender_id": "a", "is_eligible": True, "fit_score": 80},
                {"lender_id": "b", "is_eligible": True, "fit_score": 90},
                {"lender_id": "c", "is_eligible": False, "fit_score": 0},
            ],
        })

        result = await workflow.persist_and_rank_results(context)

        assert result["status"] == "completed"
        ranked = result["ranked_matches"]

        # First two should be eligible, sorted by score
        assert ranked[0]["lender_id"] == "b"  # Higher score first
        assert ranked[0]["rank"] == 1
        assert ranked[1]["lender_id"] == "a"
        assert ranked[1]["rank"] == 2

        # Ineligible should have no rank
        assert ranked[2]["lender_id"] == "c"
        assert ranked[2]["rank"] is None

    @pytest.mark.asyncio
    async def test_rank_no_eligible_lenders(self):
        """Test handling when no lenders are eligible."""
        workflow = ApplicationEvaluationWorkflow()

        context = MockHatchetContext({})
        context.set_step_output("evaluate_all_lenders", {
            "total_evaluated": 2,
            "total_eligible": 0,
            "matches": [
                {"lender_id": "a", "is_eligible": False, "fit_score": 0},
                {"lender_id": "b", "is_eligible": False, "fit_score": 0},
            ],
        })

        result = await workflow.persist_and_rank_results(context)

        assert result["status"] == "completed"
        ranked = result["ranked_matches"]

        # All ineligible, no ranks
        for match in ranked:
            assert match["rank"] is None

    @pytest.mark.asyncio
    async def test_skips_on_evaluation_failure(self):
        """Test persist is skipped when evaluation was skipped."""
        workflow = ApplicationEvaluationWorkflow()

        context = MockHatchetContext({})
        context.set_step_output("evaluate_all_lenders", {"skipped": True, "reason": "Derivation skipped"})

        result = await workflow.persist_and_rank_results(context)

        assert result["status"] == "skipped"
