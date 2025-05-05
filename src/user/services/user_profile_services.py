"""User profile service module for managing profile-related business logic.

This module provides core functionality for user profile management operations,
including profile creation, retrieval, and updates.
"""
import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.user.exceptions import UserNotFoundError
from src.user.models import UserProfile
from src.user.schemas.user_profile_schemas import (
    UserProfileCreate,
    UserProfileUpdate,
)
from src.user.services.user_services import get_user_by_id


logger = logging.getLogger(__name__)


async def get_user_profile_by_id(
        db: AsyncSession, profile_id: UUID
) -> UserProfile:
    """Retrieve a profile by its ID.

    Args:
        db: Database session
        profile_id: UUID of the profile to retrieve

    Returns:
        UserProfile: The requested profile

    Raises:
        UserNotFoundError: If no profile exists with the given ID
    """
    profile: UserProfile | None = await db.get(
        entity=UserProfile, ident=profile_id
    )

    if not profile:
        logger.warning(msg=f"Profile not found with ID: {profile_id}")
        raise UserNotFoundError(identifier=profile_id)

    logger.info(msg=f"Successfully retrieved profile with ID: {profile_id}")
    return profile


async def get_user_profile_by_user_id(
    db: AsyncSession, user_id: UUID
) -> UserProfile:
    """Retrieve a user's profile by user ID.

    Args:
        db: Database session
        user_id: UUID of the user whose profile to retrieve

    Returns:
        UserProfile: The requested user profile

    Raises:
        UserNotFoundError: If no profile exists for the given user ID
    """
    query = select(UserProfile).where(UserProfile.user_id == user_id)
    result = await db.execute(query)
    profile = result.scalar_one_or_none()

    if not profile:
        logger.warning(msg=f"Profile not found for user ID: {user_id}")
        raise UserNotFoundError(
            identifier=user_id,
            lookup_field="User ID (Profile)"
        )

    logger.info(msg=f"Successfully retrieved profile for user ID: {user_id}")
    return profile


async def create_user_profile(
    db: AsyncSession,
    user_id: UUID,
    schema: UserProfileCreate
) -> UserProfile:
    """Create a new profile for a user.

    Args:
        db: Database session
        user_id: UUID of the user to create profile for
        schema: Validated profile creation data

    Returns:
        UserProfile: The newly created profile

    Raises:
        UserNotFoundError: If the specified user doesn't exist
        SQLAlchemyError: If there's any database error during creation
    """
    # Verify user exists using the dedicated service function
    await get_user_by_id(db=db, user_id=user_id)

    try:
        # Create new profile instance
        profile = UserProfile(
            user_id=user_id,
            first_name=schema.first_name,
            last_name=schema.last_name,
            phone_number=schema.phone_number,
        )

        db.add(profile)
        await db.flush()
        await db.refresh(profile)

        logger.info(
            msg="Successfully created user profile",
            extra={
                "user_id": str(user_id),
                "profile_id": str(profile.id)
            }
        )
        return profile

    except SQLAlchemyError as e:
        await db.rollback()
        logger.error(
            msg="Database error during profile creation",
            extra={
                "user_id": str(user_id),
                "error": str(e)
            }
        )
        raise


async def update_user_profile(
    db: AsyncSession,
    user_id: UUID,
    schema: UserProfileUpdate
) -> UserProfile:
    """Update an existing user profile.

    Args:
        db: Database session
        user_id: UUID of the user whose profile to update
        schema: Validated profile update data

    Returns:
        UserProfile: The updated profile

    Raises:
        UserNotFoundError: If no profile exists for the given user
        SQLAlchemyError: If there's any database error during update
    """
    # Get existing profile
    profile = await get_user_profile_by_user_id(db=db, user_id=user_id)

    # Update profile attributes if provided in schema
    update_data = schema.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(profile, field, value)

    try:
        await db.flush()
        await db.refresh(profile)

        logger.info(
            msg="Successfully updated user profile",
            extra={
                "user_id": str(user_id),
                "profile_id": str(profile.id),
                "updated_fields": list(update_data.keys())
            }
        )
        return profile

    except SQLAlchemyError as e:
        await db.rollback()
        logger.error(
            msg="Database error during profile update",
            extra={
                "user_id": str(user_id),
                "error": str(e),
                "updated_fields": list(update_data.keys())
            }
        )
        raise
