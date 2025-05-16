"""Tests for the src.auth.dependencies module.

This module contains tests for the get_current_user dependency function.
"""
from datetime import (
    datetime,
    timezone,
)
from unittest.mock import AsyncMock
from uuid import UUID

import pytest
from fastapi import (
    HTTPException,
    status,
)
from pytest import MonkeyPatch

from src.auth.dependencies import get_current_user
from src.auth.exceptions import (
    NotAuthorizedError,
    TokenError,
)
from src.auth.schemas import TokenPayload
from src.core.config import auth_settings
from src.user.exceptions import UserNotFoundError
from src.user.models import User


# Mocking the DBAsyncSession - for unit tests,
# we don't need a real DB connection
# if we mock the services that use it.
MockDBAsyncSession = AsyncMock()


@pytest.mark.asyncio
class TestGetCurrentUser:

    async def test_dep_get_current_user_with_valid_token_user_return_success(
            self,
            monkeypatch: MonkeyPatch,
            first_test_token: str,
            first_test_client_user: User,
    ) -> None:
        """
        Test get_current_user with a valid token and existing user.

        This test ensures that get_current_user returns the expected user
        when given a valid token and an existing user.

        Mocking is used to isolate the dependency and ensure that
        the dependency function will return the expected user.

        :param monkeypatch: A pytest fixture for monkeypatching.
        :param first_test_token: A valid token fixture.
        :param first_test_client_user: An existing user fixture.
        :return: None
        """
        # Create a mock object for the verify_access_token function.
        # This mock will simulate the behavior of the actual function.
        mock_verify = AsyncMock()

        # Prepare the expected token payload structure.
        # The token should have a 'sub' (subject) attribute matching
        # the user's ID.
        test_user_id = first_test_client_user.id
        now = datetime.now(timezone.utc)  # Current time in UTC.
        expire = now + auth_settings.access_token_expire_delta

        mock_verify.return_value = TokenPayload(
            sub=test_user_id, iat=now, exp=expire
        )

        # Use monkeypatch to replace the actual verify_access_token function
        # with the mock object within the test scope.
        monkeypatch.setattr(
            target="src.auth.dependencies.verify_access_token",
            name=mock_verify
        )

        # Create a mock object for the get_user_by_id function.
        # This mock will return the first_test_client_user when called.
        mock_get_user = AsyncMock(return_value=first_test_client_user)
        monkeypatch.setattr(
            target="src.auth.dependencies.get_user_by_id",
            name=mock_get_user
        )

        # Call get_current_user with a mocked database session and token.
        # The function is expected to return the user associated
        # with the token.
        user = await get_current_user(
            db=MockDBAsyncSession, token=first_test_token
        )

        # Verify that the returned user is not None and
        # matches the expected user.
        assert user is not None
        assert user.id == first_test_client_user.id
        assert user.email == first_test_client_user.email

        # Ensure that verify_access_token was called exactly once
        # with the test token.
        mock_verify.assert_awaited_once_with(first_test_token)

        # Ensure that get_user_by_id was called exactly once with
        # the correct parameters.
        mock_get_user.assert_awaited_once_with(
            db=MockDBAsyncSession, user_id=test_user_id
        )

    async def test_dep_get_current_user_with_expired_token_return_error(
        self,
        monkeypatch: MonkeyPatch,
        first_test_expired_token: str,
    ) -> None:
        """Test get_current_user with an expired token.

        This test verifies that the get_current_user dependency
        correctly handles expired tokens.

        This test verifies that:
        - Expired tokens are rejected
        - Correct error type is raised
        - Error message indicates expiration
        """
        # Mock verify_access_token to raise an exception
        # when called with the expired token.
        # The exception raised is a NotAuthorizedError with
        # a message indicating that the token has expired.
        mock_verify = AsyncMock(
            side_effect=NotAuthorizedError("Token has expired")
        )

        # Use monkeypatch to replace the actual verify_access_token function
        # with the mock object within the test scope.
        monkeypatch.setattr(
            target="src.auth.dependencies.verify_access_token",
            name=mock_verify
        )

        # Call get_current_user with a mocked database session and
        # the expired token.
        # The function is expected to raise an HTTPException.
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(
                db=MockDBAsyncSession, token=first_test_expired_token
            )

        # Verify that the raised exception is an HTTPException
        # with the correct status code and detail.
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert exc_info.value.detail == "Could not validate credentials"

        # Verify that verify_access_token was called exactly once
        # with the expired token.
        mock_verify.assert_awaited_once_with(first_test_expired_token)

    async def test_dep_get_current_user_with_malformed_token_return_error(
        self,
        monkeypatch: MonkeyPatch,
        first_test_token: str,
    ) -> None:
        """Test that get_current_user returns an error with a malformed token.

        This test verifies that the get_current_user function correctly raises
        an HTTPException when it is provided with a malformed token.
        The test ensures that the raised exception has the correct
        status code and detail.
        Additionally, it checks that the verify_access_token function is
        called exactly once with the malformed token.

        :param monkeypatch: A pytest fixture for monkeypatching, used to
            replace parts of the system under test with mock objects.
        :param first_test_token: A valid token fixture used to simulate
        a malformed token.
        """
        # Use an obviously invalid token
        malformed_token = "this-is-not-a-valid-jwt-token"

        # Create an AsyncMock for the verify_access_token function,
        # set to raise a TokenError
        # This simulates the behavior of the function when a malformed
        # token is provided
        mock_verify = AsyncMock(side_effect=TokenError("Invalid token"))

        # Use monkeypatch to replace the verify_access_token function
        # in the test scope with the mock object created above
        monkeypatch.setattr(
            target="src.auth.dependencies.verify_access_token",
            name=mock_verify
        )

        # Use pytest.raises to assert that an HTTPException is raised
        # when get_current_user is called with the mocked database session
        # and the malformed token
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(
                db=MockDBAsyncSession, token=malformed_token
            )

        # Verify that the exception raised is an HTTPException with the
        # expected status code
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED

        # Verify that the exception detail message is as expected
        assert exc_info.value.detail == "Could not validate credentials"

        # Ensure that verify_access_token was called exactly once with
        # the malformed token
        mock_verify.assert_awaited_once_with(malformed_token)

    async def test_dep_get_current_user_token_with_missing_sub_return_error(
        self,
        monkeypatch: MonkeyPatch,
        first_test_token: str,
    ) -> None:
        """Test get_current_user with a token missing the 'sub' claim.

        This test verifies that the get_current_user function correctly raises
        an HTTPException when it is provided with a token that is missing the
        'sub' claim.

        The test ensures that the raised exception has the correct
        status code and detail.
        Additionally, it checks that the verify_access_token function is
        called exactly once with the token missing the 'sub' claim.

        The test works as follows:

        1. A token is created with the 'sub' claim removed.
        2. The verify_access_token function is replaced with a mock
           object that raises a TokenError when called.
        3. The get_current_user function is called with the mocked
           database session and the token missing the 'sub' claim.
        4. The test asserts that an HTTPException is raised with the
           correct status code and detail.
        5. The test asserts that the verify_access_token function was
           called exactly once with the token missing the 'sub' claim.

        :param monkeypatch: A pytest fixture for monkeypatching, used to
            replace parts of the system under test with mock objects.
        :param first_test_token: A valid token fixture used to simulate
        a token missing the 'sub' claim.
        """
        token_missing_sub_claim = "token-placeholder-missing-sub-claim"

        # Create an AsyncMock for the verify_access_token function,
        # set to raise a TokenError when called
        mock_verify = AsyncMock(
            side_effect=TokenError("Invalid token format")
        )

        # Use monkeypatch to replace the verify_access_token function
        # in the test scope with the mock object created above
        monkeypatch.setattr(
            target="src.auth.dependencies.verify_access_token",
            name=mock_verify
        )

        # Use pytest.raises to assert that an HTTPException is raised
        # when get_current_user is called with the mocked database session
        # and the token missing the 'sub' claim
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(
                db=MockDBAsyncSession, token=token_missing_sub_claim
            )

        # Verify that the exception raised is an HTTPException with the
        # expected status code
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED

        # Verify that the exception detail message is as expected
        assert exc_info.value.detail == "Could not validate credentials"

        # Ensure that verify_access_token was called exactly once with
        # the token missing the 'sub' claim
        mock_verify.assert_awaited_once_with(token_missing_sub_claim)

    async def test_dep_get_current_user_and_user_not_found_in_db_return_error(
        self,
        monkeypatch: MonkeyPatch,
        first_test_token: str,
        first_test_user_id: UUID
    ) -> None:
        """Test that get_current_user returns an error with a 401 status code.

        The detail "Could not validate credentials" when the user is not found
        in the database.

        This test verifies that the get_current_user dependency correctly
        handles the case where the access token is valid but the user is
        not found in the database.

        It verifies that the HTTPException is raised with the expected status
        code and detail message. It also checks that the verify_access_token
        and get_user_by_id functions are called exactly once with the correct
        arguments.

        The test works as follows:

        1. A valid token fixture is used to simulate a token that is valid
           but for which the user is not found in the database.
        2. The verify_access_token function is replaced with a mock that
           returns a valid token payload when called with the above token.
        3. The get_user_by_id function is replaced with a mock that raises a
           UserNotFoundError when called with the user ID from the token.
        4. The test asserts that an HTTPException is raised with the expected
           status code and detail message.
        5. The test asserts that the verify_access_token and get_user_by_id
           functions were called exactly once with the correct arguments.
        """
        # A valid token fixture is used to simulate a token that is valid
        # but for which the user is not found in the database.
        mock_verify = AsyncMock()

        # The verify_access_token function is replaced with a mock that
        # returns a valid token payload when called with the above token.
        now = datetime.now(timezone.utc)
        expire = now + auth_settings.access_token_expire_delta
        mock_verify.return_value = TokenPayload(
            sub=first_test_user_id, iat=now, exp=expire
        )

        monkeypatch.setattr(
            target="src.auth.dependencies.verify_access_token",
            name=mock_verify
        )

        # The get_user_by_id function is replaced with a mock that raises a
        # UserNotFoundError when called with the user ID from the token.
        mock_get_user = AsyncMock(
            side_effect=UserNotFoundError(identifier=first_test_user_id)
        )
        monkeypatch.setattr(
            target="src.auth.dependencies.get_user_by_id",
            name=mock_get_user
        )

        # The test asserts that an HTTPException is raised with the expected
        # status code and detail message.
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(
                db=MockDBAsyncSession, token=first_test_token
            )

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert exc_info.value.detail == "Could not validate credentials"

        # The test asserts that the verify_access_token and get_user_by_id
        # functions were called exactly once with the correct arguments.
        mock_verify.assert_awaited_once_with(first_test_token)
        mock_get_user.assert_awaited_once_with(
            db=MockDBAsyncSession, user_id=first_test_user_id
        )
