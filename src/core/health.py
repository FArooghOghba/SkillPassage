"""Health check endpoint implementation."""
from typing import Dict

from fastapi import (
    APIRouter,
    Depends,
)
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import get_db


router = APIRouter(
    tags=["health"],
    prefix="/health",
)


@router.get(
    path="/",
    description="Health check endpoint",
    response_model=Dict[str, str]
)
async def health_check(
        session: AsyncSession = Depends(get_db)
) -> Dict[str, str]:
    """
    Check if the API is running.

    Returns:
        Dict[str, str]: Status message indicating service health
    """
    try:
        # Test the database connection
        await session.execute(text("SELECT 1"))
        await session.commit()
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "database": str(e)}
