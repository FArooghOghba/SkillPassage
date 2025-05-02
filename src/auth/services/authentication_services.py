"""Authentication service module for verifying user credentials.

This module contains functions for handling user authentication using password
hashing and verification with bcrypt, as well as token-based authentication
using OAuth2.
"""
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.exceptions import NotAuthorizedError
from src.auth.services.password_services import verify_password
from src.user.exceptions import UserNotFoundError
from src.user.models import User
from src.user.services.user_services import get_user_by_email


logger = logging.getLogger(__name__)


async def authenticate_user(
        db: AsyncSession, email: str, password: str
) -> User:
    """Authenticate a user with email and password.

    Args:
        db: Database session for executing database operations
        email: User's email address
        password: User's plain text password to verify

    Returns:
        User: Authenticated user object if credentials are valid

    Raises:
        NotAuthorizedError: If credentials are invalid
        (wrong email or password)
    """
    # Handle None password case explicitly
    if password is None:
        logging.warning(
            msg="Authentication failed: password is None",
            extra={"email": email, "reason": "none_password"}
        )
        raise NotAuthorizedError('Invalid credentials')

    try:
        # Try to retrieve the user by email
        user = await get_user_by_email(db=db, user_email=email)

        # If user exists, verify password
        if not verify_password(
                plain_password=password, hashed_password=user.hashed_password
        ):
            logging.warning(
                msg="Authentication failed: invalid password",
                extra={
                    "user_id": str(user.id),
                    "email": email,
                    "username": user.username,
                    "reason": "invalid_password"
                }
            )
            raise NotAuthorizedError('Invalid credentials')

        # Authentication successful
        logging.info(
            msg="User authenticated successfully",
            extra={
                "user_id": str(user.id),
                "email": user.email
            }
        )
        return user

    except UserNotFoundError:
        # Convert UserNotFoundError to a generic NotAuthorizedError
        # to avoid revealing whether the email exists or not
        logging.warning(
            msg="Authentication failed: user not found",
            extra={
                "email": email,
                "reason": "user_not_found"
            }
        )
        raise NotAuthorizedError('Invalid credentials')
