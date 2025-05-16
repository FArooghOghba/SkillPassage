"""This module provides dependencies for authentication and authorization.

It includes functions and classes that handle user authentication,
token verification, and access control for protected routes.
The dependencies are designed to be used with FastAPI's dependency
injection system, enabling seamless integration with API endpoints.
"""
import logging
from typing import Annotated

from fastapi import (
    Depends,
    HTTPException,
    status,
)
from fastapi.security import OAuth2PasswordBearer

from src.auth.exceptions import (
    NotAuthorizedError,
    TokenError,
)
from src.auth.schemas import TokenPayload
from src.auth.services.token_services import verify_access_token
from src.db.session import DBAsyncSession
from src.user.exceptions import UserNotFoundError
from src.user.models import User
from src.user.services.user_services import get_user_by_id


logger = logging.getLogger(__name__)


USER_AUTH_LOGIN_URL = "/api/v1/auth/login"

# OAuth2 scheme for token extraction from requests
oauth2_bearer = OAuth2PasswordBearer(tokenUrl=USER_AUTH_LOGIN_URL)


async def get_current_user(
        db: DBAsyncSession,
        token: Annotated[str, Depends(oauth2_bearer)]
) -> User:
    """Authenticate a user from a given Bearer token.

    Args:
        db: The database session to use for the authentication.
        token: The Bearer token to authenticate the user with.

    Returns:
        User: The authenticated user object, or None if
        the authentication fails.

    Raises:
        HTTPException: If the authentication fails, with a
        401 Unauthorized status code.
    """
    # Create an exception instance to raise if any sub-step fails
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # Verify the given token and extract its payload
        token_payload: TokenPayload = await verify_access_token(token)
    except (TokenError, NotAuthorizedError) as e:
        logger.warning(f"Token validation failed: {str(e)}")
        raise credentials_exception from e

    # Extract the user ID from the token payload
    user_id_from_token = token_payload.sub

    try:
        # Retrieve the user from the database by ID
        user = await get_user_by_id(db=db, user_id=user_id_from_token)
    except UserNotFoundError:
        logger.warning(
            f"User ID {user_id_from_token} from token not found in DB."
        )
        raise credentials_exception from None

    # Return the authenticated user object
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
