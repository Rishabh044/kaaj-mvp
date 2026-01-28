"""Application evaluation workflow for processing loan applications.

This workflow orchestrates the evaluation of a loan application against
all lender policies, with steps for validation, feature derivation,
lender evaluation, and result ranking.
"""

import logging
from datetime import datetime
from typing import Optional
from uuid import UUID

from app.core.database import async_session_factory
from app.core.hatchet import MockHatchetContext, get_hatchet
from app.policies.loader import PolicyLoader
from app.rules.context_builder import build_evaluation_context
from app.services.application_db_manager import ApplicationDBManager
from app.services.matching_service import LenderMatchingService

logger = logging.getLogger(__name__)

# Get Hatchet client
hatchet = get_hatchet()


class ValidationError(Exception):
    """Raised when application validation fails."""

    def __init__(self, field: str, message: str):
        self.field = field
        self.message = message
        super().__init__(f"Validation error on '{field}': {message}")


class ApplicationEvaluationWorkflow:
    """Workflow for evaluating loan applications against lender policies.

    This workflow consists of 4 steps:
    1. validate_application - Validate required fields
    2. derive_features - Compute derived features (equipment age, etc.)
    3. evaluate_all_lenders - Evaluate against all lender policies
    4. rank_results - Compute final rankings
    """

    def __init__(
        self,
        matching_service: Optional[LenderMatchingService] = None,
        policy_loader: Optional[PolicyLoader] = None,
    ):
        """Initialize the workflow.

        Args:
            matching_service: Service for lender matching. Created if not provided.
            policy_loader: Loader for lender policies. Created if not provided.
        """
        self.policy_loader = policy_loader or PolicyLoader()
        self.matching_service = matching_service or LenderMatchingService(
            policy_loader=self.policy_loader
        )

    async def run(self, application_data: dict) -> dict:
        """Run the complete evaluation workflow.

        This is the main entry point for synchronous execution without Hatchet.

        Args:
            application_data: The loan application data.

        Returns:
            Workflow result with matching results and status.
        """
        context = MockHatchetContext({"application_data": application_data})

        # Step 1: Validate
        validation_result = await self.validate_application(context)
        context.set_step_output("validate_application", validation_result)

        if not validation_result.get("is_valid"):
            return {
                "status": "validation_failed",
                "errors": validation_result.get("errors", []),
            }

        # Step 2: Derive features
        features_result = await self.derive_features(context)
        context.set_step_output("derive_features", features_result)

        # Step 3: Evaluate lenders
        evaluation_result = await self.evaluate_all_lenders(context)
        context.set_step_output("evaluate_all_lenders", evaluation_result)

        # Step 4: Rank results
        final_result = await self.rank_results(context)

        return final_result

    async def validate_application(self, context) -> dict:
        """Step 1: Validate the application has all required fields.

        Args:
            context: Hatchet workflow context.

        Returns:
            Validation result with is_valid flag and any errors.
        """
        input_data = context.workflow_input()
        application_data = input_data.get("application_data", {})

        errors = []

        # Required fields
        required_fields = [
            ("fico_score", "FICO score is required"),
            ("state", "State is required"),
            ("loan_amount", "Loan amount is required"),
            ("equipment_category", "Equipment category is required"),
        ]

        for field, message in required_fields:
            value = application_data.get(field)
            if value is None or (isinstance(value, str) and not value.strip()):
                errors.append({"field": field, "message": message})

        # FICO score range validation
        fico_score = application_data.get("fico_score")
        if fico_score is not None:
            if not isinstance(fico_score, int) or fico_score < 300 or fico_score > 850:
                errors.append(
                    {
                        "field": "fico_score",
                        "message": "FICO score must be between 300 and 850",
                    }
                )

        # Loan amount validation
        loan_amount = application_data.get("loan_amount")
        if loan_amount is not None:
            if not isinstance(loan_amount, int) or loan_amount <= 0:
                errors.append(
                    {
                        "field": "loan_amount",
                        "message": "Loan amount must be a positive integer",
                    }
                )

        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "validated_at": datetime.utcnow().isoformat(),
        }

    async def derive_features(self, context) -> dict:
        """Step 2: Compute derived features from application data.

        Args:
            context: Hatchet workflow context.

        Returns:
            Dictionary of derived features.
        """
        validation_result = context.step_output("validate_application")
        if not validation_result.get("is_valid"):
            return {"skipped": True, "reason": "Validation failed"}

        input_data = context.workflow_input()
        application_data = input_data.get("application_data", {})

        # Equipment age
        equipment_year = application_data.get("equipment_year", 0)
        current_year = datetime.now().year
        equipment_age_years = (
            max(0, current_year - equipment_year) if equipment_year else 0
        )

        # Years in business from formation date if provided
        years_in_business = application_data.get("years_in_business", 0)

        # Is startup
        is_startup = years_in_business < 2.0

        # Is trucking
        equipment_category = application_data.get("equipment_category", "").lower()
        trucking_categories = {
            "class_8_truck",
            "trailer",
            "semi",
            "truck",
            "tractor_trailer",
        }
        is_trucking = equipment_category in trucking_categories

        return {
            "equipment_age_years": equipment_age_years,
            "years_in_business": years_in_business,
            "is_startup": is_startup,
            "is_trucking": is_trucking,
            "derived_at": datetime.utcnow().isoformat(),
        }

    async def evaluate_all_lenders(self, context) -> dict:
        """Step 3: Evaluate application against all lender policies.

        This step runs evaluations in parallel for performance.

        Args:
            context: Hatchet workflow context.

        Returns:
            Evaluation results for all lenders.
        """
        derive_result = context.step_output("derive_features")
        if derive_result.get("skipped"):
            return {"skipped": True, "reason": "Feature derivation skipped"}

        input_data = context.workflow_input()
        application_data = input_data.get("application_data", {})

        # Build evaluation context
        eval_context = build_evaluation_context(
            application_id=application_data.get("application_id", "unknown"),
            business=application_data.get("business", {}),
            guarantor=application_data.get("guarantor", {}),
            business_credit=application_data.get("business_credit", {}),
            loan_request={
                "loan_amount": application_data.get("loan_amount", 0),
                "requested_term_months": application_data.get("requested_term_months"),
                "transaction_type": application_data.get("transaction_type", "purchase"),
                "is_private_party": application_data.get("is_private_party", False),
            },
            equipment={
                "category": application_data.get("equipment_category", ""),
                "year": application_data.get("equipment_year", 0),
                "mileage": application_data.get("equipment_mileage"),
                "hours": application_data.get("equipment_hours"),
                "condition": application_data.get("equipment_condition", "used"),
            },
            derived_features=derive_result,
        )

        # Run matching
        result = await self.matching_service.match_application_async(eval_context)

        return {
            "total_evaluated": result.total_evaluated,
            "total_eligible": result.total_eligible,
            "matches": [m.to_dict() for m in result.matches],
            "best_match": result.best_match.to_dict() if result.best_match else None,
            "evaluated_at": datetime.utcnow().isoformat(),
        }

    async def rank_results(self, context) -> dict:
        """Step 4: Compute final rankings for evaluation results.

        Args:
            context: Hatchet workflow context.

        Returns:
            Final workflow result with rankings and status.
        """
        eval_result = context.step_output("evaluate_all_lenders")
        if eval_result.get("skipped"):
            return {
                "status": "skipped",
                "reason": eval_result.get("reason"),
            }

        matches = eval_result.get("matches", [])

        # Rank eligible lenders
        eligible = [m for m in matches if m.get("is_eligible")]
        ineligible = [m for m in matches if not m.get("is_eligible")]

        # Sort eligible by fit score descending
        eligible.sort(key=lambda m: m.get("fit_score", 0), reverse=True)

        # Assign ranks
        for rank, match in enumerate(eligible, start=1):
            match["rank"] = rank

        # Ineligible have no rank
        for match in ineligible:
            match["rank"] = None

        # Combine results
        all_matches = eligible + ineligible

        return {
            "status": "completed",
            "total_evaluated": eval_result.get("total_evaluated"),
            "total_eligible": eval_result.get("total_eligible"),
            "best_match": eval_result.get("best_match"),
            "ranked_matches": all_matches,
            "completed_at": datetime.utcnow().isoformat(),
        }


