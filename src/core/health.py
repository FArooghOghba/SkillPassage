"""Health check endpoint implementation."""
from typing import Dict

from fastapi import APIRouter


router = APIRouter(
    tags=["health"],
    prefix="/health",
)


@router.get(
    path="/",
    description="Health check endpoint",
    response_model=Dict[str, str]
)
async def health_check() -> Dict[str, str]:
    """
    Check if the API is running.

    Returns:
        Dict[str, str]: Status message indicating service health
    """
    return {"status": "Healthy"}
