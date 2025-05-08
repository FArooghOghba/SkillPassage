"""User factory for generating test data."""
from typing import (
    Any,
    Dict,
)

from async_factory_boy.factory.sqlalchemy import AsyncSQLAlchemyFactory
from factory import (
    LazyAttribute,
    LazyFunction,
    SubFactory,
)
from faker import Faker

from src.auth.services.password_services import get_password_hash
from src.user.constants import UserRole
from src.user.models import (
    User,
    UserProfile,
)


fake = Faker()

TEST_PASSWORD = "Test_passw0rd"


class UserFactory(AsyncSQLAlchemyFactory):  # type: ignore[misc]
    """Factory for creating User instances for testing.

    This factory generates realistic test data for User models using Faker.
    It supports both sync and async creation through AsyncSQLAlchemyFactory.
    """

    class Meta:
        """Factory configuration."""

        model = User
        sqlalchemy_session_persistence = "flush"

    # Basic user information
    email: Any = LazyAttribute(lambda _: fake.email())
    username: Any = LazyAttribute(lambda _: fake.user_name())
    hashed_password = LazyFunction(lambda: get_password_hash(TEST_PASSWORD))

    @classmethod
    def create_payload(cls) -> Dict[str, str]:
        """Generate a payload dictionary for creating a user.

        This class method creates a consistent set of user data that can be
        used for API testing or fixture creation. The generated payload
        includes the email, username, and a randomly generated password with
        a set of predefined complexity rules.
        A class method that creates a consistent set of user data that can be
        used for API testing or fixture creation.

        Returns:
            A payload dictionary with consistent values for creating users.
        """
        test_user = cls.build()
        fake_password = fake.password(
            length=12,
            special_chars=True,
            digits=True,
            upper_case=True,
            lower_case=True
        )
        return {
            'email': str(test_user.email),
            'username': str(test_user.username),
            'password': fake_password,
            'password_confirm': fake_password
        }

    @classmethod
    async def login_payload(cls) -> Dict[str, str]:
        """Generate a payload dictionary for user login.

        This provides credentials that will work with users
        created by UserFactory, since it uses the same 'test_password'
        that is hashed in the factory's hashed_password field.

        Returns:
            A dictionary with email and password for test login attempts
        """
        test_user = await cls.create()
        return {
            'email': str(test_user.email),
            'password': TEST_PASSWORD,
        }

    @classmethod
    async def inactive_login_payload(cls) -> Dict[str, str]:
        """Generate a payload dictionary for user login with inactive account.

        This provides credentials that will work with users
        created by UserFactory, since it uses the same 'test_password'
        that is hashed in the factory's hashed_password field. The
        user is however marked as inactive, so the login should fail.

        Returns:
            A dictionary with email and password for test login attempts
        """
        test_user = await cls.create()
        test_user.is_active = False

        return {
            'email': str(test_user.email),
            'password': TEST_PASSWORD,
        }


class UserProfileFactory(AsyncSQLAlchemyFactory):  # type: ignore[misc]
    """Factory for creating UserProfile instances for testing.

    This factory generates realistic test data for UserProfile models
    using Faker.
    It supports both sync and async creation through AsyncSQLAlchemyFactory.
    """

    class Meta:
        """Factory configuration."""

        model = UserProfile
        sqlalchemy_session_persistence = "flush"

    # Link to user
    user_id: Any = SubFactory(UserFactory)

    # Profile information
    first_name: Any = LazyAttribute(lambda _: fake.first_name())
    last_name: Any = LazyAttribute(lambda _: fake.last_name())
    phone_number: Any = LazyAttribute(
        lambda _: f"+1{fake.numerify(text='##########')}"
    )
    role: Any = LazyAttribute(lambda _: UserRole.CLIENT.value)

    @classmethod
    def create_payload(cls) -> Dict[str, str]:
        """Generate a payload dictionary for creating a user profile.

        A class method that creates a consistent set of profile data
        that can be used for API testing or fixture creation.

        Returns:
            A payload dictionary with consistent values for creating
            user profiles.
        """
        test_user = cls.build()
        return {
            'first_name': str(test_user.first_name),
            'last_name': str(test_user.last_name),
            'phone_number': str(test_user.phone_number),
        }
