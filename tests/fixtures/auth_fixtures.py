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
from src.core.config import auth_settings


@pytest.fixture
def first_test_user_id() -> UUID:
    """Fixture providing a test user ID.

    Yields:
        UUID: A randomly generated UUID for test user identification
    """
    return uuid4()


@pytest.fixture
def first_test_token(first_test_user_id: UUID) -> str:
    """Fixture providing a valid test JWT token.

    Args:
        first_test_user_id: UUID of the test user

    Returns:
        str: A valid JWT access token
    """
    token = create_access_token(
        user_id=first_test_user_id,
        expires_delta=auth_settings.access_token_expire_delta
    )
    return token


@pytest.fixture
def first_test_expired_token(first_test_user_id: UUID) -> str:
    """Fixture providing an expired test JWT token.

    Args:
        first_test_user_id: UUID of the test user

    Returns:
        str: An expired JWT access token, with a negative expiration delta
            to simulate a token that has already expired for testing purposes.
    """
    token = create_access_token(
        user_id=first_test_user_id,
        expires_delta=timedelta(seconds=-1)
    )
    return token
