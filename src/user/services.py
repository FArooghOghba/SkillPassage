"""
User service module for managing user-related business logic.

This module provides core functionality for user management operations,
including user creation, retrieval, update, and deletion.
"""
import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.user.exceptions import UserNotFoundError
from src.user.models import User


logger = logging.getLogger(__name__)


async def get_user_by_id(db: AsyncSession, user_id: UUID) -> User:
    """
    Retrieve a user by their ID.

    Args:
        db: Database session
        user_id: UUID of the user to retrieve

    Returns:
        User: The requested user

    Raises:
        UserNotFoundError: If no user exists with the given ID
    """
    user: User | None = await db.get(entity=User, ident=user_id)
    if not user:
        logger.warning(msg=f"User not found with ID: {user_id}")
        raise UserNotFoundError(user_id)

    logger.info(msg=f"Successfully retrieved user with ID: {user_id}")
    return user


async def get_user_by_email(db: AsyncSession, user_email: str) -> User:
    """
    Retrieve a user by their email address.

    Args:
        db: Database session
        user_email: Email of the user to retrieve

    Returns:
        User: The requested user

    Raises:
        UserNotFoundError: If no user exists with the given email
    """
    # Construct a select statement to find the user by email
    query = select(User).where(User.email == user_email)

    # Execute the statement and get the scalar result (one user or None)
    result = await db.execute(query)
    user: User | None = result.scalar_one_or_none()

    if not user:
        logger.warning(msg=f"User not found with Email: {user_email}")
        raise UserNotFoundError(identifier=user_email, lookup_field="Email")

    logger.info(msg=f"Successfully retrieved user with Email: {user_email}")
    return user
