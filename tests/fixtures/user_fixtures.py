"""Fixtures for user-related tests."""
from typing import (
    AsyncGenerator,
    Dict,
)

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.user.models import (
    User,
    UserProfile,
)
from tests.factories.user_factories import (
    UserFactory,
    UserProfileFactory,
)


@pytest.fixture
async def first_test_client_user(
        db_session: AsyncSession
) -> AsyncGenerator[User, None]:
    """Create a test user in the database.

    This fixture creates a standard test user with default factory values
    and automatically handles cleanup after tests.

    Args:
        db_session: The database session fixture

    Yields:
        User: A test user instance
    """
    user = await UserFactory()
    yield user
    # Cleanup is handled by db_session fixture's rollback


@pytest.fixture
async def second_test_client_user(
        db_session: AsyncSession
) -> AsyncGenerator[User, None]:
    """Create a test user in the database.

    This fixture creates a standard test user with default factory values
    and automatically handles cleanup after tests.

    Args:
        db_session: The database session fixture

    Yields:
        User: A test user instance
    """
    user = await UserFactory()
    yield user
    # Cleanup is handled by db_session fixture's rollback


@pytest.fixture
def first_test_user_client_payload() -> Dict[str, str]:
    """Fixture for creating a test user instance.

    This fixture uses the `BaseUserFactory` factory
    to create a test user instance. The created user
    can be used in tests to simulate a user with predefined
    attributes for testing various scenarios.

    :return: a dict test user payload
    """
    return UserFactory.create_payload()


@pytest.fixture
def second_test_user_client_payload() -> Dict[str, str]:
    """Fixture for creating a test user instance.

    This fixture uses the `BaseUserFactory` factory
    to create a test user instance. The created user
    can be used in tests to simulate a user with predefined
    attributes for testing various scenarios.

    :return: a dict test user payload
    """
    return UserFactory.create_payload()


@pytest.fixture
async def first_test_user_login_payload() -> Dict[str, str]:
    """Fixture for login a test user instance.

    This fixture uses the `UserFactory` factory
    to log in a test user instance. The created user
    can be used in tests to simulate a user with predefined
    attributes for testing various scenarios.

    :return: a dict test user payload
    """
    return await UserFactory.login_payload()


@pytest.fixture
async def first_test_client_profile(
        db_session: AsyncSession,
        first_test_client_user: User
) -> AsyncGenerator[UserProfile, None]:
    """Create a test user profile in the database.

    This fixture creates a profile for the first test user with default
    factory values and automatically handles cleanup after tests.

    Args:
        db_session: The database session fixture
        first_test_client_user: The user fixture to associate with
        this profile

    Yields:
        UserProfile: A test user profile instance
    """
    profile = await UserProfileFactory(user=first_test_client_user)
    yield profile
    # Cleanup is handled by db_session fixture's rollback


@pytest.fixture
async def second_test_client_profile(
        db_session: AsyncSession,
        second_test_client_user: User
) -> AsyncGenerator[UserProfile, None]:
    """Create a test user profile in the database.

    This fixture creates a profile for the second test user with default
    factory values and automatically handles cleanup after tests.

    Args:
        db_session: The database session fixture
        second_test_client_user: The user fixture to associate with
        this profile

    Yields:
        UserProfile: A test user profile instance
    """
    profile = await UserProfileFactory(user=second_test_client_user)
    yield profile
    # Cleanup is handled by db_session fixture's rollback


@pytest.fixture
def first_test_user_profile_payload() -> Dict[str, str]:
    """Fixture for creating a test user profile payload.

    This fixture uses the `UserProfileFactory` factory
    to create a test user profile payload. The created payload
    can be used in tests to simulate a user profile with predefined
    attributes for testing various scenarios.

    :return: a dict test user profile payload
    """
    return UserProfileFactory.create_payload()
