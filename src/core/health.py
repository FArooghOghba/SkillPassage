"""Health check endpoint implementation."""
import logging

from fastapi import (
    APIRouter,
    Depends,
    status,
)
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import get_db


logger = logging.getLogger(__name__)


router = APIRouter(
    tags=["health"],
    prefix="/health",
)


@router.get(
    path="/",
    description="Health check endpoint",
    responses={
        status.HTTP_200_OK: {"description": "Service is healthy"},
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "description": "Service is unhealthy"
        },
    }
)
async def health_check(
        session: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """
    Check if the API and database connection are healthy.

    Sets HTTP status code to 200 if healthy, 503 if unhealthy.

    Returns:
        JSONResponse: Detailed status message with appropriate
        HTTP status code.
    """
    db_detail = "connection_failed"
    overall_status = "unhealthy"
    http_status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    try:
        # Test the database connection
        await session.execute(text("SELECT 1"))

        db_detail = "connected"
        overall_status = "healthy"
        http_status_code = status.HTTP_200_OK
    except Exception as e:
        logger.error(msg=f"Health check database error: {e}", exc_info=True)
        print(f"Health check database error: {e}")

    response_body = {"status": overall_status, "database": db_detail}

    return JSONResponse(
        content=response_body, status_code=http_status_code
    )
