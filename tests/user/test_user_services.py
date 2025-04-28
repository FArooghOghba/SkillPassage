"""
Unit tests for user service functions.

This module contains test cases for the user service layer functions
that handle core user operations such as retrieval, creation, updates,
and deletion.
"""
from uuid import uuid4

import pytest
from faker import Faker
from sqlalchemy.ext.asyncio import AsyncSession

from src.user.exceptions import (
    UserAlreadyExistsError,
    UserNotFoundError,
)
from src.user.models import User
from src.user.schemas.user_schemas import (
    UserCreate,
    UserUpdate,
)
from src.user.services.user_services import (
    create_user,
    get_user_by_email,
    get_user_by_id,
    update_user,
)


@pytest.mark.asyncio
class TestCreateUser:
    """
    Test suite for create_user service function.

    This class contains tests that verify the behavior of the create_user
    service function under various scenarios including:
    - Successful user creation with all fields
    - Handling of duplicate email/username constraints
    - Password hashing verification

    Each test method uses its own database transaction that is rolled back
    after the test completes.
    """

    async def test_create_user_success(
            self, db_session: AsyncSession,
            first_test_user_client_payload: dict[str, str]
    ) -> None:
        """
        Test successful user creation with valid data.

        This test verifies that a user can be created with all required fields
        and that the user is properly stored in the database with the correct
        attributes and default values.

        Args:
            db_session: Async SQLAlchemy session for database operations.
            first_test_user_client_payload: Dictionary containing test
            user data.
            first_test_user_client_payload: Test user data dictionary

        Raises:
            AssertionError: If any of the user attributes don't match
                the expected values or if the user isn't properly stored
                in the database.
        """
        # Prepare user data from payload
        user_data = UserCreate(**first_test_user_client_payload)

        # Create user and store in database
        created_user = await create_user(db=db_session, schema=user_data)

        # Verify user attributes
        assert created_user.id is not None
        assert created_user.email == user_data.email
        assert created_user.username == user_data.username
        assert created_user.hashed_password != user_data.password
        assert created_user.is_active is True

        # Verify that user exists in the database
        db_user = await get_user_by_email(
            db=db_session, user_email=user_data.email
        )
        assert db_user is not None, "User should exist in the database"
        assert db_user.email == user_data.email, "Emails should match"

    async def test_service_create_user_with_existed_email_return_error(
            self, db_session: AsyncSession,
            first_test_client_user: User,
            first_test_user_client_payload: dict[str, str]
    ) -> None:
        """
        Test user creation fails with duplicate email.

        Verifies that attempting to create a user with an existing email
        address raises an UserAlreadyExistsError. This ensures the unique
        constraint on the email field is working properly.

        Args:
            db_session: Async SQLAlchemy session for database operations.
            first_test_client_user: Pre-created test user fixture.
            first_test_user_client_payload: Test user data dictionary

        Raises:
            AssertionError: If the expected UserAlreadyExistsError
            is not raised or if the error message doesn't match
            the expected format.
        """
        # Prepare data for the test
        existed_email = first_test_client_user.email

        # Same email as first user
        first_test_user_client_payload['email'] = existed_email

        # Try to create second user with same email
        user_data = UserCreate(**first_test_user_client_payload)

        # Verify the error is raised
        with pytest.raises(UserAlreadyExistsError) as exc_info:
            await create_user(db=db_session, schema=user_data)

        # Verify the error message is correct
        assert str(exc_info.value.detail) == (
            f"User already exists with Email: {existed_email}"
        )

    async def test_service_create_user_with_existed_username_return_error(
            self, db_session: AsyncSession,
            first_test_client_user: User,
            first_test_user_client_payload: dict[str, str]
    ) -> None:
        """
        Test user creation fails with duplicate username.

        Verifies that attempting to create a user with an existing username
        raises an UserAlreadyExistsError. This ensures the unique constraint
        on the username field is working properly.

        Args:
            db_session: Async SQLAlchemy session for database operations.
            first_test_client_user: Pre-created test user fixture.
            first_test_user_client_payload: Test user data dictionary

        Raises:
            AssertionError: If the expected UserAlreadyExistsError is
            not raised or if the error message doesn't match the expected
            format.
        """
        existed_username = first_test_client_user.username

        # Same username as first user
        first_test_user_client_payload['username'] = existed_username

        # Try to create second user with same username
        user_data = UserCreate(**first_test_user_client_payload)

        with pytest.raises(UserAlreadyExistsError) as exc_info:
            await create_user(db=db_session, schema=user_data)

        assert str(exc_info.value.detail) == (
            f"User already exists with Username: {existed_username}"
        )

    async def test_service_create_user_password_hashing(
            self, db_session: AsyncSession,
            first_test_user_client_payload: dict[str, str]
    ) -> None:
        """
        Test that password is properly hashed during user creation.

        Verifies that the user's password is properly hashed using bcrypt
        before being stored in the database. Checks the hash format and
        ensures the original password is not stored in plain text.

        Args:
            db_session: Async SQLAlchemy session for database operations.
            first_test_user_client_payload: Test user data dictionary

        Raises:
            AssertionError: If the password is not properly hashed or if
                the hash format doesn't match bcrypt's expected pattern.
        """
        password = first_test_user_client_payload['password']

        user_data = UserCreate(**first_test_user_client_payload)

        created_user = await create_user(db=db_session, schema=user_data)

        # Verify password is hashed
        user_hashed_password = created_user.hashed_password
        assert user_hashed_password != password
        assert user_hashed_password.startswith("$2b$")  # bcrypt hash prefix
        assert len(created_user.hashed_password) > 50  # bcrypt hash length

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "invalid_password,expected_error",
        [
            (
                "nouppercaseordigits!",
                "must contain an uppercase letter; must contain a digit"
            ),
            (
                "NOLOWERCASEORDIGITS!",
                "must contain a lowercase letter; must contain a digit"
            ),
            (
                "NoSpecialCharsOrDigits",
                "must contain a digit; must contain a special character"
            ),
            (
                "NoSpecial123",
                "must contain a special character"
            ),
            (
                "short",
                "must be at least 8 characters"
            ),  # If you have min_length=8
        ],
        ids=[
            "no-uppercase-or-digits",
            "no-lowercase-or-digits",
            "no-special-chars-or-digits",
            "no-special-chars",
            "too-short",
        ]
    )
    async def test_service_create_user_with_invalid_password_return_error(
            self, db_session: AsyncSession,
            first_test_user_client_payload: dict[str, str],
            invalid_password: str, expected_error: str
    ) -> None:
        """
        Test that invalid password formats are rejected.

        Uses parameterized test cases to verify that passwords missing required
        complexity elements (lowercase, uppercase, digits, special chars)
        are rejected with appropriate error messages.

        Args:
            db_session: Async SQLAlchemy session for database operations.
            first_test_user_client_payload: Base test user payload.
            invalid_password: The invalid password to test.
            expected_error: Expected error message fragment.
        """
        first_test_user_client_payload['password'] = invalid_password

        with pytest.raises(ValueError) as exc_info:
            user_data = UserCreate(**first_test_user_client_payload)
            await create_user(db=db_session, schema=user_data)

        error_message = str(exc_info.value)
        assert "Password validation failed" in error_message

        # Check that the specific expected error is in the message
        for error_part in expected_error.split("; "):
            assert error_part in error_message


