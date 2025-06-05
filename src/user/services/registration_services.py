"""Registration service for handling complete user registration flow."""
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from src.user.models import User
from src.user.schemas.user_base_profile_schemas import UserBaseProfileCreate
from src.user.schemas.user_schemas import UserCreate
from src.user.services.user_profile_services import create_user_profile
from src.user.services.user_services import create_user


logger = logging.getLogger(__name__)


async def register_user(
    db: AsyncSession,
    user_schema: UserCreate,
    profile_schema: UserBaseProfileCreate,
) -> User:
    """Register a new user with complete profile.

    This function handles the full user registration process, including:
    - Creating the base user
    - Setting up initial profile
    - Any additional registration steps
    (e.g., welcome email, initial settings)

    The entire registration process is wrapped in a transaction to ensure
    atomicity - if any part fails, all changes are rolled back.

    Args:
        db: Database session for executing database operations
        user_schema: Validated user registration data containing
        email, username, password
        profile_schema: Validated profile creation data containing
        personal information

    Returns:
        User: The newly registered user object with all fields populated

    Raises:
        UserAlreadyExistsError: If user with same email/username
        already exists
        SQLAlchemyError: If there's any database error during
        the registration process
        ValueError: If profile creation fails with validation errors
    """
    # Use transaction to ensure atomicity
    # if any part fails, all changes are rolled back
    async with db.begin_nested():
        # Create the base user account with credentials
        user = await create_user(
            db=db,
            schema=user_schema
        )

        # Create the user profile with personal information
        await create_user_profile(
            db=db,
            user_id=user.id,
            schema=profile_schema
        )

        await db.refresh(user, attribute_names=['profile'])

        # Here you can add additional registration steps
        # For example:
        # await send_welcome_email(user.email)
        # await setup_initial_settings(db=db, user=user)

        logger.info(
            msg=f"Completed registration for user with Email: {user.email}",
            extra={
                "email": user.email,
                "user_id": str(user.id),
            }
        )
        return user
