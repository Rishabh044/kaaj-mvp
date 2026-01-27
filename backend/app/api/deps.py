"""Common API dependencies."""

from typing import AsyncGenerator, Optional

from fastapi import Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db  # Reuse the session dependency from database module
from app.core.hatchet import get_hatchet
from app.policies.loader import PolicyLoader
from app.rules.engine import MatchingEngine
from app.services.matching_service import LenderMatchingService


def get_policy_loader() -> PolicyLoader:
    """Get policy loader dependency."""
    return PolicyLoader()


def get_matching_engine() -> MatchingEngine:
    """Get matching engine dependency."""
    return MatchingEngine()


def get_matching_service(
    policy_loader: PolicyLoader = Depends(get_policy_loader),
    engine: MatchingEngine = Depends(get_matching_engine),
) -> LenderMatchingService:
    """Get matching service dependency."""
    return LenderMatchingService(engine=engine, policy_loader=policy_loader)


def get_hatchet_client():
    """Get Hatchet client dependency."""
    return get_hatchet()


class PaginationParams:
    """Pagination query parameters."""

    def __init__(
        self,
        skip: int = Query(0, ge=0, description="Number of items to skip"),
        limit: int = Query(20, ge=1, le=100, description="Maximum items to return"),
    ):
        self.skip = skip
        self.limit = limit


def validate_uuid(value: str, field_name: str = "id") -> str:
    """Validate a string is a valid UUID format."""
    import re

    uuid_pattern = re.compile(
        r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
        re.IGNORECASE,
    )
    if not uuid_pattern.match(value):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid {field_name} format",
        )
    return value
