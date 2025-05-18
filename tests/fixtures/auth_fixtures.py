"""Authentication fixtures for testing authentication-related functionality.

This module provides pytest fixtures for authentication testing, including:
- Test user IDs
- JWT tokens
- Authentication credentials
"""
from datetime import timedelta
from typing import (
    Callable,
    Dict,
)
from uuid import (
    UUID,
    uuid4,
)

import pytest

from src.auth.services.token_services import create_access_token
from src.core.config import auth_settings
from src.user.models import User as UserModel


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


@pytest.fixture
def auth_headers_for_user() -> Callable[[UserModel], Dict[str, str]]:
    """Fixture providing authorization headers for a given user.

    This fixture returns a function that generates HTTP authorization
    headers containing a valid JWT access token for a specified user
    model instance. The token is used to authenticate requests in tests.

    Returns:
        Callable[[UserModel], Dict[str, str]]: A function that takes a
            UserModel instance and returns a dictionary with the
            "Authorization" header containing a bearer token.
    """
    def _auth_headers_for_user(user_model: UserModel) -> Dict[str, str]:
        """Generate HTTP authorization headers for a given user model.

        Args:
            user_model: The UserModel instance to generate the token for

        Returns:
            Dict[str, str]: A dictionary containing the "Authorization" header
                with a bearer token
        """
        token = create_access_token(
            user_id=user_model.id,
            expires_delta=auth_settings.access_token_expire_delta
        )
        return {"Authorization": f"Bearer {token}"}
    return _auth_headers_for_user


@pytest.fixture
def auth_headers_with_expired_token() -> Callable[[UserModel], Dict[str, str]]:
    """Fixture providing authorization headers with an expired token.

    This fixture returns a function that generates HTTP authorization
    headers containing an expired JWT access token for a specified user
    model instance. The token is used to simulate expired token scenarios
    in tests.

    Returns:
        Callable[[UserModel], Dict[str, str]]: A function that takes a
            UserModel instance and returns a dictionary with the
            "Authorization" header containing an expired bearer token.
    """
    def _auth_headers_for_user(user_model: UserModel) -> Dict[str, str]:
        """Generate HTTP authorization headers with an expired token.

        Args:
            user_model: The UserModel instance to generate the token for

        Returns:
            Dict[str, str]: A dictionary containing the "Authorization" header
                with an expired bearer token
        """
        token = create_access_token(
            user_id=user_model.id,
            expires_delta=timedelta(seconds=-1)
        )
        return {"Authorization": f"Bearer {token}"}
    return _auth_headers_for_user
