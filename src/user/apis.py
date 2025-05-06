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

from src.db.session import DBAsyncSession
from src.user.exceptions import UserAlreadyExistsError
from src.user.schemas.user_profile_schemas import UserProfileCreate
from src.user.schemas.user_registration_schema import RegisterUserRequest
from src.user.schemas.user_schemas import (
    User,
    UserCreate,
)
from src.user.services.registration_services import register_user


logger = logging.getLogger(__name__)


router = APIRouter(
    prefix='/user',
    tags=['user']
)


@router.post(
    path="/registration",
    response_model=User,
    status_code=status.HTTP_201_CREATED,
    summary="Register new user",
    description="Creates a new user account with profile information",
    responses={
        status.HTTP_201_CREATED: {
            "description": "User successfully registered", "model": User
        },
        status.HTTP_409_CONFLICT: {
            "description": "Email or username already registered"
        },
        status.HTTP_422_UNPROCESSABLE_ENTITY: {
            "description": "Validation Error "
                           "(e.g., invalid email format, password too short)"
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "description": "Internal server error"
        }
    }
)
async def register_user_endpoint(
        db: DBAsyncSession, request_data: RegisterUserRequest,
) -> User:
    """Endpoint to register a new user and their profile.

    Handles request validation, calls the registration service,
    and manages specific exceptions like duplicate users.
    """
    try:
        # Create UserCreate instance from the request data
        user_schema = UserCreate.model_validate(request_data)

        # Create UserProfileCreate instance from the request data
        profile_schema = UserProfileCreate.model_validate(request_data)

        logger.debug(f"Attempting to register user: {request_data.email}")

        # Call the core registration service
        created_user = await register_user(
            db=db,
            user_schema=user_schema,
            profile_schema=profile_schema
        )

        # Commit the transaction if service succeeded (IMPORTANT!)
        # If register_user raises an exception, commit won't happen
        # and exception handlers below (or FastAPI's) should trigger rollback.
        await db.commit()

        logger.info(f"Successfully registered user: {created_user.email}")

        # Return the created User ORM model instance.
        # FastAPI will automatically serialize it based
        # on `response_model=User`.
        return created_user  # type: ignore[return-value]

    except UserAlreadyExistsError as e:
        # No need to rollback here, exception occurred before commit
        logger.warning(
            msg=f"Registration conflict for {request_data.email}: {e.detail}"
        )
        # Re-raise as HTTPException 409
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=e.detail  # Use detail from the custom exception
        ) from e
    except Exception as e:
        # Catch any other unexpected errors from the service layer or commit
        # Rollback in case the error happened during commit
        logger.error(
            msg=f"Unexpected error during registration for "
                f"{request_data.email}: {e}",
            exc_info=True
        )
        await db.rollback()  # Explicit rollback on general failure
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during registration.",
        ) from e
