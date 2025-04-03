"""Router configuration for API v1 endpoints."""
from fastapi import APIRouter

from src.core.health import router as health_router


router = APIRouter()

router.include_router(router=health_router)
