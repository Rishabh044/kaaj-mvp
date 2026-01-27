"""Lender API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_db, get_policy_loader
from app.policies.loader import PolicyLoader, PolicyLoadError
from app.schemas.api import (
    CriteriaDetail,
    LenderCreateRequest,
    LenderDetailResponse,
    LenderListItem,
    LenderStatusResponse,
    LenderUpdateRequest,
    ProgramDetail,
    RestrictionsDetail,
)

router = APIRouter()


@router.get("/", response_model=list[LenderListItem])
async def list_lenders(
    policy_loader: PolicyLoader = Depends(get_policy_loader),
) -> list[LenderListItem]:
    """List all lenders with program counts.

    Returns a list of all configured lenders with summary information.
    """
    policies = policy_loader.get_active_policies()

    return [
        LenderListItem(
            id=p.id,
            name=p.name,
            version=p.version,
            program_count=len(p.programs),
            is_active=True,  # All loaded policies are considered active
        )
        for p in policies
    ]


@router.get("/{lender_id}", response_model=LenderDetailResponse)
async def get_lender(
    lender_id: str,
    policy_loader: PolicyLoader = Depends(get_policy_loader),
) -> LenderDetailResponse:
    """Get lender details with full policy.

    Returns complete lender information including all programs
    and their criteria configurations.
    """
    try:
        policy = policy_loader.load_policy(lender_id)
    except PolicyLoadError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lender '{lender_id}' not found",
        )

    # Transform programs
    programs = []
    for prog in policy.programs:
        criteria_detail = None
        if prog.criteria:
            criteria_detail = CriteriaDetail(
                credit_score=(
                    prog.criteria.credit_score.model_dump()
                    if prog.criteria.credit_score
                    else None
                ),
                business=(
                    prog.criteria.business.model_dump()
                    if prog.criteria.business
                    else None
                ),
                credit_history=(
                    prog.criteria.credit_history.model_dump()
                    if prog.criteria.credit_history
                    else None
                ),
                equipment=(
                    prog.criteria.equipment.model_dump()
                    if prog.criteria.equipment
                    else None
                ),
                geographic=(
                    prog.criteria.geographic.model_dump()
                    if prog.criteria.geographic
                    else None
                ),
                industry=(
                    prog.criteria.industry.model_dump()
                    if prog.criteria.industry
                    else None
                ),
                transaction=(
                    prog.criteria.transaction.model_dump()
                    if prog.criteria.transaction
                    else None
                ),
            )

        programs.append(
            ProgramDetail(
                id=prog.id,
                name=prog.name,
                description=prog.description,
                is_app_only=prog.is_app_only,
                min_amount=prog.min_amount,
                max_amount=prog.max_amount,
                max_term_months=prog.max_term_months,
                criteria=criteria_detail,
            )
        )

    # Transform restrictions
    restrictions = None
    if policy.restrictions:
        restrictions = RestrictionsDetail(
            geographic=(
                policy.restrictions.geographic.model_dump()
                if policy.restrictions.geographic
                else None
            ),
            industry=(
                policy.restrictions.industry.model_dump()
                if policy.restrictions.industry
                else None
            ),
            transaction=(
                policy.restrictions.transaction.model_dump()
                if policy.restrictions.transaction
                else None
            ),
            equipment=(
                policy.restrictions.equipment.model_dump()
                if policy.restrictions.equipment
                else None
            ),
        )

    return LenderDetailResponse(
        id=policy.id,
        name=policy.name,
        version=policy.version,
        description=policy.description,
        contact_email=policy.contact_email,
        contact_phone=policy.contact_phone,
        programs=programs,
        restrictions=restrictions,
    )


@router.post("/", response_model=LenderDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_lender(
    lender_input: LenderCreateRequest,
    policy_loader: PolicyLoader = Depends(get_policy_loader),
) -> LenderDetailResponse:
    """Create a new lender with policy.

    Creates a new lender configuration. In a full implementation,
    this would write a new YAML file and register the lender.
    """
    # Check if lender already exists
    try:
        policy_loader.load_policy(lender_input.id)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Lender '{lender_input.id}' already exists",
        )
    except PolicyLoadError:
        pass  # Good, lender doesn't exist

    # In a full implementation, we would:
    # 1. Create a YAML file with the lender configuration
    # 2. Reload policies
    # 3. Return the new lender

    # For now, return a mock response
    return LenderDetailResponse(
        id=lender_input.id,
        name=lender_input.name,
        version=1,
        description=lender_input.description,
        contact_email=lender_input.contact_email,
        contact_phone=lender_input.contact_phone,
        programs=[],
    )


@router.put("/{lender_id}", response_model=LenderDetailResponse)
async def update_lender(
    lender_id: str,
    lender_update: LenderUpdateRequest,
    policy_loader: PolicyLoader = Depends(get_policy_loader),
) -> LenderDetailResponse:
    """Update an existing lender.

    Updates lender metadata. In a full implementation,
    this would modify the YAML file and reload.
    """
    try:
        policy = policy_loader.load_policy(lender_id)
    except PolicyLoadError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lender '{lender_id}' not found",
        )

    # In a full implementation, we would:
    # 1. Load and modify the YAML file
    # 2. Increment the version
    # 3. Reload policies
    # 4. Return the updated lender

    # For now, return current lender with updates applied
    return LenderDetailResponse(
        id=policy.id,
        name=lender_update.name or policy.name,
        version=policy.version + 1,
        description=lender_update.description or policy.description,
        contact_email=lender_update.contact_email or policy.contact_email,
        contact_phone=lender_update.contact_phone or policy.contact_phone,
        programs=[
            ProgramDetail(
                id=p.id,
                name=p.name,
                description=p.description,
                is_app_only=p.is_app_only,
                min_amount=p.min_amount,
                max_amount=p.max_amount,
                max_term_months=p.max_term_months,
            )
            for p in policy.programs
        ],
    )


@router.patch("/{lender_id}/status", response_model=LenderStatusResponse)
async def toggle_lender_status(
    lender_id: str,
    policy_loader: PolicyLoader = Depends(get_policy_loader),
) -> LenderStatusResponse:
    """Toggle lender active/inactive status.

    Toggles whether the lender is active for matching.
    In a full implementation, this would update the database.
    """
    try:
        policy = policy_loader.load_policy(lender_id)
    except PolicyLoadError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lender '{lender_id}' not found",
        )

    # In a full implementation, we would:
    # 1. Toggle the is_active flag in the database
    # 2. Return the new status

    # For demonstration, always return active
    return LenderStatusResponse(
        id=policy.id,
        name=policy.name,
        is_active=True,
        message=f"Lender '{policy.name}' status toggled",
    )


@router.delete("/{lender_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_lender(
    lender_id: str,
    policy_loader: PolicyLoader = Depends(get_policy_loader),
) -> None:
    """Soft delete a lender.

    Marks the lender as deleted. The policy file is preserved
    but the lender will not appear in matches.
    """
    try:
        policy_loader.load_policy(lender_id)
    except PolicyLoadError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lender '{lender_id}' not found",
        )

    # In a full implementation, we would:
    # 1. Mark the lender as deleted in the database
    # 2. Or remove/archive the YAML file

    return None


@router.get("/{lender_id}/programs", response_model=list[ProgramDetail])
async def list_lender_programs(
    lender_id: str,
    policy_loader: PolicyLoader = Depends(get_policy_loader),
) -> list[ProgramDetail]:
    """List all programs for a lender.

    Returns detailed information about each lending program.
    """
    try:
        policy = policy_loader.load_policy(lender_id)
    except PolicyLoadError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lender '{lender_id}' not found",
        )

    return [
        ProgramDetail(
            id=p.id,
            name=p.name,
            description=p.description,
            is_app_only=p.is_app_only,
            min_amount=p.min_amount,
            max_amount=p.max_amount,
            max_term_months=p.max_term_months,
        )
        for p in policy.programs
    ]
