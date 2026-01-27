"""API module for FastAPI routes."""

from fastapi import APIRouter

from app.api.routes import applications, lenders

api_router = APIRouter()

# Include route modules
api_router.include_router(
    applications.router,
    prefix="/applications",
    tags=["Applications"],
)
api_router.include_router(
    lenders.router,
    prefix="/lenders",
    tags=["Lenders"],
)
