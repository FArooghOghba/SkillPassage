from typing import (
    Callable,
    Dict,
)

import pytest
from fastapi import status
from httpx import AsyncClient

from src.user.models import (
    BaseUserProfile as UserProfileModel,
    User as UserModel,
)


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

        user_email = first_test_client_user.email
        user_username = first_test_client_user.username

        user_first_name = first_test_client_profile.first_name
        user_last_name = first_test_client_profile.last_name
        user_phone = first_test_client_profile.phone_number

        response_user_data = response.json()

        assert response_user_data["email"] == user_email
        assert response_user_data["username"] == user_username
        assert response_user_data['is_active'] is True
        assert response_user_data['is_superuser'] is False
        assert response_user_data['professional_profile'] is None

        response_profile_data = response_user_data['profile']
        assert response_profile_data["first_name"] == user_first_name
        assert response_profile_data["last_name"] == user_last_name
        assert response_profile_data["phone_number"] == user_phone

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
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

        response_data = response.json()
        expected_msg = "User profile data is missing."
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
