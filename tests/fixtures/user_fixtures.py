"""Fixtures for user-related tests."""
from typing import AsyncGenerator

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.user.models import User
from tests.factories.user_factories import UserFactory


@pytest.fixture
async def first_test_client_user(
        db_session: AsyncSession
) -> AsyncGenerator[User, None]:
    """
    Create a test user in the database.

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
    """
    Create a test user in the database.

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
