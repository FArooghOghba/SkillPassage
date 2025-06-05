"""User service module for managing user-related business logic.

This module provides core functionality for user management operations,
including user creation, retrieval, update, and deletion.
"""
import logging
import re
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import (
    IntegrityError,
    SQLAlchemyError,
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.auth.services.password_services import get_password_hash
from src.user.exceptions import (
    UserAlreadyExistsError,
    UserNotFoundError,
)
from src.user.models import User as UserModel
from src.user.schemas.user_schemas import (
    UserCreate as UserCreateSchema,
    UserUpdate as UserUpdateSchema,
)


logger = logging.getLogger(__name__)


async def get_user_by_id(db: AsyncSession, user_id: UUID) -> UserModel:
    """Retrieve a user by their ID.

    Args:
        db: Database session
        user_id: UUID of the user to retrieve

    Returns:
        User: The requested user

    Raises:
        UserNotFoundError: If no user exists with the given ID
    """
    user: UserModel | None = await db.get(entity=UserModel, ident=user_id)
    if not user:
        logger.warning(msg=f"User not found with ID: {user_id}")
        raise UserNotFoundError(identifier=user_id)

    logger.info(msg=f"Successfully retrieved user with ID: {user_id}")
    return user


async def get_user_by_email(
        *, db: AsyncSession, user_email: str
) -> UserModel:
    """Retrieve a user by their email address.

    Args:
        db: Database session
        user_email: Email of the user to retrieve

    Returns:
        User: The requested user

    Raises:
        UserNotFoundError: If no user exists with the given email
    """
    # Construct a select statement to find the user by email
    query = select(UserModel).where(UserModel.email == user_email)

    # Execute the statement and get the scalar result (one user or None)
    result = await db.execute(query)
    user: UserModel | None = result.scalar_one_or_none()

    if not user:
        logger.warning(msg=f"User not found with Email: {user_email}")
        raise UserNotFoundError(identifier=user_email, lookup_field="Email")

    logger.info(msg=f"Successfully retrieved user with Email: {user_email}")
    return user


async def get_user_for_auth_with_profile(
        db: AsyncSession, user_id: UUID
) -> UserModel:
    """Retrieve a user by ID with their base profile eagerly loaded.

    Intended for authentication flows where the full user object is needed.
    Returns None if user not found, allowing caller to raise specific auth
    exceptions.
    """
    stmt = (
        select(UserModel)
        .options(
            selectinload(UserModel.profile)  # Eagerly load BaseUserProfile
            # If ProfessionalProfileExtension should also be loaded
            # for /me endpoint eventually:
            # .selectinload(
            #     User.profile.of_type(BaseUserProfile).professional_extension
            # )
            # Or if using relationship name directly from BaseUserProfile:
            # .selectinload(User.profile).selectinload(
            #     BaseUserProfile.professional_extension
            # )
        )
        .where(UserModel.id == user_id)
    )
    result = await db.execute(stmt)
    user: UserModel | None = result.scalar_one_or_none()

    if not user:
        logger.warning(f"User {user_id} not found during auth flow fetch.")
        raise UserNotFoundError(identifier=user_id)

    logger.info(
        msg=f"Successfully retrieved user {user_id} "
            f"with profile for auth flow."
    )
    return user


async def create_user(
        *, db: AsyncSession, schema: UserCreateSchema
) -> UserModel:
    """Create a new user in the database.

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
    user = UserModel(
        email=schema.email,
        username=schema.username,
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
        await db.rollback()

        violated_field: str | None = None
        identifier_value: str | None = None

        # Attempt to parse the specific column from the error detail
        # DETAIL: Key (column_name)=(value) already exists.
        # Safely get detail string
        error_detail = str(e.orig).lower()
        match = re.search(
            pattern=r"key \((?P<column>\w+)\)=\(", string=error_detail
        )

        if match:
            column_name = match.group('column')

            # Check if the parsed column name corresponds to
            # a field we tried to update
            if column_name == 'username':
                violated_field = "Username"
                identifier_value = schema.username
            elif column_name == 'email':
                violated_field = "Email"
                identifier_value = schema.email

        # If we identified a specific field from
        # the detail AND it was in the update:
        if violated_field and identifier_value is not None:
            raise UserAlreadyExistsError(
                identifier=identifier_value,
                lookup_field=violated_field
            ) from e

        # Fallback: If parsing failed or didn't match update_data,
        # log and re-raise generic IntegrityError
        logger.error(
            msg="Integrity error during user update "
                "(constraint violation parsing failed or unrelated)",
            extra={
                "email": schema.email,
                "username": schema.username,
                "error": str(e),
                "detail": error_detail,  # Log the detail we tried to parse
            }
        )
        raise  # Re-raise original IntegrityError

    except SQLAlchemyError as e:
        await db.rollback()

        logger.error(
            msg="Database error during user update",
            extra={
                "email": schema.email,
                "username": schema.username,
                "error": str(e),
            }
        )
        raise


async def update_user(
        *, db: AsyncSession, user_id: UUID, schema: UserUpdateSchema
) -> UserModel:
    """Update an existing user's information.

    Args:
        db: Database session
        user_id: UUID of the user to update
        schema: Validated update data

    Returns:
        User: The updated user

    Raises:
        UserNotFoundError: If no user exists with the given ID
        UserAlreadyExistsError: If update violates unique constraints
        (email/username)
        SQLAlchemyError: If there's any other database error
    """
    # Get existing user
    user = await get_user_by_id(db=db, user_id=user_id)

    # Update user attributes if provided in schema
    update_data = schema.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)

    try:
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

    except IntegrityError as e:
        await db.rollback()

        violated_field: str | None = None
        identifier_value: str | None = None

        # Attempt to parse the specific column from the error detail
        # DETAIL: Key (column_name)=(value) already exists.
        # Safely get detail string
        error_detail = str(e.orig).lower()
        match = re.search(
            pattern=r"key \((?P<column>\w+)\)=\(", string=error_detail
        )

        if match:
            column_name = match.group('column')

            # Check if the parsed column name corresponds to
            # a field we tried to update
            if column_name == 'username' and 'username' in update_data:
                violated_field = "Username"
                identifier_value = update_data['username']
            elif column_name == 'email' and 'email' in update_data:
                violated_field = "Email"
                identifier_value = update_data['email']

        # If we identified a specific field from
        # the detail AND it was in the update:
        if violated_field and identifier_value is not None:
            raise UserAlreadyExistsError(
                identifier=identifier_value,
                lookup_field=violated_field
            ) from e

        # Fallback: If parsing failed or didn't match update_data,
        # log and re-raise generic IntegrityError
        logger.error(
            msg="Integrity error during user update "
                "(constraint violation parsing failed or unrelated)",
            extra={
                "user_id": str(user_id),
                "error": str(e),
                "detail": error_detail,  # Log the detail we tried to parse
                "updated_fields": list(update_data.keys())
            }
        )
        raise  # Re-raise original IntegrityError

    except SQLAlchemyError as e:
        await db.rollback()

        logger.error(
            msg="Database error during user update",
            extra={
                "user_id": str(user_id),
                "error": str(e),
                "updated_fields": list(update_data.keys())
            }
        )
        raise
