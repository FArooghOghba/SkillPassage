"""Unit tests for user profile service functions.

This module contains test cases for the user profile service layer functions
that handle profile operations such as creation, retrieval, and updates.
"""
from uuid import uuid4

import pytest
from faker import Faker
from sqlalchemy.ext.asyncio import AsyncSession

from src.user.exceptions import (
    UserNotFoundError,
    UserProfileAlreadyExistsError,
)
from src.user.models import (
    BaseUserProfile,
    User,
)
from src.user.schemas.user_base_profile_schemas import (
    UserBaseProfileCreate as UserBaseProfileCreateSchema,
    UserBaseProfileUpdate as UserBaseProfileUpdateSchema,
)
from src.user.services.user_profile_services import (
    create_user_profile,
    get_user_profile_by_id,
    get_user_profile_by_user_id,
    update_user_profile,
)


@pytest.mark.asyncio
class TestCreateUserProfile:
    """Test suite for create_user_profile service function."""

    async def test_service_create_user_profile_return_success(
        self,
        db_session: AsyncSession,
        first_test_client_user: User
    ) -> None:
        """Test successful profile creation with all fields."""
        fake = Faker()
        profile_data = UserBaseProfileCreateSchema(
            first_name=fake.first_name(),
            last_name=fake.last_name(),
            phone_number=f"+1{fake.numerify(text='##########')}",
        )

        profile = await create_user_profile(
            db=db_session,
            user_id=first_test_client_user.id,
            schema=profile_data
        )

        assert profile.id is not None
        assert profile.user_id == first_test_client_user.id
        assert profile.first_name == profile_data.first_name
        assert profile.last_name == profile_data.last_name
        assert profile.phone_number == profile_data.phone_number

    async def test_service_create_user_profile_without_phone_return_success(
        self,
        db_session: AsyncSession,
        first_test_client_user: User
    ) -> None:
        """Test profile creation with optional phone number field as None."""
        fake = Faker()
        profile_data = UserBaseProfileCreateSchema(
            first_name=fake.first_name(),
            last_name=fake.last_name(),
            phone_number=None,
        )

        profile = await create_user_profile(
            db=db_session,
            user_id=first_test_client_user.id,
            schema=profile_data
        )

        assert profile.phone_number is None

    async def test_service_create_user_profile_nonexistent_user_return_error(
        self,
        db_session: AsyncSession
    ) -> None:
        """Test error handling when creating profile for non-existent user."""
        fake = Faker()
        non_existent_id = uuid4()
        profile_data = UserBaseProfileCreateSchema(
            first_name=fake.first_name(),
            last_name=fake.last_name(),
        )

        with pytest.raises(UserNotFoundError) as exc_info:
            await create_user_profile(
                db=db_session,
                user_id=non_existent_id,
                schema=profile_data
            )

        assert str(exc_info.value) == (
            f"404: User not found with ID: {non_existent_id}"
        )

    async def test_service_create_user_profile_with_existed_user_return_error(
            self,
            db_session: AsyncSession,
            first_test_client_user: User,
            first_test_client_profile: BaseUserProfile
    ) -> None:
        """Test successful profile creation with all fields."""
        fake = Faker()
        profile_data = UserBaseProfileCreateSchema(
            first_name=fake.first_name(),
            last_name=fake.last_name(),
            phone_number=f"+1{fake.numerify(text='##########')}",
        )

        user_id_with_profile = first_test_client_user.id
        with pytest.raises(UserProfileAlreadyExistsError) as exc_info:
            await create_user_profile(
                db=db_session,
                user_id=user_id_with_profile,
                schema=profile_data
            )

        assert str(exc_info.value) == (
            f"409: A profile already exists for "
            f"user ID: {user_id_with_profile}"
        )


@pytest.mark.asyncio
class TestGetUserProfileByUserId:
    """Test suite for get_user_profile service function."""

    async def test_service_get_user_profile_return_success(
        self,
        db_session: AsyncSession,
        first_test_client_user: User,
        first_test_client_profile: BaseUserProfile
    ) -> None:
        """Test successful profile retrieval."""
        profile = await get_user_profile_by_user_id(
            db=db_session,
            user_id=first_test_client_user.id
        )

        assert profile is not None
        assert profile.id == first_test_client_profile.id
        assert profile.user_id == first_test_client_user.id
        assert profile.first_name == first_test_client_profile.first_name
        assert profile.last_name == first_test_client_profile.last_name
        assert profile.phone_number == first_test_client_profile.phone_number

    async def test_service_get_user_profile_nonexistent_user_return_error(
        self,
        db_session: AsyncSession
    ) -> None:
        """Test error handling when retrieving profile for
        non-existent user.
        """
        non_existent_id = uuid4()

        with pytest.raises(UserNotFoundError) as exc_info:
            await get_user_profile_by_user_id(
                db=db_session,
                user_id=non_existent_id
            )

        assert str(exc_info.value) == (
            f"404: User not found with User ID (Profile): {non_existent_id}"
        )


