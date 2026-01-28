"""Workflow trigger utilities for starting and monitoring workflows."""

import logging
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.hatchet import get_hatchet
from app.policies.loader import PolicyLoader
from app.services.application_db_manager import ApplicationDBManager
from app.workflows.evaluation import ApplicationEvaluationWorkflow

logger = logging.getLogger(__name__)


class WorkflowRun:
    """Represents a workflow run with its ID and status."""

    def __init__(self, run_id: str, status: str = "pending"):
        self.run_id = run_id
        self.status = status
        self.result: Optional[dict] = None

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "run_id": self.run_id,
            "status": self.status,
            "result": self.result,
        }


async def trigger_evaluation(
    application_id: str,
    application_data: dict,
    db: Optional[AsyncSession] = None,
) -> WorkflowRun:
    """Trigger the application evaluation workflow.

    This function either triggers a Hatchet workflow if configured,
    or runs the evaluation synchronously.

    Args:
        application_id: The unique application identifier.
        application_data: The application data to evaluate.
        db: Optional SQLAlchemy async session for synchronous persistence.

    Returns:
        WorkflowRun with run ID and initial status.
    """
    hatchet = get_hatchet()

    if hatchet:
        # Use Hatchet for async workflow execution
        try:
            run = await hatchet.admin.run_workflow(
                "application-evaluation",
                input={
                    "application_id": application_id,
                    "application_data": application_data,
                },
            )
            logger.info(f"Triggered Hatchet workflow for application {application_id}")
            return WorkflowRun(run_id=run.workflow_run_id, status="running")
        except Exception as e:
            logger.error(f"Failed to trigger Hatchet workflow: {e}")
            # Fall back to synchronous execution
            pass

    # Synchronous execution without Hatchet
    logger.info(f"Running evaluation synchronously for application {application_id}")

    run_id = str(uuid4())
    workflow_run = WorkflowRun(run_id=run_id, status="running")

    try:
        workflow = ApplicationEvaluationWorkflow()
        result = await workflow.run(application_data)
        workflow_run.status = result.get("status", "completed")
        workflow_run.result = result

        # Persist results using SQLAlchemy
        if db and result.get("status") == "completed":
            db_manager = ApplicationDBManager(db)
            await db_manager.update_status(UUID(application_id), "completed")
            # Sync lenders to DB before saving match results (avoids FK violation)
            policy_loader = PolicyLoader()
            policies = policy_loader.load_all_policies(skip_errors=True)
            await db_manager.sync_lenders(policies)
            await db_manager.save_match_results(
                UUID(application_id), result.get("ranked_matches", [])
            )
            # Note: Don't commit here - FastAPI's get_db() dependency auto-commits

    except Exception as e:
        logger.error(f"Workflow execution failed: {e}")
        workflow_run.status = "failed"
        workflow_run.result = {"error": str(e)}
        if db:
            db_manager = ApplicationDBManager(db)
            await db_manager.update_status(UUID(application_id), "error")

    return workflow_run


async def get_workflow_status(run_id: str) -> dict:
    """Get the status of a workflow run.

    Args:
        run_id: The workflow run ID.

    Returns:
        Dictionary with status and result if available.
    """
    hatchet = get_hatchet()

    if hatchet:
        try:
            run = await hatchet.admin.get_workflow_run(run_id)
            return {
                "run_id": run_id,
                "status": run.status,
                "result": run.result if hasattr(run, "result") else None,
            }
        except Exception as e:
            logger.error(f"Failed to get workflow status: {e}")
            return {
                "run_id": run_id,
                "status": "unknown",
                "error": str(e),
            }

    # Without Hatchet, we can't track async status
    # In a real implementation, you'd store run state in a database
    return {
        "run_id": run_id,
        "status": "unknown",
        "message": "Workflow tracking not available without Hatchet",
    }


def trigger_evaluation_sync(
    application_id: str,
    application_data: dict,
) -> dict:
    """Trigger evaluation synchronously (non-async version).

    This is a convenience function for synchronous contexts.

    Args:
        application_id: The unique application identifier.
        application_data: The application data to evaluate.

    Returns:
        Workflow result dictionary.
    """
    import asyncio

    async def _run():
        workflow = ApplicationEvaluationWorkflow()
        return await workflow.run(application_data)

    return asyncio.run(_run())
