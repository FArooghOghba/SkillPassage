import asyncio
from typing import (
    Any,
    Union,
)

import pytest
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
)

from src.user.exceptions import (
    UserAlreadyExistsError,
    UserNotFoundError,
)
from src.user.models import User
from src.user.schemas.user_base_profile_schemas import UserBaseProfileCreate
from src.user.schemas.user_schemas import UserCreate
from src.user.services.registration_services import register_user
from src.user.services.user_profile_services import get_user_profile_by_user_id
from src.user.services.user_services import get_user_by_email


@pytest.mark.asyncio
class TestRegisterUser:
    """Test suite for user registration service.

    Verifies user registration process including:
    - User creation
    - Password hashing
    - Profile creation
    - Error handling for duplicate emails/usernames
    - Transaction rollback on failures
    """

    async def test_service_register_user_return_success(
            self, db_session: AsyncSession,
            first_test_user_client_payload: dict[str, str],
            first_test_user_profile_payload: dict[str, str]
    ) -> None:
        """
        Test successful user registration with complete profile.

        Verifies that a user can be registered with all required fields
        and that both user and profile data are correctly stored.

        Args:
            db_session: Async SQLAlchemy session for database operations

        Raises:
            AssertionError: If user registration fails or data doesn't match
        """
        email = first_test_user_client_payload["email"]
        username = first_test_user_client_payload["username"]
        password = first_test_user_client_payload["password"]
        first_name = first_test_user_profile_payload["first_name"]
        last_name = first_test_user_profile_payload["last_name"]
        phone_number = first_test_user_profile_payload["phone_number"]

        user_data = UserCreate(**first_test_user_client_payload)
        profile_data = UserBaseProfileCreate(**first_test_user_profile_payload)

        await register_user(
            db=db_session,
            user_schema=user_data,
            profile_schema=profile_data
        )

        user = await get_user_by_email(
            db=db_session, user_email=email
        )

        profile = await get_user_profile_by_user_id(
            db=db_session, user_id=user.id
        )

        assert user is not None
        assert user.email == email
        assert user.username == username
        assert user.hashed_password != password
        assert user.is_active is True

        assert profile.first_name == first_name
        assert profile.last_name == last_name
        assert profile.phone_number == phone_number

    async def test_service_register_user_password_is_hashed_success(
            self, db_session: AsyncSession,
            first_test_user_client_payload: dict[str, str],
            first_test_user_profile_payload: dict[str, str]
    ) -> None:
        """
        Test that password is properly hashed during registration.

        Verifies that the password is not stored in plain text and
        is properly hashed using bcrypt.

        Args:
            db_session: Async SQLAlchemy session for database operations
            first_test_user_client_payload: Test user data dictionary
            first_test_user_profile_payload: Test profile data dictionary

        Raises:
            AssertionError: If password is not properly hashed
        """
        password = first_test_user_client_payload["password"]

        user_data = UserCreate(**first_test_user_client_payload)
        profile_data = UserBaseProfileCreate(
            **first_test_user_profile_payload
        )

        user = await register_user(
            db=db_session,
            user_schema=user_data,
            profile_schema=profile_data
        )

        assert user.hashed_password != password
        assert user.hashed_password.startswith("$2b$")  # bcrypt hash prefix

    async def test_service_create_user_without_phone_number_return_success(
            self, db_session: AsyncSession,
            first_test_user_client_payload: dict[str, str],
            first_test_user_profile_payload: dict[str, str]
    ) -> None:
        """
        Test successful user creation without phone number.

        Verifies that a user can be created with a null phone number,
        ensuring that this field is truly optional in the system.

        Args:
            db_session: Async SQLAlchemy session for database operations
            first_test_user_client_payload: Test user data dictionary
            first_test_user_profile_payload: Test profile data dictionary

        Raises:
            AssertionError: If the user creation fails or if the phone
                number field is not properly handled as null
        """
        email = first_test_user_client_payload["email"]
        first_test_user_profile_payload.pop("phone_number")

        user_data = UserCreate(**first_test_user_client_payload)
        profile_data = UserBaseProfileCreate(
            **first_test_user_profile_payload
        )

        created_user = await register_user(
            db=db_session,
            user_schema=user_data,
            profile_schema=profile_data
        )

        user = await get_user_by_email(
            db=db_session, user_email=email
        )

        profile = await get_user_profile_by_user_id(
            db=db_session, user_id=user.id
        )

        assert created_user.email == email
        assert profile.phone_number is None

    async def test_service_register_user_with_existed_email_return_error(
            self, db_session: AsyncSession,
            first_test_client_user: User,
            first_test_user_client_payload: dict[str, str],
            first_test_user_profile_payload: dict[str, str]
    ) -> None:
        """
        Test error handling when registering with an existing email.

        Verifies that attempting to register a user with an email that
        already exists in the system raises the appropriate error.

        Args:
            db_session: Async SQLAlchemy session for database operations
            first_test_client_user: Existing test user in the database
            first_test_user_client_payload: Test user data dictionary
            first_test_user_profile_payload: Test profile data dictionary

        Raises:
            AssertionError: If the expected error is not raised or
                if the error message doesn't match
        """
        existed_email = first_test_client_user.email
        first_test_user_client_payload["email"] = existed_email

        user_data = UserCreate(**first_test_user_client_payload)
        profile_data = UserBaseProfileCreate(
            **first_test_user_profile_payload
        )

        with pytest.raises(UserAlreadyExistsError) as exc_info:
            await register_user(
                db=db_session,
                user_schema=user_data,
                profile_schema=profile_data
            )

        assert str(exc_info.value.detail) == (
            f"User already exists with Email: {existed_email}"
        )

    async def test_service_register_user_with_existed_username_return_error(
            self, db_session: AsyncSession,
            first_test_client_user: User,
            first_test_user_client_payload: dict[str, str],
            first_test_user_profile_payload: dict[str, str]
    ) -> None:
        """
        Test error handling when registering with an existing username.

        Verifies that attempting to register a user with a username that
        already exists in the system raises the appropriate error.

        Args:
            db_session: Async SQLAlchemy session for database operations
            first_test_client_user: Existing test user in the database
            first_test_user_client_payload: Test user data dictionary
            first_test_user_profile_payload: Test profile data dictionary

        Raises:
            AssertionError: If the expected error is not raised or
                if the error message doesn't match
        """
        existed_username = first_test_client_user.username
        first_test_user_client_payload["username"] = existed_username

        user_data = UserCreate(**first_test_user_client_payload)
        profile_data = UserBaseProfileCreate(
            **first_test_user_profile_payload
        )

        with pytest.raises(UserAlreadyExistsError) as exc_info:
            await register_user(
                db=db_session,
                user_schema=user_data,
                profile_schema=profile_data
            )

        assert str(exc_info.value.detail) == (
            f"User already exists with Username: {existed_username}"
        )

    async def test_service_register_user_transaction_rollback_on_failure(
            self,
            db_session: AsyncSession,
            monkeypatch: pytest.MonkeyPatch,
            first_test_user_client_payload: dict[str, str],
            first_test_user_profile_payload: dict[str, str]
    ) -> None:
        """Test that user creation is rolled back if profile creation fails.

        This test verifies the atomicity of the registration process by
        simulating a failure during profile creation and ensuring no
        user record remains in the database after the transaction is
        rolled back.

        The test uses monkeypatch to inject a failing implementation of the
        create_user_profile function, then verifies that no user record exists
        after the expected exception is raised.

        Args:
            db_session: Async SQLAlchemy session for database operations
            monkeypatch: Pytest fixture for patching functions during test
            first_test_user_client_payload: Test user data dictionary
            first_test_user_profile_payload: Test profile data dictionary

        Raises:
            AssertionError: If the transaction rollback doesn't work
            as expected and a user record remains in the database
        """
        # Setup test data
        user_data = UserCreate(**first_test_user_client_payload)
        profile_data = UserBaseProfileCreate(
            **first_test_user_profile_payload
        )

        # Mock profile creation to fail
        async def mock_create_profile(*args: Any, **kwargs: Any) -> None:
            raise ValueError("Simulated failure")

        monkeypatch.setattr(
            "src.user.services.registration_services.create_user_profile",
            mock_create_profile
        )

        # Act & Assert
        with pytest.raises(ValueError):
            await register_user(
                db=db_session,
                user_schema=user_data,
                profile_schema=profile_data
            )

        # Verify user was not created
        with pytest.raises(UserNotFoundError) as exc_info:
            await get_user_by_email(db=db_session, user_email=user_data.email)

        assert str(exc_info.value.detail) == (
            f"User not found with Email: {user_data.email}"
        )

    async def test_service_register_user_with_invalid_profile_returns_error(
            self, db_session: AsyncSession,
            first_test_user_client_payload: dict[str, str],
            first_test_user_profile_payload: dict[str, str]
    ) -> None:
        """Test error handling when registering with invalid profile data.

        This test verifies that when profile data fails validation,
        the appropriate error is raised and no user record is created.

        Args:
            db_session: Async SQLAlchemy session for database operations
            first_test_user_client_payload: Test user data dictionary
            first_test_user_profile_payload: Test profile data dictionary
        """
        user_data = UserCreate(**first_test_user_client_payload)

        # For example, if phone number has a format requirement:
        # Create an invalid profile with data that will fail validation
        first_test_user_profile_payload["phone_number"] = "invalid_phone_num"

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            invalid_profile_data = UserBaseProfileCreate(
                **first_test_user_profile_payload
            )
            await register_user(
                db=db_session,
                user_schema=user_data,
                profile_schema=invalid_profile_data
            )

        assert "Invalid phone number format" in str(exc_info.value)

        # Verify user was not created (transaction was rolled back)
        with pytest.raises(UserNotFoundError):
            await get_user_by_email(db=db_session, user_email=user_data.email)

    async def test_service_concurrent_register_user_with_same_email(
            self, async_session_maker: async_sessionmaker[AsyncSession],
            first_test_user_client_payload: dict[str, str],
            second_test_user_client_payload: dict[str, str],
            first_test_user_profile_payload: dict[str, str]
    ) -> None:
        """Test handling of concurrent registrations with the same user email.

        This test verifies the system's ability to maintain data integrity
        when two users attempt to register simultaneously using the same
        email address. It simulates a race condition that could occur in
        production when multiple registration requests arrive at nearly
        the same time.

        Test workflow:
        1. Two different users attempt to register with identical email
        addresses
        2. The registrations run concurrently using independent database
        sessions
        3. Due to the database's unique constraint on email, only one
        registration
           should succeed while the other should fail with an exception
        4. The database should contain exactly one user with the target email

        Technical implementation details:
        - Uses asyncio.gather() to execute both registrations concurrently
        - Creates independent database sessions for each registration attempt
        - Explicitly commits successful transactions
        - Captures exceptions from failed registration attempts
        - Verifies database integrity by querying for the user after test

        Args:
            async_session_maker: Factory to create independent database
                        sessions, ensuring proper transaction isolation
            first_test_user_client_payload: Test data for the first user
            second_test_user_client_payload: Test data for the second user
            first_test_user_profile_payload: Profile data for both test users
        """
        # Set the same email for both users to create the conflict condition
        existed_email = first_test_user_client_payload["email"]
        second_test_user_client_payload["email"] = existed_email

        # Create Pydantic model instances from the test data
        # These objects will be used for the registration attempts
        first_user_data = UserCreate(**first_test_user_client_payload)
        first_profile_data = UserBaseProfileCreate(
            **first_test_user_profile_payload
        )

        second_user_data = UserCreate(**second_test_user_client_payload)
        second_profile_data = UserBaseProfileCreate(
            **first_test_user_profile_payload
        )

        # Helper function to perform a registration attempt and handle
        # any exceptions.
        # This abstracts away the session management and error handling logic
        async def attempt_registration(
                user_schema: UserCreate,
                profile_schema: UserBaseProfileCreate
        ) -> Union[User, Exception]:
            try:
                # Create a fresh session for this specific registration
                # attempt. This ensures proper transaction isolation between
                # concurrent attempts
                async with async_session_maker() as test_session:
                    registered_user = await register_user(
                        db=test_session,
                        user_schema=user_schema,
                        profile_schema=profile_schema
                    )
                    # Explicitly commit the transaction to make changes
                    # visible. This is critical for the test to properly
                    # simulate concurrent operations
                    await test_session.commit()
                    return registered_user
            except Exception as e:
                # Instead of letting the exception propagate, capture it
                # so we can analyze which registration attempt failed
                return e

        # Execute both registration attempts concurrently
        # asyncio.gather runs both coroutines in parallel and
        # waits for them to complete
        results = await asyncio.gather(
            attempt_registration(first_user_data, first_profile_data),
            attempt_registration(second_user_data, second_profile_data)
        )

        # Analyze the results to determine which attempts succeeded vs failed
        # We expect exactly one success and one failure due to the email
        # uniqueness constraint
        user_results = [r for r in results if isinstance(r, User)]
        error_results = [r for r in results if isinstance(r, Exception)]

        # Verify that exactly one registration succeeded
        # If both succeed, the database constraint isn't working correctly
        # If both fail, there's an error in the test or registration logic
        assert len(user_results) == 1, \
            "Expected exactly one successful registration"
        assert len(error_results) == 1, \
            "Expected exactly one registration to fail"

        # Final verification: check the database to confirm only one user
        # exists with this email. This validates that database integrity
        # is maintained even with concurrent operations
        async with async_session_maker() as test_get_session:
            user = await get_user_by_email(
                db=test_get_session, user_email=existed_email
            )
            assert user is not None, "User should exist in database"
