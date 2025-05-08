"""Unit tests for authentication services."""
from datetime import (
    datetime,
    timedelta,
    timezone,
)
from uuid import UUID

import pytest
from faker import Faker
from jose import jwt
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.exceptions import (
    NotAuthorizedError,
    TokenError,
)
from src.auth.services.authentication_services import authenticate_user
from src.auth.services.password_services import (
    get_password_hash,
    verify_password,
)
from src.auth.services.token_services import (
    create_access_token,
    verify_access_token,
)
from src.core.config import auth_settings


class TestPasswordHashing:
    """Test suite for password hashing functions.

    Verifies the security and correctness of password hashing operations.
    """

    def test_service_get_password_hash(self) -> None:
        """Test password hashing and verification workflow.

        Ensures:
        - Hashed password differs from original
        - Correct password verifies successfully
        - Incorrect password fails verification
        """
        password = Faker().password()
        hashed_password = get_password_hash(password=password)

        assert hashed_password != password
        assert verify_password(
            plain_password=password, hashed_password=hashed_password
        )
        assert not verify_password(
            plain_password="wrong_password", hashed_password=hashed_password
        )


@pytest.mark.asyncio
class TestTokenOperations:
    """Test suite for JWT token operations.

    Verifies token creation, validation, and error handling scenarios.
    """

    def test_service_create_access_token_return_success(
            self, first_test_user_id: UUID
    ) -> None:
        """Test JWT access token creation.

        Verifies:
        - Token is created successfully
        - Required claims are present
        - Claims have correct values
        """
        expires_delta = timedelta(minutes=30)
        token = create_access_token(
            user_id=first_test_user_id, expires_delta=expires_delta
        )

        # Decode token to verify contents
        payload = jwt.decode(
            token=token,
            key=auth_settings.JWT_SECRET_KEY,
            algorithms=[auth_settings.JWT_ALGORITHM]
        )

        assert payload["sub"] == str(first_test_user_id)
        assert "exp" in payload
        assert "iat" in payload

    async def test_service_verify_valid_token_return_success(
            self, fixt_test_token: str
    ) -> None:
        """Test successful token verification.

        Verifies:
        - Valid token is accepted
        - User ID is correctly extracted
        """
        result = await verify_access_token(fixt_test_token)
        assert "id" in result
        assert UUID(result["id"])

    async def test_service_verify_expired_token_return_error(
            self, first_test_user_id: UUID
    ) -> None:
        """Test expired token handling.

        Verifies:
        - Expired tokens are rejected
        - Correct error type is raised
        - Error message indicates expiration
        """
        # Negative delta = already expired
        expired_token = create_access_token(
            user_id=first_test_user_id,
            expires_delta=timedelta(seconds=-1)
        )

        with pytest.raises(NotAuthorizedError) as exc_info:
            await verify_access_token(expired_token)
        assert "expired" in str(exc_info.value.detail)

    async def test_service_verify_invalid_token_return_error(self) -> None:
        """Test invalid token handling.

        Verifies:
        - Malformed tokens are rejected
        - Correct error type is raised
        """
        with pytest.raises(TokenError) as exc_info:
            await verify_access_token("invalid.token.string")

        assert "Invalid token" in str(exc_info.value.detail)

    async def test_service_verify_token_missing_sub_return_error(
            self
    ) -> None:
        """Test token with missing subject claim.

        Verifies:
        - Tokens without 'sub' claim are rejected
        - Correct error type is raised
        """
        exp = datetime.now(timezone.utc) + timedelta(minutes=30)

        # Create token without 'sub' claim
        token = jwt.encode(
            claims={"exp": exp},  # Far future expiration
            key=auth_settings.JWT_SECRET_KEY,
            algorithm=auth_settings.JWT_ALGORITHM
        )

        with pytest.raises(TokenError) as exc_info:
            await verify_access_token(token)
        assert "Invalid token format" in str(exc_info.value.detail)


@pytest.mark.asyncio
class TestAuthenticationService:
    """Test suite for authentication service.

    This class contains tests that verify the behavior of the authentication
    service function under various scenarios including successful
    authentication with valid credentials.
    """

    async def test_service_authentication_user_return_success(
            self, db_session: AsyncSession,
            first_test_user_login_payload: dict[str, str]
    ) -> None:
        """
        Test successful user authentication.

        Verifies that a user can be successfully authenticated with valid
        credentials.

        Args:
            db_session: Async SQLAlchemy session for database operations.
            first_test_user_login_payload: Test user login data dictionary
        """
        user_email = first_test_user_login_payload["email"]
        user_password = first_test_user_login_payload["password"]

        user = await authenticate_user(
            db=db_session,
            email=user_email,
            password=user_password,
        )
        assert user is not None
        assert user.email == user_email

    @pytest.mark.parametrize(
        "invalid_password,expected_error",
        [
            # Empty password
            ("", "Invalid credentials"),
            # Password is too short
            ("short", "Invalid credentials"),
            # Password contains a space
            (" ", "Invalid credentials"),
            # Password contains a common password
            ("password123", "Invalid credentials"),
            # Wrong password
            ("completely_wrong_password", "Invalid credentials"),
            # Password is None
            (None, "Invalid credentials"),
        ],
        ids=["empty", "short", "space", "common", "wrong", "none"]
    )
    async def test_service_authentication_user_with_invalid_pass_return_error(
            self, db_session: AsyncSession,
            first_test_user_login_payload: dict[str, str],
            invalid_password: str, expected_error: str
    ) -> None:
        """Test authentication fails with invalid password.

        Verifies that authentication fails with different types of invalid
        passwords, such as empty password, short password, password with a
        space, common password, and wrong password.

        Args:
            db_session: Async SQLAlchemy session for database operations.
            first_test_user_login_payload: Test user login data dictionary
            invalid_password: Password to test
            expected_error: Expected error message
        """
        user_email = first_test_user_login_payload["email"]
        user_password = invalid_password

        with pytest.raises(NotAuthorizedError) as exc_info:
            await authenticate_user(
                db=db_session,
                email=user_email,
                password=user_password,
            )

        assert str(exc_info.value.detail) == expected_error

    async def test_service_authentication_nonexistent_user_return_error(
            self, db_session: AsyncSession,
    ) -> None:
        """Test authentication fails with non-existent email.

        Verifies:
        - Authentication with email that doesn't exist in the database
          raises appropriate error
        - Error message is generic to prevent user enumeration
        """
        non_existent_email = "nonexistent_user@example.com"
        user_password = "any_password"

        with pytest.raises(NotAuthorizedError) as exc_info:
            await authenticate_user(
                db=db_session,
                email=non_existent_email,
                password=user_password,
            )

        assert str(exc_info.value.detail) == (
            "Invalid credentials"
        )

    async def test_service_authentication_inactive_user_return_error(
            self, db_session: AsyncSession,
            first_test_inactive_user_login_payload: dict[str, str]
    ) -> None:
        """Test authentication fails with inactive user.

        Verifies:
        - Authentication with inactive user raises appropriate error
        - Error message is generic to prevent user enumeration
        """
        user_email = first_test_inactive_user_login_payload["email"]
        user_password = first_test_inactive_user_login_payload["password"]

        with pytest.raises(NotAuthorizedError) as exc_info:
            await authenticate_user(
                db=db_session,
                email=user_email,
                password=user_password,
            )

        assert str(exc_info.value.detail) == (
            "User account is inactive"
        )
