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

from src.auth.dependencies import CurrentActiveUser
from src.db.session import DBAsyncSession
from src.user.exceptions import (
    UserAlreadyExistsError,
    UserNotFoundError,
)
from src.user.schemas.user_profile_schemas import (
    UserProfile as UserProfileSchema,
    UserProfileCreate as UserProfileCreateSchema,
)
from src.user.schemas.user_registration_schema import RegisterUserRequest
from src.user.schemas.user_schemas import (
    User as UserSchema,
    UserCreate as UserCreateSchema,
)
from src.user.services.registration_services import register_user
from src.user.services.user_profile_services import get_user_profile_by_user_id


logger = logging.getLogger(__name__)


router = APIRouter(
    prefix='/user',
    tags=['user']
)


@router.post(
    path="/registration",
    response_model=UserSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Register new user",
    description="Creates a new user account with profile information",
    responses={
        status.HTTP_201_CREATED: {
            "description": "User successfully registered", "model": UserSchema
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
) -> UserSchema:
    """Endpoint to register a new user and their profile.

    Handles request validation, calls the registration service,
    and manages specific exceptions like duplicate users.
    """
    try:
        # Create UserCreate instance from the request data
        user_schema = UserCreateSchema.model_validate(request_data)

        # Create UserProfileCreate instance from the request data
        profile_schema = UserProfileCreateSchema.model_validate(request_data)

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


@router.get(
    path="/me",
    response_model=UserProfileSchema,
    status_code=status.HTTP_200_OK,
    summary="Get current authenticated user's profile",
    description="""
        Retrieves the profile information for the currently authenticated and
        active user. This endpoint uses the dependency injection mechanism to
        ensure that the current user is active. If the user is inactive, a
        403 Forbidden response with a detail message indicating the account is
        inactive will be returned.
    """,
    responses={
        status.HTTP_200_OK: {
            "description": "User profile information retrieved successfully.",
            "model": UserProfileSchema
        },
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Authentication required."
        },
        status.HTTP_403_FORBIDDEN: {
            "description": "User account is inactive."
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "User profile not found."
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "description": "Internal server error."
        }
    }
)
async def get_user_profile_endpoint(
        db: DBAsyncSession,
        current_user: CurrentActiveUser,
) -> UserProfileSchema:
    """Retrieves the profile for the currently authenticated and active user.

    Args:
        db: Database session
        current_user: The authenticated and active user instance

    Returns:
        UserProfileSchema: The retrieved user profile information

    Raises:
        HTTPException: In the case of unexpected errors, or if
        the user is inactive.
    """
    try:
        logger.debug(
            msg=f"Attempting to get user profile "
                f"for user ID: {current_user.id}"
        )

        # Get the user profile by the current user's ID
        user_profile = await get_user_profile_by_user_id(
            db=db, user_id=current_user.id
        )

        # Log the successful retrieval of the user profile
        logger.info(
            msg=f"Successfully retrieved user profile for "
            f"user ID: {current_user.id}"
        )
        return user_profile  # type: ignore[return-value]

    except UserNotFoundError as e:
        # Log the occurrence of a UserNotFoundError
        logger.warning(
            msg=f"User profile not found for "
                f"user: {current_user.id}: {e.detail}"
        )
        # Raise an HTTPException with a 404 Not Found status code
        # and the detail message from the UserNotFoundError
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.detail
        ) from e
    except Exception as e:
        # Log the occurrence of any other unexpected error
        logger.error(
            msg=f"Unexpected error retrieving profile for "
                f"user ID {current_user.id}: {e}",
            exc_info=True
        )
        # Raise an HTTPException with a 500 Internal Server Error
        # status code and a detail message indicating an unexpected error
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while retrieving "
                   "the user profile.",
        ) from e
