"""Authentication service module for verifying user credentials.

This module contains functions for handling user authentication using password
hashing and verification with bcrypt, as well as token-based authentication
using OAuth2.
"""
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.exceptions import NotAuthorizedError
from src.auth.schemas import (
    EmailPasswordLoginRequest,
    Token,
)
from src.auth.services.password_services import verify_password
from src.auth.services.token_services import create_access_token
from src.core.config import auth_settings
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
        # get_user_by_email raises UserNotFoundError on any failure
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

        if not user.is_active:
            logging.warning(
                msg=f"Authentication failed: User {email} is inactive.",
                extra={
                    "user_id": str(user.id),
                    "email": email,
                    "username": user.username,
                    "reason": "inactive_password"
                }
            )
            raise NotAuthorizedError("User account is inactive")

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


async def login_for_access_token(
        db: AsyncSession,
        login_request_schema: EmailPasswordLoginRequest
) -> Token:
    """Handles login request and returns an access token.

    Args:
        db: Database session for executing database operations
        login_request_schema: EmailPasswordLoginRequest schema
        containing email and password

    Returns:
        Token: Token response schema instance with access token
        and expiration time

    Raises:
        NotAuthorizedError: If authentication fails due to invalid credentials
    """
    login_form_email = login_request_schema.email
    login_form_password = login_request_schema.password

    # authenticate_user raises NotAuthorizedError on any failure
    user = await authenticate_user(
        db=db, email=login_form_email, password=login_form_password
    )

    # Get expiration delta from settings
    expires_delta = auth_settings.access_token_expire_delta

    # Create the token string
    token = create_access_token(
        user_id=user.id,
        expires_delta=expires_delta
    )

    logger.info(
        msg=f"Completed logged in for user with Email: {user.email}",
        extra={
            "email": user.email,
            "user_id": str(user.id),
        }
    )

    # Create and return the Token response schema instance
    return Token(
        access_token=token,
        token_type="bearer",  # Default is handled by schema, explicit is ok
        expires_in=int(expires_delta.total_seconds())
        # refresh_token=... # Add later if needed
    )
