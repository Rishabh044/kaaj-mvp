"""Application API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import (
    get_db,
    get_matching_service,
    get_hatchet_client,
    PaginationParams,
)
from app.rules.context_builder import build_evaluation_context
from app.schemas.api import (
    ApplicationListItem,
    ApplicationStatusResponse,
    ApplicationSubmitRequest,
    ApplicationSubmitResponse,
    CriterionResultResponse,
    LenderMatchResponse,
    MatchingResultsResponse,
    PaginatedListResponse,
)
from app.services.matching_service import LenderMatchingService
from app.workflows.triggers import trigger_evaluation

router = APIRouter()


@router.post("/", response_model=ApplicationSubmitResponse, status_code=status.HTTP_201_CREATED)
async def submit_application(
    application_input: ApplicationSubmitRequest,
    db: AsyncSession = Depends(get_db),
    hatchet=Depends(get_hatchet_client),
) -> ApplicationSubmitResponse:
    """Submit a new loan application and trigger evaluation workflow.

    This endpoint creates a new application record and triggers the
    evaluation workflow to match against lender policies.
    """
    import uuid
    from datetime import datetime

    # Generate application ID and number
    application_id = str(uuid.uuid4())
    application_number = f"APP-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

    # Build application data for workflow
    application_data = {
        "application_id": application_id,
        "fico_score": application_input.applicant.fico_score,
        "state": application_input.business.state,
        "loan_amount": application_input.loan_request.amount,
        "equipment_category": application_input.equipment.category,
        "equipment_year": application_input.equipment.year,
        "years_in_business": application_input.business.years_in_business,
        "guarantor": {
            "fico_score": application_input.applicant.fico_score,
            "transunion_score": application_input.applicant.transunion_score,
            "experian_score": application_input.applicant.experian_score,
            "equifax_score": application_input.applicant.equifax_score,
            "is_homeowner": application_input.applicant.is_homeowner,
            "is_us_citizen": application_input.applicant.is_us_citizen,
            "has_cdl": application_input.applicant.has_cdl,
            "cdl_years": application_input.applicant.cdl_years,
            "industry_experience_years": application_input.applicant.industry_experience_years,
            "has_bankruptcy": application_input.credit_history.has_bankruptcy,
            "bankruptcy_discharge_years": application_input.credit_history.bankruptcy_discharge_years,
            "bankruptcy_chapter": application_input.credit_history.bankruptcy_chapter,
            "has_open_judgements": application_input.credit_history.has_open_judgements,
            "judgement_amount": application_input.credit_history.judgement_amount,
            "has_foreclosure": application_input.credit_history.has_foreclosure,
            "has_repossession": application_input.credit_history.has_repossession,
            "has_tax_liens": application_input.credit_history.has_tax_liens,
            "tax_lien_amount": application_input.credit_history.tax_lien_amount,
        },
        "business": {
            "name": application_input.business.name,
            "state": application_input.business.state,
            "industry_code": application_input.business.industry_code,
            "industry_name": application_input.business.industry_name,
            "years_in_business": application_input.business.years_in_business,
            "annual_revenue": application_input.business.annual_revenue,
            "fleet_size": application_input.business.fleet_size,
        },
        "business_credit": (
            {
                "paynet_score": application_input.business_credit.paynet_score,
                "paynet_master_score": application_input.business_credit.paynet_master_score,
                "paydex_score": application_input.business_credit.paydex_score,
            }
            if application_input.business_credit
            else {}
        ),
        "equipment_mileage": application_input.equipment.mileage,
        "equipment_hours": application_input.equipment.hours,
        "equipment_condition": application_input.equipment.condition,
        "transaction_type": application_input.loan_request.transaction_type,
        "is_private_party": application_input.loan_request.is_private_party,
        "requested_term_months": application_input.loan_request.requested_term_months,
    }

    # Trigger evaluation workflow
    workflow_run = await trigger_evaluation(application_id, application_data)

    return ApplicationSubmitResponse(
        id=application_id,
        application_number=application_number,
        status="processing" if workflow_run.status == "running" else workflow_run.status,
        workflow_run_id=workflow_run.run_id,
        message="Application submitted successfully. Evaluation in progress.",
    )


@router.get("/", response_model=PaginatedListResponse)
async def list_applications(
    pagination: PaginationParams = Depends(),
    db: AsyncSession = Depends(get_db),
) -> PaginatedListResponse:
    """List all applications with pagination.

    Returns a paginated list of application summaries.
    """
    # In production, this would query the database
    # For now, return empty list
    return PaginatedListResponse(
        items=[],
        total=0,
        skip=pagination.skip,
        limit=pagination.limit,
    )


@router.get("/{application_id}", response_model=ApplicationListItem)
async def get_application(
    application_id: str,
    db: AsyncSession = Depends(get_db),
) -> ApplicationListItem:
    """Get full application details by ID.

    Returns the complete application details including business,
    applicant, equipment, and loan request information.
    """
    # In production, this would query the database
    # For now, raise not found
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Application {application_id} not found",
    )


@router.get("/{application_id}/status", response_model=ApplicationStatusResponse)
async def get_application_status(
    application_id: str,
    db: AsyncSession = Depends(get_db),
) -> ApplicationStatusResponse:
    """Get current processing status for an application.

    Returns the workflow status and summary of results if completed.
    """
    # In production, this would check workflow status
    return ApplicationStatusResponse(
        application_id=application_id,
        status="completed",
    )


@router.get("/{application_id}/results", response_model=MatchingResultsResponse)
async def get_match_results(
    application_id: str,
    matching_service: LenderMatchingService = Depends(get_matching_service),
    db: AsyncSession = Depends(get_db),
) -> MatchingResultsResponse:
    """Get matching results for an application.

    Returns detailed matching results including eligibility,
    scores, and criteria breakdown for each lender.
    """
    # In production, this would query stored results
    # For now, demonstrate with a sample evaluation

    # Build a sample context for demonstration
    context = build_evaluation_context(
        application_id=application_id,
        guarantor={"fico_score": 720, "is_homeowner": True},
        business={"years_in_business": 5.0, "state": "TX"},
        loan_request={"loan_amount": 5000000, "transaction_type": "purchase"},
        equipment={"category": "construction", "year": 2022},
    )

    # Run matching
    result = matching_service.match_application(context)

    # Transform to response
    matches = []
    for m in result.matches:
        criteria_results = []
        if m.best_program:
            for cr in m.best_program.criteria_results:
                criteria_results.append(
                    CriterionResultResponse(
                        rule_name=cr.rule_name,
                        passed=cr.passed,
                        required_value=cr.required_value,
                        actual_value=cr.actual_value,
                        message=cr.message,
                    )
                )

        matches.append(
            LenderMatchResponse(
                lender_id=m.lender_id,
                lender_name=m.lender_name,
                is_eligible=m.is_eligible,
                fit_score=m.fit_score,
                rank=m.rank,
                best_program=m.best_program.program_name if m.best_program else None,
                rejection_reasons=(
                    m.global_rejection_reasons
                    or (m.best_program.rejection_reasons if m.best_program else [])
                ),
                criteria_results=criteria_results,
            )
        )

    return MatchingResultsResponse(
        application_id=application_id,
        total_evaluated=result.total_evaluated,
        total_eligible=result.total_eligible,
        best_match=matches[0] if result.has_eligible_lender else None,
        matches=matches,
    )