# Export step functions for direct use and testing
async def validate_application(context) -> dict:
    """Validate application - standalone step function."""
    workflow = ApplicationEvaluationWorkflow()
    return await workflow.validate_application(context)


async def derive_features(context) -> dict:
    """Derive features - standalone step function."""
    workflow = ApplicationEvaluationWorkflow()
    return await workflow.derive_features(context)


async def evaluate_all_lenders(context) -> dict:
    """Evaluate lenders - standalone step function."""
    workflow = ApplicationEvaluationWorkflow()
    return await workflow.evaluate_all_lenders(context)


async def rank_results(context) -> dict:
    """Rank results - standalone step function."""
    workflow = ApplicationEvaluationWorkflow()
    return await workflow.rank_results(context)


# Register with Hatchet if available
if hatchet:
    try:

        @hatchet.workflow(
            name="application-evaluation", on_events=["application:submitted"]
        )
        class HatchetApplicationEvaluationWorkflow:
            """Hatchet-decorated workflow class."""

            def __init__(self):
                self._workflow = ApplicationEvaluationWorkflow()

            @hatchet.step(timeout="30s", retries=3)
            async def validate_application(self, context) -> dict:
                return await self._workflow.validate_application(context)

            @hatchet.step(timeout="30s", parents=["validate_application"])
            async def derive_features(self, context) -> dict:
                return await self._workflow.derive_features(context)

            @hatchet.step(timeout="2m", parents=["derive_features"], retries=2)
            async def evaluate_all_lenders(self, context) -> dict:
                return await self._workflow.evaluate_all_lenders(context)

            @hatchet.step(timeout="30s", parents=["evaluate_all_lenders"], retries=3)
            async def rank_results(self, context) -> dict:
                """Rank results. Includes database persistence."""
                # Run the ranking logic
                result = await self._workflow.rank_results(context)

                # Persist to database using SQLAlchemy (Hatchet worker creates own session)
                try:
                    application_id = context.workflow_input().get("application_id")
                    if application_id:
                        async with async_session_factory() as db:
                            try:
                                db_manager = ApplicationDBManager(db)
                                await db_manager.update_status(
                                    UUID(application_id), "completed"
                                )
                                # Sync lenders to DB before saving match results (avoids FK violation)
                                policies = self._workflow.policy_loader.load_all_policies(
                                    skip_errors=True
                                )
                                await db_manager.sync_lenders(policies)
                                await db_manager.save_match_results(
                                    UUID(application_id),
                                    result.get("ranked_matches", []),
                                )
                                await db.commit()  # Explicit commit for Hatchet worker
                            except Exception as e:
                                await db.rollback()  # Rollback on error
                                logger.error(f"SQLAlchemy persistence failed: {e}")
                                # Update status to error
                                try:
                                    async with async_session_factory() as error_db:
                                        db_manager = ApplicationDBManager(error_db)
                                        await db_manager.update_status(
                                            UUID(application_id), "error"
                                        )
                                        await error_db.commit()
                                except Exception:
                                    pass
                                raise
                except Exception as e:
                    logger.error(f"Failed to persist results: {e}")
                    # Don't fail the workflow step for persistence errors

                return result

        logger.info("Registered ApplicationEvaluationWorkflow with Hatchet")
    except Exception as e:
        logger.warning(f"Failed to register workflow with Hatchet: {e}")
