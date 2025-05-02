"""Authentication fixtures for testing authentication-related functionality.

This module provides pytest fixtures for authentication testing, including:
- Test user IDs
- JWT tokens
- Authentication credentials
"""
from datetime import timedelta
from uuid import (
    UUID,
    uuid4,
)

import pytest

from src.auth.services.token_services import create_access_token


@pytest.fixture
def first_test_user_id() -> UUID:
    """Fixture providing a test user ID.

    Yields:
        UUID: A randomly generated UUID for test user identification
    """
    return uuid4()


@pytest.fixture
def fixt_test_token(first_test_user_id: UUID) -> str:
    """Fixture providing a valid test JWT token.

    Args:
        first_test_user_id: UUID of the test user

    Returns:
        str: A valid JWT access token
    """
    token = create_access_token(
        user_id=first_test_user_id,
        expires_delta=timedelta(minutes=30)
    )
    return token
