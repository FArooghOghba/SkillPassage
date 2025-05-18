from typing import (
    Callable,
    Dict,
)

import pytest
from fastapi import status
from httpx import AsyncClient

from src.user.models import (
    User as UserModel,
    UserProfile as UserProfileModel,
)
from src.user.schemas.user_profile_schemas import UserProfile as ProfileSchema


USER_PROFILE_ME_URL = "/api/v1/user/me"


@pytest.mark.asyncio
class TestGetCurrentUserProfileAPI:

    async def test_api_get_me_current_user_return_success(
            self,
            client: AsyncClient,
            first_test_client_user: UserModel,
            first_test_client_profile: UserProfileModel,
            auth_headers_for_user: Callable[[UserModel], Dict[str, str]]
    ) -> None:
        """
        Test GET /me for the current authenticated user.

        Checks that the successful response contains the expected data.

        Args:
            client: The HTTP client fixture
            first_test_client_user: The test user fixture
            first_test_client_profile: The test user profile fixture
            auth_headers_for_user: The fixture that generates auth headers
        """
        headers = auth_headers_for_user(first_test_client_user)

        response = await client.get(
            url=USER_PROFILE_ME_URL, headers=headers
        )

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()

        # Validate against the Pydantic UserProfile schema
        profile = ProfileSchema(**response_data)

        assert profile.id == first_test_client_profile.id
        assert profile.user_id == first_test_client_user.id
        assert profile.first_name == first_test_client_profile.first_name
        assert profile.last_name == first_test_client_profile.last_name
        assert profile.phone_number == first_test_client_profile.phone_number
        assert profile.role == first_test_client_profile.role

    async def test_api_get_me_current_user_unauthenticated_return_error(
            self, client: AsyncClient
    ) -> None:
        """
        Test GET /me when the client is not authenticated.

        Verifies that a 401 Unauthorized response is returned when
        the client is not authenticated.

        Args:
            client: The HTTP client fixture
        """
        response = await client.get(url=USER_PROFILE_ME_URL)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

        response_data = response.json()
        assert response_data["detail"] == "Not authenticated"

    async def test_api_get_me_current_user_with_invalid_token_return_error(
            self, client: AsyncClient
    ) -> None:
        """
        Test GET /me when the authenticated user has an invalid token.

        Verifies that a 401 Unauthorized response is returned when
        the client is authenticated with an invalid token.

        Args:
            client: The HTTP client fixture
        """
        headers = {"Authorization": "Bearer this.is.an.invalid.token"}

        response = await client.get(url=USER_PROFILE_ME_URL, headers=headers)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

        response_data = response.json()
        assert response_data["detail"] == "Could not validate credentials"

    async def test_api_get_me_current_inactive_user_return_error(
            self,
            client: AsyncClient,
            first_test_client_user: UserModel,
            first_test_client_profile: UserProfileModel,
            auth_headers_for_user: Callable[[UserModel], Dict[str, str]]
    ) -> None:
        """
        Test GET /me for inactive user returns error.

        Verifies that a 403 Forbidden response is returned when
        the client is authenticated as an inactive user.

        Args:
            client: The HTTP client fixture.
            first_test_client_user: The test user fixture, marked as inactive.
            first_test_client_profile: The test user profile fixture.
            auth_headers_for_user: The fixture to generate auth headers.

        Raises:
            AssertionError: If the response status code is not 403, or if
            the response data does not match the expected values.
        """
        first_test_client_user.is_active = False
        inactive_user = first_test_client_user
        headers = auth_headers_for_user(inactive_user)

        response = await client.get(url=USER_PROFILE_ME_URL, headers=headers)
        assert response.status_code == status.HTTP_403_FORBIDDEN

        response_data = response.json()
        assert response_data["detail"] == "User account is inactive."

    async def test_api_get_me_current_user_exists_but_no_profile_return_error(
            self,
            client: AsyncClient,
            first_test_client_user: UserModel,
            auth_headers_for_user: Callable[[UserModel], Dict[str, str]]
    ) -> None:
        """
        Test GET /me for a user that exists but has no profile.

        Verifies that a 404 Not Found response is returned when
        the client is authenticated as a user who exists in the
        system but does not have an associated user profile.

        Args:
            client: The HTTP client fixture.
            first_test_client_user: The test user fixture, without a profile.
            auth_headers_for_user: The fixture to generate auth headers.

        Raises:
            AssertionError: If the response status code is not 404, or if
            the response data does not match the expected values.
        """
        headers = auth_headers_for_user(first_test_client_user)

        response = await client.get(url=USER_PROFILE_ME_URL, headers=headers)
        assert response.status_code == status.HTTP_404_NOT_FOUND

        response_data = response.json()
        user_id = first_test_client_user.id
        expected_msg = f"User not found with User ID (Profile): {user_id}"
        assert response_data["detail"] == expected_msg

    async def test_api_get_me_current_user_with_expired_token_return_error(
        self,
        client: AsyncClient,
        first_test_client_user: UserModel,
        auth_headers_with_expired_token: Callable[[UserModel], Dict[str, str]]
    ) -> None:
        """
        Test GET /me for current authenticated user with an expired token.

        Verifies that a 401 Unauthorized response is returned when
        the client is authenticated with an expired token.

        Args:
            client: The HTTP client fixture.
            first_test_client_user: The test user fixture.
            auth_headers_with_expired_token: The fixture to generate
                auth headers with an expired token.

        Raises:
            AssertionError: If the response status code is not 401, or if
            the response data does not match the expected values.
        """
        headers = auth_headers_with_expired_token(first_test_client_user)

        response = await client.get(
            url=USER_PROFILE_ME_URL, headers=headers
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

        response_data = response.json()
        assert response_data["detail"] == "Could not validate credentials"
