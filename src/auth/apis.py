"""This module defines the API routes related to user operations.

It includes the necessary imports and sets up the APIRouter
for handling user-related requests. It also imports and handles
specific exceptions related to user operations, such as when
a user already exists. The module is part of the application's
user management functionality, interacting with the database
and user schemas for registration and profile creation.
"""
import logging

from fastapi import (
    APIRouter,
    HTTPException,
    status,
)

from src.auth.exceptions import NotAuthorizedError
from src.auth.schemas import (
    EmailPasswordLoginRequest,
    Token,
)
from src.auth.services.authentication_services import login_for_access_token
from src.db.session import DBAsyncSession


logger = logging.getLogger(__name__)


router = APIRouter(
    prefix='/auth',
    tags=['Authentication']
)


@router.post(
    path="/login",
    response_model=Token,
    status_code=status.HTTP_200_OK,
    summary="Login for Access Token",
    description=(
        "Authenticate using email and password to obtain an access token."
    ),
    responses={
        status.HTTP_200_OK: {
            "description": "Authentication successful, token issued",
            "model": Token
        },
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Incorrect email, password, or inactive user"
        },
        status.HTTP_422_UNPROCESSABLE_ENTITY: {
             "description": "Validation Error (e.g., invalid email format)"
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "description": "Internal server error during login"
        }
    }
)
async def login_endpoint(
        db: DBAsyncSession, request_data: EmailPasswordLoginRequest,
) -> Token:
    """Endpoint to authenticate a user and issue an access token.

    This endpoint allows users to authenticate using their email and password.
    Upon successful authentication, an access token is generated and returned
    to the client. The token can be used to access protected endpoints.

    Args:
        db: An asynchronous database session instance.
        request_data: A request schema containing the user's email
        and password.

    Returns:
        Token: An object containing the access token and related information.

    Raises:
        HTTPException: If authentication fails due to incorrect credentials
                       or if an unexpected error occurs during the process.
    """
    try:
        logger.debug(f"Attempting to login user: {request_data.email}")

        created_token = await login_for_access_token(
            db=db,
            login_request_schema=request_data
        )

        logger.info(f"Successfully logged in user: {request_data.email}")

        return created_token

    except NotAuthorizedError as e:
        logger.warning(
            msg=f"Login failed for {request_data.email}: {e.detail}"
        )

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=e.detail,
            headers={"WWW-Authenticate": "Bearer"},
        ) from e
    except Exception as e:
        logger.error(
            msg=f"Unexpected error during login for "
                f"{request_data.email}: {e}",
            exc_info=True
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during login.",
        ) from e
