from typing import Any

import pytest
from faker import Faker
from sqlalchemy.ext.asyncio import AsyncSession

from src.user.constants import UserRole
from src.user.exceptions import (
    UserAlreadyExistsError,
    UserNotFoundError,
)
from src.user.models import User
from src.user.schemas.user_profile_schemas import UserProfileCreate
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
            self, db_session: AsyncSession
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
        fake = Faker()

        email = fake.email()
        username = fake.user_name()
        password = fake.password()

        first_name = fake.first_name()
        last_name = fake.last_name()
        phone_number = f"+1{fake.numerify(text='##########')}"

        user_data = UserCreate(
            email=email,
            username=username,
            password=password,
        )

        profile_data = UserProfileCreate(
            first_name=first_name,
            last_name=last_name,
            phone_number=phone_number,
        )
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

        assert profile.role == UserRole.CLIENT.value
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
        profile_data = UserProfileCreate(**first_test_user_profile_payload)

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
        profile_data = UserProfileCreate(
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
        profile_data = UserProfileCreate(**first_test_user_profile_payload)

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
        profile_data = UserProfileCreate(**first_test_user_profile_payload)

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
        profile_data = UserProfileCreate(**first_test_user_profile_payload)

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