@pytest.mark.asyncio
class TestGetUserProfileById:
    """Test suite for user profile service functions.

    Contains comprehensive test cases for profile creation,
    retrieval by ID and user ID, and profile updates including
    error handling scenarios.
    """

    async def test_service_get_user_profile_by_profile_id_return_success(
            self, db_session: AsyncSession,
            first_test_client_user: User,
            first_test_client_profile: BaseUserProfile
    ) -> None:
        """Test successful retrieval of user profile by profile ID.

        Verifies that get_user_profile_by_id returns the correct profile
        when given a valid profile ID and that all profile attributes
        match the expected values.

        Args:
            db_session: Database session fixture
            first_test_client_user: Test user fixture
            first_test_client_profile: Test user profile fixture
        """
        profile = await get_user_profile_by_id(
            db=db_session, profile_id=first_test_client_profile.id
        )

        assert profile is not None
        assert profile.id == first_test_client_profile.id
        assert profile.user_id == first_test_client_user.id
        assert profile.first_name == first_test_client_profile.first_name
        assert profile.last_name == first_test_client_profile.last_name
        assert profile.phone_number == first_test_client_profile.phone_number

    async def test_service_get_nonexistence_user_profile_by_id_return_error(
        self, db_session: AsyncSession
    ) -> None:
        """Test error handling when retrieving non-existent user profile by ID.

        Verifies that get_user_profile_by_id raises UserNotFoundError with
        the correct error message when attempting to retrieve a profile that
        doesn't exist in the database.

        Args:
            db_session: Database session fixture
        """
        non_existent_profile_id = uuid4()
        with pytest.raises(UserNotFoundError) as exc_info:
            await get_user_profile_by_id(
                db=db_session, profile_id=non_existent_profile_id
            )
        assert str(exc_info.value) == (
            f"404: User not found with ID: {non_existent_profile_id}"
        )


@pytest.mark.asyncio
class TestUpdateUserProfile:
    """Test suite for update_user_profile service function."""

    async def test_service_update_user_profile_return_success(
        self,
        db_session: AsyncSession,
        first_test_client_user: User,
        first_test_client_profile: BaseUserProfile
    ) -> None:
        """Test successful profile update with all fields."""
        fake = Faker()
        update_data = UserBaseProfileUpdateSchema(
            first_name=fake.first_name(),
            last_name=fake.last_name(),
            phone_number=f"+1{fake.numerify(text='##########')}",
        )

        updated_profile = await update_user_profile(
            db=db_session,
            user_id=first_test_client_user.id,
            schema=update_data
        )

        assert updated_profile.first_name == update_data.first_name
        assert updated_profile.last_name == update_data.last_name
        assert updated_profile.phone_number == update_data.phone_number

    async def test_service_update_user_profile_partial_return_success(
        self,
        db_session: AsyncSession,
        first_test_client_user: User,
        first_test_client_profile: BaseUserProfile
    ) -> None:
        """Test partial profile update with only some fields."""
        # Store original values
        original_first_name = first_test_client_profile.first_name
        original_phone = first_test_client_profile.phone_number

        # Update only last name
        fake = Faker()
        update_data = UserBaseProfileUpdateSchema(
            last_name=fake.last_name()
        )

        updated_profile = await update_user_profile(
            db=db_session,
            user_id=first_test_client_user.id,
            schema=update_data
        )

        assert updated_profile.first_name == original_first_name
        assert updated_profile.last_name == update_data.last_name
        assert updated_profile.phone_number == original_phone

    async def test_service_update_profile_nonexistent_user_return_error(
        self,
        db_session: AsyncSession
    ) -> None:
        """Test error handling when updating profile for non-existent user."""
        fake = Faker()
        non_existent_id = uuid4()
        update_data = UserBaseProfileUpdateSchema(
            first_name=fake.first_name()
        )

        with pytest.raises(UserNotFoundError) as exc_info:
            await update_user_profile(
                db=db_session,
                user_id=non_existent_id,
                schema=update_data
            )

        assert str(exc_info.value) == (
            f"404: User not found with User ID (Profile): {non_existent_id}"
        )
