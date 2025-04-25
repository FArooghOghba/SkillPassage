"""
Unit tests for user profile service functions.

This module contains test cases for the user profile service layer functions
that handle profile operations such as creation, retrieval, and updates.
"""
from uuid import uuid4

import pytest
from faker import Faker
from sqlalchemy.ext.asyncio import AsyncSession

from src.user.constants import UserRole
from src.user.exceptions import UserNotFoundError
from src.user.models import (
    User,
    UserProfile,
)
from src.user.schemas.user_profile_schemas import (
    UserProfileCreate,
    UserProfileUpdate,
)
from src.user.services.user_profile_services import (
    create_user_profile,
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
        profile_data = UserProfileCreate(
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
        assert profile.role == UserRole.CLIENT.value

    async def test_service_create_user_profile_without_phone_return_success(
        self,
        db_session: AsyncSession,
        first_test_client_user: User
    ) -> None:
        """Test profile creation with optional phone number field as None."""
        fake = Faker()
        profile_data = UserProfileCreate(
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
        profile_data = UserProfileCreate(
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


@pytest.mark.asyncio
class TestGetUserProfile:
    """Test suite for get_user_profile service function."""

    async def test_service_get_user_profile_return_success(
        self,
        db_session: AsyncSession,
        first_test_client_user: User,
        first_test_client_profile: UserProfile
    ) -> None:
        """Test successful profile retrieval."""
        profile = await get_user_profile_by_user_id(
            db=db_session,
            user_id=first_test_client_user.id
        )

        assert profile is not None
        assert profile.id == first_test_client_profile.id
        assert profile.user_id == first_test_client_user.id

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
class TestUpdateUserProfile:
    """Test suite for update_user_profile service function."""

    async def test_service_update_user_profile_return_success(
        self,
        db_session: AsyncSession,
        first_test_client_user: User,
        first_test_client_profile: UserProfile
    ) -> None:
        """Test successful profile update with all fields."""
        fake = Faker()
        update_data = UserProfileUpdate(
            first_name=fake.first_name(),
            last_name=fake.last_name(),
            phone_number=f"+1{fake.numerify(text='##########')}",
            role=UserRole.ADMIN.value
        )

        updated_profile = await update_user_profile(
            db=db_session,
            user_id=first_test_client_user.id,
            schema=update_data
        )

        assert updated_profile.first_name == update_data.first_name
        assert updated_profile.last_name == update_data.last_name
        assert updated_profile.phone_number == update_data.phone_number
        assert updated_profile.role == update_data.role

    async def test_service_update_user_profile_partial_return_success(
        self,
        db_session: AsyncSession,
        first_test_client_user: User,
        first_test_client_profile: UserProfile
    ) -> None:
        """Test partial profile update with only some fields."""
        # Store original values
        original_first_name = first_test_client_profile.first_name
        original_phone = first_test_client_profile.phone_number

        # Update only last name
        fake = Faker()
        update_data = UserProfileUpdate(
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
        update_data = UserProfileUpdate(
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
