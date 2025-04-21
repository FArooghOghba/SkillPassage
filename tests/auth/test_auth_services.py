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

from src.auth.exceptions import (
    NotAuthorizedError,
    TokenError,
)
from src.auth.services import (
    create_access_token,
    get_password_hash,
    verify_access_token,
    verify_password,
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
        expired_token = create_access_token(
            user_id=first_test_user_id,
            expires_delta=timedelta(microseconds=1)
        )
        # Wait for token to expire
        import asyncio
        await asyncio.sleep(1)

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
