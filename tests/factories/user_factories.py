"""User factory for generating test data."""
from async_factory_boy.factory.sqlalchemy import AsyncSQLAlchemyFactory
from factory import LazyFunction
from faker import Faker

from src.auth.services import get_password_hash
from src.user.constants import UserType
from src.user.models import User


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
    email = Faker("email")
    username = Faker("user_name")
    first_name = Faker("first_name")
    last_name = Faker("last_name")
    phone_number = Faker("phone_number")
    hashed_password = LazyFunction(lambda: get_password_hash("test_password"))
    type = UserType.CLIENT.value
