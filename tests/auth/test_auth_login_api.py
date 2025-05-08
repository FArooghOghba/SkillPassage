"""Tests for the user login API endpoints.

This module contains tests for the user login endpoints exposed by the
application. It verifies that the API endpoints behave as expected for
both valid and invalid input data.
"""
import pytest
from fastapi import status
from httpx import AsyncClient


USER_AUTH_LOGIN_URL = "/api/v1/auth/login"


@pytest.mark.asyncio
class TestAuthLoginUser:
    async def test_api_login_user_return_success(
            self, client: AsyncClient,
            first_test_user_login_payload: dict[str, str]
    ) -> None:
        """Test successful user login via API.

        This test ensures that a user can successfully log in using valid
        credentials. It verifies that the response status is HTTP 200 OK
        and checks that the response data includes a non-null access token,
        an expiration time, and the token type is 'bearer'. Additionally, it
        confirms that the refresh token is not included in the response.

        Args:
            client: AsyncClient instance for making HTTP requests.
            first_test_user_login_payload: Dictionary containing the test
            user login data.

        Raises:
            AssertionError: If the response status code is not 200 or if
            the response data does not match the expected values.
        """
        response = await client.post(
            url=USER_AUTH_LOGIN_URL, json=first_test_user_login_payload
        )
        assert response.status_code == status.HTTP_200_OK

        response_data = response.json()

        assert response_data['access_token'] is not None
        assert response_data['expires_in'] is not None
        assert response_data['token_type'] == 'bearer'
        assert response_data['refresh_token'] is None

    async def test_api_login_user_with_invalid_password_return_error(
            self, client: AsyncClient,
            first_test_user_login_payload: dict[str, str]
    ) -> None:
        """Test API user login with invalid password returns an error.

        This test verifies that attempting to log in with an invalid password
        raises an error. It checks that the response status is HTTP 401
        Unauthorized, and ensures that the error message in the response
        matches the expected format indicating that the credentials are
        invalid.

        Args:
            client: AsyncClient instance for making HTTP requests.
            first_test_user_login_payload: Dictionary containing the test
            user login data.

        Raises:
            AssertionError: If the response status code is not 401, or if
            the response data does not match the expected values.
        """
        first_test_user_login_payload["password"] = "invalid_password"

        response = await client.post(
            url=USER_AUTH_LOGIN_URL, json=first_test_user_login_payload
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

        expected_error_msg = "Invalid credentials"
        response_data = response.json()["detail"]
        assert response_data == expected_error_msg

    async def test_api_login_user_with_nonexistence_email_return_error(
            self, client: AsyncClient,
            first_test_user_login_payload: dict[str, str],
    ) -> None:
        """Test API user login with nonexistence email returns an error.

        This test verifies that attempting to log in with a nonexistence email
        raises an error. It checks that the response status is HTTP 401
        Unauthorized, and ensures that the error message in the response
        matches the expected format indicating that the credentials are
        invalid.

        Args:
            client: AsyncClient instance for making HTTP requests.
            first_test_user_login_payload: Dictionary containing the test
            user login data.

        Raises:
            AssertionError: If the response status code is not 401, or if
            the response data does not match the expected values.
        """
        first_test_user_login_payload["email"] = "nonexistence@email.com"

        response = await client.post(
            url=USER_AUTH_LOGIN_URL, json=first_test_user_login_payload
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

        expected_error_msg = "Invalid credentials"
        response_data = response.json()["detail"]
        assert response_data == expected_error_msg

    async def test_api_login_user_with_inactive_user_email_return_error(
            self, client: AsyncClient,
            first_test_inactive_user_login_payload: dict[str, str],
    ) -> None:
        """Test API user login with inactive user email returns an error.

        This test verifies that attempting to log in with an inactive
        user email raises an error. It checks that the response status
        is HTTP 401 Unauthorized, and ensures that the error message in
        the response matches the expected format indicating that the user
        account is inactive.

        Args:
            client: AsyncClient instance for making HTTP requests.
            first_test_inactive_user_login_payload: Dictionary containing
            the test user login data with inactive user email.

        Raises:
            AssertionError: If the response status code is not 401, or if
            the response data does not match the expected values.
        """
        response = await client.post(
            url=USER_AUTH_LOGIN_URL,
            json=first_test_inactive_user_login_payload
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

        expected_error_msg = "User account is inactive"
        response_data = response.json()["detail"]
        assert response_data == expected_error_msg

    @pytest.mark.parametrize(
        "invalid_email, expected_error_msg",
        [
            (
                "wrong_email@!",
                "The part after the @-sign contains invalid characters: '!'."
            ),
            (
                "@wrong_email.com",
                "There must be something before the @-sign."
            ),
            (
                "wrong_email",
                "An email address must have an @-sign."
            ),
            (
                " ",
                "An email address must have an @-sign."
            ),
            (
                "",
                "An email address must have an @-sign."
            ),
        ],
        ids=[
            "without-mailserver-and-domain",
            "without-username-part",
            "without-@",
            "space",
            "no-email",
        ]
    )
    async def test_api_login_user_with_invalid_email_return_error(
            self, client: AsyncClient,
            first_test_user_login_payload: dict[str, str],
            invalid_email: str, expected_error_msg: str
    ) -> None:
        """
        Test API user login with an invalid email address.

        This test verifies that attempting to log in a user with an invalid
        email address results in an HTTP 422 Unprocessable Entity error. It
        checks that the response status is HTTP 422, and ensures the error
        message in the response matches the expected format indicating that
        the email address is not valid.

        Args:
            client: AsyncClient instance for making HTTP requests.
            first_test_user_login_payload: Test user data dictionary.
            invalid_email: The invalid email to test.
            expected_error_msg: Expected error message fragment.

        Raises:
            AssertionError: If the response status code is not 422, or if
            the response data does not match the expected values.
        """
        first_test_user_login_payload["email"] = invalid_email

        response = await client.post(
            url=USER_AUTH_LOGIN_URL, json=first_test_user_login_payload
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

        response_data = response.json()["detail"][0]["msg"]
        assert response_data == (
            f"value is not a valid email address: {expected_error_msg}"
        )
