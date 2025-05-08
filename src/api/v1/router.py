"""Router configuration for API v1 endpoints."""
from fastapi import APIRouter

from src.auth.apis import router as login_router
from src.core.health import router as health_router
from src.user.apis import router as user_registration_router


router = APIRouter()


router.include_router(router=health_router)
router.include_router(router=user_registration_router)
router.include_router(router=login_router)
