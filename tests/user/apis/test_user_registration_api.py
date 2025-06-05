"""Tests for the user registration API endpoints.

This module contains tests for the user registration endpoints exposed
by the application. It verifies that the API endpoints behave as expected
for both valid and invalid input data.

"""
import pytest
from fastapi import status
from httpx import AsyncClient

from src.user.models import User


USER_REGISTRATION_URL = "/api/v1/user/registration"


@pytest.mark.asyncio
class TestRegisterUser:
    async def test_api_user_registration_return_success(
            self, client: AsyncClient,
            first_test_register_payload: dict[str, str]
    ) -> None:
        """Test successful user registration via API.

        This test verifies that a new user can successfully register
        using the provided registration payload. It checks that the
        response status is HTTP 201 Created, and ensures that the email
        and username in the response match the ones in the registration
        payload. Additionally, it confirms that the user is marked as
        active in the response.

        Args:
            client: AsyncClient instance for making HTTP requests.
            first_test_register_payload: Dictionary containing the test
            registration data.

        Raises:
            AssertionError: If the response status code is not 201, or if
            the response data does not match the expected values.
        """
        response = await client.post(
            url=USER_REGISTRATION_URL, json=first_test_register_payload
        )
        assert response.status_code == status.HTTP_201_CREATED

        user_payload_email = first_test_register_payload["email"]
        user_payload_username = first_test_register_payload["username"]

        user_payload_first_name = first_test_register_payload["first_name"]
        user_payload_last_name = first_test_register_payload["last_name"]
        user_payload_phone = first_test_register_payload["phone_number"]

        response_user_data = response.json()

        assert response_user_data['email'] == user_payload_email
        assert response_user_data['username'] == user_payload_username
        assert response_user_data['is_active'] is True
        assert response_user_data['is_superuser'] is False
        assert response_user_data['professional_profile'] is None

        response_profile_data = response_user_data['profile']
        assert response_profile_data['first_name'] == user_payload_first_name
        assert response_profile_data['last_name'] == user_payload_last_name
        assert response_profile_data['phone_number'] == user_payload_phone

    async def test_api_user_registration_with_existent_email_return_error(
            self, client: AsyncClient,
            first_test_client_user: User,
            first_test_register_payload: dict[str, str]
    ) -> None:
        """Test API user registration with an existing email returns an error.

        This test verifies that attempting to register a user with an
        email that already exists in the system raises an error.

        Args:
            client: AsyncClient instance for making HTTP requests.
            first_test_client_user: Existing test user fixture.
            first_test_register_payload: Test user data dictionary.

        Raises:
            AssertionError: If the response status code is not 409, or if
            the response data does not match the expected values.
        """
        existed_email = first_test_client_user.email
        first_test_register_payload["email"] = existed_email

        response = await client.post(
            url=USER_REGISTRATION_URL, json=first_test_register_payload
        )
        assert response.status_code == status.HTTP_409_CONFLICT

        response_data = response.json()
        expected_error_msg = f"User already exists with Email: {existed_email}"
        assert response_data["detail"] == expected_error_msg

    async def test_api_user_registration_with_existent_username_return_error(
            self, client: AsyncClient,
            first_test_client_user: User,
            first_test_register_payload: dict[str, str]
    ) -> None:
        """Test API user registration with an existing username.

        This test verifies that attempting to register a user with a
        username that already exists in the system results in a conflict
        error. It checks that the response status is HTTP 409 Conflict,
        and ensures the error message in the response matches the expected
        format indicating the username conflict.

        Args:
            client: AsyncClient instance for making HTTP requests.
            first_test_client_user: Existing test user fixture.
            first_test_register_payload: Test user data dictionary.

        Raises:
            AssertionError: If the response status code is not 409, or if
            the response data does not match the expected values.
        """
        existed_username = first_test_client_user.username
        first_test_register_payload["username"] = existed_username

        response = await client.post(
            url=USER_REGISTRATION_URL, json=first_test_register_payload
        )
        assert response.status_code == status.HTTP_409_CONFLICT

        response_data = response.json()
        expected_error_msg = (
            f"User already exists with Username: {existed_username}"
        )
        assert response_data["detail"] == expected_error_msg

    async def test_api_user_registration_with_non_matched_pass_return_error(
            self, client: AsyncClient,
            first_test_register_payload: dict[str, str]
    ) -> None:
        """Test API user registration with non-matching passwords.

        This test verifies that attempting to register a user with a
        password and password confirmation that do not match results in
        an HTTP 422 Unprocessable Entity error. It checks that the
        response status is HTTP 422, and ensures the error message in
        the response matches the expected format indicating that the
        passwords do not match.

        Args:
            client: AsyncClient instance for making HTTP requests.
            first_test_register_payload: Test user data dictionary.

        Raises:
            AssertionError: If the response status code is not 422, or if
            the response data does not match the expected values.
        """
        first_test_register_payload["password_confirm"] = "non_matched_pass"

        response = await client.post(
            url=USER_REGISTRATION_URL, json=first_test_register_payload
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

        expected_error_msg = "Passwords do not match"
        response_data = response.json()["detail"][0]["msg"]
        assert expected_error_msg in response_data

    @pytest.mark.parametrize(
        "invalid_password,expected_error_msg",
        [
            (
                    "nouppercaseordigits!",
                    "must contain an uppercase letter; must contain a digit"
            ),
            (
                    "NOLOWERCASEORDIGITS!",
                    "must contain a lowercase letter; must contain a digit"
            ),
            (
                    "NoSpecialCharsOrDigits",
                    "must contain a digit; must contain a special character"
            ),
            (
                    "NoSpecial123",
                    "must contain a special character"
            ),
            (
                    "short",
                    "must be at least 8 characters"
            ),  # If you have min_length=8
        ],
        ids=[
            "no-uppercase-or-digits",
            "no-lowercase-or-digits",
            "no-special-chars-or-digits",
            "no-special-chars",
            "too-short",
        ]
    )
    async def test_api_user_registration_with_invalid_pass_return_error(
            self, client: AsyncClient,
            first_test_register_payload: dict[str, str],
            invalid_password: str, expected_error_msg: str
    ) -> None:
        """Test API user registration with invalid passwords.

        This parameterized test verifies that attempting to register a user
        with a password that does not meet complexity requirements results in
        an HTTP 422 Unprocessable Entity error. It checks that the response
        status is HTTP 422, and ensures the error message in the response
        matches the expected format indicating that the password does not meet
        complexity requirements.

        Args:
            client: AsyncClient instance for making HTTP requests.
            first_test_register_payload: Test user data dictionary.
            invalid_password: The invalid password to test.
            expected_error_msg: Expected error message fragment.

        Raises:
            AssertionError: If the response status code is not 422, or if
            the response data does not match the expected values.
        """
        first_test_register_payload["password"] = invalid_password
        first_test_register_payload["password_confirm"] = invalid_password

        response = await client.post(
            url=USER_REGISTRATION_URL, json=first_test_register_payload
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

        response_data = response.json()["detail"][0]["msg"]
        assert expected_error_msg in response_data
