"""
User service module for managing user-related business logic.

This module provides core functionality for user management operations,
including user creation, retrieval, update, and deletion.
"""
import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import (
    IntegrityError,
    SQLAlchemyError,
)
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.services import get_password_hash
from src.user.exceptions import UserNotFoundError
from src.user.models import User
from src.user.schemas import (
    UserCreate,
    UserUpdate,
)


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


async def create_user(db: AsyncSession, schema: UserCreate) -> User:
    """
    Create a new user in the database.

    Args:
        db: Database session
        schema: Validated user creation data

    Returns:
        User: The newly created user

    Raises:
        IntegrityError: If a user with the same email or username
        already exists.
        SQLAlchemyError: If there's any other database error during creation
    """
    # Hash the password before storing
    hashed_password = get_password_hash(schema.password)

    # Create new user instance
    user = User(
        email=schema.email,
        username=schema.username,
        first_name=schema.first_name,
        last_name=schema.last_name,
        phone_number=schema.phone_number,
        hashed_password=hashed_password,
    )

    try:
        # Add the user to the session
        db.add(user)
        # Flush to send INSERT to DB, generate ID, check constraints
        await db.flush()
        # Refresh to load the generated ID/defaults back onto the user object
        await db.refresh(user)

        logger.info(
            msg="Successfully created user",
            extra={
                "email": user.email,
                "username": user.username,
                "user_id": str(user.id)
            }
        )
        return user

    except IntegrityError as e:
        logger.error(
            msg="Failed to create user - duplicate entry",
            extra={
                "email": schema.email,
                "username": schema.username,
                "error": str(e)
            }
        )
        raise

    except SQLAlchemyError as e:
        logger.error(
            msg="Failed to create user - database error",
            extra={
                "email": schema.email,
                "username": schema.username,
                "error": str(e)
            }
        )
        raise


async def update_user(
        db: AsyncSession, user_id: UUID, schema: UserUpdate
) -> User:
    """
    Update an existing user's information.

    Args:
        db: Database session
        user_id: UUID of the user to update
        schema: Validated update data

    Returns:
        User: The updated user

    Raises:
        UserNotFoundError: If no user exists with the given ID
        IntegrityError: If update violates unique constraints
        SQLAlchemyError: If there's any other database error
    """
    # Get existing user
    user = await get_user_by_id(db=db, user_id=user_id)

    # Update user attributes if provided in schema
    update_data = schema.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)

    # Flush changes to check constraints and get updated user
    await db.flush()
    await db.refresh(user)

    logger.info(
        msg="Successfully updated user",
        extra={
            "user_id": str(user.id),
            "updated_fields": list(update_data.keys())
        }
    )
    return user