@pytest.mark.asyncio
class TestGetUserById:
    """
    Test suite for get_user_by_id service function.

    This class contains tests that verify the behavior of the get_user_by_id
    service function under various scenarios including:
    - Successful user retrieval
    - Handling of non-existent users

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

        assert str(exc_info.value) == (
            f"404: User not found with ID: {non_existent_id}"
        )


@pytest.mark.asyncio
class TestGetUserByEmail:
    """
    Test suite for get_user_by_email service function.

    This class contains tests that verify the behavior of the get_user_by_email
    service function under various scenarios including:
    - Successful user retrieval
    - Handling of non-existent users

    Each test method uses its own database transaction that is rolled back
    after the test completes.
    """

    async def test_service_get_user_by_email_return_success(
        self, db_session: AsyncSession, first_test_client_user: User
    ) -> None:
        """
        Test successful user retrieval by email.

        Verifies that get_user_by_email correctly returns a user when given
        a valid email address. Checks all relevant user attributes to ensure
        the complete user object is returned correctly.

        Args:
            db_session: Async SQLAlchemy session for database operations.
            first_test_client_user: Pre-created test user fixture.

        Raises:
            AssertionError: If any of the user attributes don't match
                the expected values.
        """
        user = await get_user_by_email(
            db=db_session, user_email=first_test_client_user.email
        )

        assert user.id == first_test_client_user.id
        assert user.email == first_test_client_user.email
        assert user.username == first_test_client_user.username
        assert user.is_active == first_test_client_user.is_active

    async def test_service_get_not_existing_user_by_email_raises_not_found(
        self, db_session: AsyncSession
    ) -> None:
        """
        Test error handling for non-existent email addresses.

        Verifies that attempting to retrieve a user with a non-existent email
        raises the appropriate UserNotFoundError with the correct error
        message.

        Args:
            db_session: Async SQLAlchemy session for database operations.

        Raises:
            AssertionError: If the expected UserNotFoundError is not raised
                or if the error message doesn't match the expected format.
        """
        non_existent_email = Faker().email()

        with pytest.raises(UserNotFoundError) as exc_info:
            await get_user_by_email(
                db=db_session, user_email=non_existent_email
            )

        assert str(exc_info.value) == (
            f"404: User not found with Email: {non_existent_email}"
        )


@pytest.mark.asyncio
class TestUpdateUser:
    """
    Test suite for update_user service function.

    This class contains tests that verify the behavior of the update_user
    service function under various scenarios including:
    - Successful user updates with different field combinations
    - Handling of non-existent users
    - Validation of unique constraints (email/username)
    - Partial updates
    """

    async def test_service_update_user_success(
        self, db_session: AsyncSession, first_test_client_user: User
    ) -> None:
        """
        Test successful user update with all fields.

        Verifies that a user can be updated with new values for all
        updatable fields.

        Args:
            db_session: Async SQLAlchemy session for database operations.
            first_test_client_user: Pre-created test user fixture.
        """
        fake = Faker()
        update_data = UserUpdate(
            email=fake.email(),
            username=fake.user_name()
        )

        updated_user = await update_user(
            db=db_session,
            user_id=first_test_client_user.id,
            schema=update_data
        )

        # Verify updated fields
        assert updated_user.email == update_data.email
        assert updated_user.username == update_data.username

        # Verify unchanged fields
        assert updated_user.id == first_test_client_user.id
        assert updated_user.is_active == first_test_client_user.is_active

    async def test_service_update_user_partial_success(
        self, db_session: AsyncSession, first_test_client_user: User
    ) -> None:
        """
        Test successful partial user update.

        Verifies that a user can be updated with only some fields
        changed while others remain unchanged.

        Args:
            db_session: Async SQLAlchemy session for database operations.
            first_test_client_user: Pre-created test user fixture.
        """
        # Store original values
        original_email = first_test_client_user.email

        # Update only names
        fake = Faker()
        update_data = UserUpdate(
            username=fake.user_name()
        )

        updated_user = await update_user(
            db=db_session,
            user_id=first_test_client_user.id,
            schema=update_data
        )

        # Verify updated fields
        assert updated_user.username == update_data.username

        # Verify unchanged fields
        assert updated_user.email == original_email

    async def test_service_update_nonexistent_user_raises_error(
        self, db_session: AsyncSession
    ) -> None:
        """
        Test error handling when updating non-existent user.

        Verifies that attempting to update a non-existent user
        raises the appropriate UserNotFoundError.

        Args:
            db_session: Async SQLAlchemy session for database operations.
        """
        fake = Faker()
        non_existent_id = uuid4()
        update_data = UserUpdate(username=fake.user_name())

        with pytest.raises(UserNotFoundError) as exc_info:
            await update_user(
                db=db_session,
                user_id=non_existent_id,
                schema=update_data
            )

        assert str(exc_info.value) == (
            f"404: User not found with ID: {non_existent_id}"
        )

    async def test_service_update_user_with_existing_email_raises_error(
        self, db_session: AsyncSession,
        first_test_client_user: User,
        second_test_client_user: User
    ) -> None:
        """
        Test error handling when updating with existing email.

        Verifies that attempting to update a user's email to one that
        already exists raises an UserAlreadyExistsError.

        Args:
            db_session: Async SQLAlchemy session for database operations.
            first_test_client_user: First pre-created test user fixture.
            second_test_client_user: Second pre-created test user fixture.
        """
        existed_email = second_test_client_user.email
        update_data = UserUpdate(email=existed_email)

        with pytest.raises(UserAlreadyExistsError) as exc_info:
            await update_user(
                db=db_session,
                user_id=first_test_client_user.id,
                schema=update_data
            )

        assert str(exc_info.value.detail) == (
            f"User already exists with Email: {existed_email}"
        )

    async def test_service_update_user_with_existing_username_raises_error(
        self, db_session: AsyncSession,
        first_test_client_user: User,
        second_test_client_user: User
    ) -> None:
        """
        Test error handling when updating with existing username.

        Verifies that attempting to update a user's username to one that
        already exists raises an UserAlreadyExistsError.

        Args:
            db_session: Async SQLAlchemy session for database operations.
            first_test_client_user: First pre-created test user fixture.
            second_test_client_user: Second pre-created test user fixture.
        """
        existed_username = second_test_client_user.username
        update_data = UserUpdate(username=existed_username)

        with pytest.raises(UserAlreadyExistsError) as exc_info:
            await update_user(
                db=db_session,
                user_id=first_test_client_user.id,
                schema=update_data
            )

        assert str(exc_info.value.detail) == (
            f"User already exists with Username: {existed_username}"
        )
