"""Application API endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import (
    PaginationParams,
    get_db,
    get_hatchet_client,
    get_matching_service,
)
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
from app.services.application_db_manager import ApplicationDBManager
from app.services.matching_service import LenderMatchingService
from app.workflows.triggers import trigger_evaluation

router = APIRouter()


@router.post(
    "/", response_model=ApplicationSubmitResponse, status_code=status.HTTP_201_CREATED
)
async def submit_application(
    application_input: ApplicationSubmitRequest,
    db: AsyncSession = Depends(get_db),
    hatchet=Depends(get_hatchet_client),
) -> ApplicationSubmitResponse:
    """Submit a new loan application and trigger evaluation workflow.

    This endpoint creates a new application record and triggers the
    evaluation workflow to match against lender policies.
    """
    service = ApplicationDBManager(db)

    # 1. Create DB records
    loan_application = await service.create_application(application_input)
    await db.commit()  # Commit BEFORE workflow (ensures record exists even if workflow fails)

    # 2. Build workflow data with application_id
    application_data = {
        "application_id": str(loan_application.id),
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

    # 3. Trigger evaluation workflow (pass db for sync path)
    workflow_run = await trigger_evaluation(
        str(loan_application.id), application_data, db=db
    )

    return ApplicationSubmitResponse(
        id=str(loan_application.id),
        application_number=loan_application.application_number,
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
    service = ApplicationDBManager(db)
    applications, total = await service.list_applications(
        pagination.skip, pagination.limit
    )

    items = [
        ApplicationListItem(
            id=str(app.id),
            application_number=app.application_number,
            business_name=app.business.legal_name,
            loan_amount=app.loan_amount,
            status=app.status,
            created_at=app.created_at.isoformat(),
        )
        for app in applications
    ]

    return PaginatedListResponse(
        items=items, total=total, skip=pagination.skip, limit=pagination.limit
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
    service = ApplicationDBManager(db)
    app = await service.get_application(UUID(application_id))
    if not app:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Application {application_id} not found",
        )

    return ApplicationListItem(
        id=str(app.id),
        application_number=app.application_number,
        business_name=app.business.legal_name,
        loan_amount=app.loan_amount,
        status=app.status,
        created_at=app.created_at.isoformat(),
    )


@router.get("/{application_id}/status", response_model=ApplicationStatusResponse)
async def get_application_status(
    application_id: str,
    db: AsyncSession = Depends(get_db),
) -> ApplicationStatusResponse:
    """Get current processing status for an application.

    Returns the workflow status and summary of results if completed.
    """
    service = ApplicationDBManager(db)
    app = await service.get_application(UUID(application_id))
    if not app:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Application {application_id} not found",
        )

    match_results = await service.get_match_results(app.id)
    eligible = [m for m in match_results if m.is_eligible]

    return ApplicationStatusResponse(
        application_id=application_id,
        status=app.status,
        total_evaluated=len(match_results),
        total_eligible=len(eligible),
        best_match=eligible[0].lender_id if eligible else None,
        processed_at=app.processed_at.isoformat() if app.processed_at else None,
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
    service = ApplicationDBManager(db)
    app = await service.get_application(UUID(application_id))
    if not app:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Application {application_id} not found",
        )

    match_results = await service.get_match_results(app.id)

    matches = [
        LenderMatchResponse(
            lender_id=mr.lender_id,
            lender_name=mr.lender.name if mr.lender else mr.lender_id,
            is_eligible=mr.is_eligible,
            fit_score=float(mr.fit_score),
            rank=mr.rank,
            best_program=mr.matched_program_name,
            rejection_reasons=mr.rejection_reasons or [],
            criteria_results=[
                CriterionResultResponse(
                    rule_name=v.get("rule_name", k),
                    passed=v.get("passed", False),
                    required_value=v.get("required_value", ""),
                    actual_value=v.get("actual_value", ""),
                    message=v.get("message", ""),
                )
                for k, v in (mr.criteria_results or {}).items()
            ],
        )
        for mr in match_results
    ]

    eligible_matches = [m for m in matches if m.is_eligible]

    return MatchingResultsResponse(
        application_id=application_id,
        total_evaluated=len(matches),
        total_eligible=len(eligible_matches),
        best_match=eligible_matches[0] if eligible_matches else None,
        matches=matches,
    )
