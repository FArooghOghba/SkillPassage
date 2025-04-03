"""Main router configuration combining all API versions."""
from fastapi import APIRouter

from src.api.v1.router import router as v1_router


router = APIRouter()

router.include_router(
    router=v1_router,
    prefix="/api/v1"
)
