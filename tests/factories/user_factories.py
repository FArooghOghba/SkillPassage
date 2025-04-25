"""User factory for generating test data."""
from typing import Any

from async_factory_boy.factory.sqlalchemy import AsyncSQLAlchemyFactory
from factory import (
    LazyAttribute,
    LazyFunction,
    SubFactory,
)
from faker import Faker

from src.auth.services import get_password_hash
from src.user.constants import UserRole
from src.user.models import (
    User,
    UserProfile,
)


fake = Faker()


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
    hashed_password = LazyFunction(lambda: get_password_hash("test_password"))


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
