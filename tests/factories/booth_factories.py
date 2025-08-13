"""Booth factory for generating test data.

This module contains a single factory class, BoothFactory, which is used to
generate realistic test data for Booth models using Faker. The factory
supports both synchronous and asynchronous creation through
AsyncSQLAlchemyFactory.
"""
from typing import (
    Any,
    Dict,
)

from async_factory_boy.factory.sqlalchemy import AsyncSQLAlchemyFactory
from factory import (
    LazyAttribute,
    SubFactory,
)
from faker import Faker

from src.booth.models import Booth


fake = Faker()


class BoothFactory(AsyncSQLAlchemyFactory):  # type: ignore[misc]
    """Factory for creating Booth instances for testing.

    This factory generates realistic test data for Booth models using Faker.
    It supports both sync and async creation through AsyncSQLAlchemyFactory.
    """
    class Meta:
        """Factory configuration."""

        model = Booth
        sqlalchemy_session_persistence = "flush"

    # Basic user information
    owner: Any = SubFactory("tests.factories.user_factories.UserFactory")
    title: Any = LazyAttribute(lambda _: fake.sentence(nb_words=4))
    description: Any = LazyAttribute(lambda _: fake.paragraph(nb_sentences=3))
    tags: Any = LazyAttribute(lambda _: [fake.word() for _ in range(3)])

    @classmethod
    def create_payload(cls) -> Dict[str, str]:
        """Generate a payload dictionary for creating a Booth.

        This class method creates a consistent set of data that can be
        used for API testing or fixture creation. The generated payload
        includes the title, description, and tags of a Booth.

        Returns:
            A payload dictionary with consistent values for creating
            Booths.
        """
        # Use .build() to create an unsaved instance to get fake data
        test_booth = cls.build()

        return {
            'title': test_booth.title,
            'description': test_booth.description,
            'tags': test_booth.tags
        }
