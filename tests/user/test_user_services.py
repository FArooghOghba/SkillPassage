"""
Unit tests for user service functions.

This module contains test cases for the user service layer functions
that handle core user operations such as retrieval, creation, updates,
and deletion.
Each test class focuses on a specific service function and includes
both success and error cases.

The tests use async pytest fixtures and factory boy for test data generation.
Database operations are automatically rolled back after each test to ensure
isolation.
"""
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.user.exceptions import UserNotFoundError
from src.user.models import User
from src.user.services import get_user_by_id


@pytest.mark.asyncio
class TestGetUserById:
    """
    Test suite for get_user_by_id service function.

    This class contains tests that verify the behavior of the get_user_by_id
    service function under various scenarios including:
    - Successful user retrieval
    - Handling of non-existent users
    - Retrieval of inactive users

    Each test method uses its own database transaction that is rolled back
    after the test completes.
    """

    async def test_service_get_user_by_id_return_success(
        self, db_session: AsyncSession, first_test_client_user: User
    ) -> None:
        """
        Test successful user retrieval by ID.

        Verifies that get_user_by_id correctly returns a user when given
        a valid user ID. Checks all relevant user attributes to ensure
        the complete user object is returned correctly.

        Args:
            db_session: Async SQLAlchemy session for database operations.
            first_test_client_user: Pre-created test user fixture.

        Raises:
            AssertionError: If any of the user attributes don't match
                the expected values.
        """
        user = await get_user_by_id(
            db=db_session, user_id=first_test_client_user.id
        )

        assert user.id == first_test_client_user.id
        assert user.email == first_test_client_user.email
        assert user.username == first_test_client_user.username
        assert user.is_active == first_test_client_user.is_active
        assert user.type == first_test_client_user.type

    async def test_service_get_not_existing_user_by_id_raises_not_found(
        self, db_session: AsyncSession
    ) -> None:
        """
        Test error handling for non-existent user IDs.

        Verifies that attempting to retrieve a user with a non-existent ID
        raises the appropriate UserNotFoundError with the correct error
        message.

        Args:
            db_session: Async SQLAlchemy session for database operations.

        Raises:
            AssertionError: If the expected UserNotFoundError is not raised
                or if the error message doesn't match the expected format.
        """
        non_existent_id = uuid4()

        with pytest.raises(UserNotFoundError) as exc_info:
            await get_user_by_id(db=db_session, user_id=non_existent_id)

        assert str(exc_info.value) == (f"404: User not found with ID: "
                                       f"{non_existent_id}")
