import pytest
from fastapi import status
from httpx import AsyncClient


HEALTH_CHECK_URL = "/api/v1/health"


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient) -> None:
    """Test the health check endpoint."""
    response = await client.get(url=HEALTH_CHECK_URL)
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {
        "status": "healthy",
        "database": "connected"
    }
