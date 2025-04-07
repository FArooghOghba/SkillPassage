"""Test fixtures and configuration for pytest."""
import asyncio
from typing import (
    AsyncGenerator,
    Generator,
)

import pytest
from fastapi import FastAPI
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.core.config import DatabaseSettings
from src.db.base import Base
from src.db.session import get_db
from src.main import app


# Create test-specific database settings
test_db_settings = DatabaseSettings(_env_file=".env.test")


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """
    Create an instance of the default event loop for each test case.

    A pytest fixture that creates an event loop for async tests
    scope="session" means this fixture is created once per test session.
    The event loop is needed for running async tests.
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop  # Provide the loop for the tests
    loop.close()  # Cleanup after all tests are done


@pytest.fixture(scope="session")
async def engine() -> AsyncGenerator[AsyncEngine, None]:
    """
    Create and manages the test database engine.

    This fixture:
    1. Creates a new SQLAlchemy engine connected to test database
    2. Creates all tables before tests
    3. Drops all tables after tests
    4. Disposes of the engine
    """
    engine = create_async_engine(
        url=test_db_settings.DATABASE_URL,  # Use test database URL
        echo=False  # Set to True to see SQL queries
    )

    # Before running tests: Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)  # Clean slate
        await conn.run_sync(Base.metadata.create_all)  # Create tables

    yield engine  # Provide the engine for the tests

    # After all tests: Drop all tables and cleanup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture(scope="session")
async def async_session_maker(
    engine: AsyncEngine
) -> async_sessionmaker[AsyncSession]:
    """
    Create a test session factory for the test database.

    This fixture creates a factory for making new database sessions.
    It uses the test engine and disables expire_on_commit for easier testing.
    """
    return async_sessionmaker(
        engine,
        expire_on_commit=False  # Keep objects accessible after commit
    )


@pytest.fixture
async def db_session(
    async_session_maker: async_sessionmaker[AsyncSession]
) -> AsyncGenerator[AsyncSession, None]:
    """
    Create and provides a test database session for each test.

    This fixture:
    1. Creates a new database session for each test
    2. Rolls back any changes after the test
    3. Closes the session
    """
    async with async_session_maker() as session:
        yield session  # Provide the session for the test
        await session.rollback()  # Rollback any changes made in the test


@pytest.fixture
async def client(
    db_session: AsyncSession
) -> AsyncGenerator[AsyncClient, None]:
    """
    Create a test client with a test database session.

    This fixture:
    1. Overrides the database dependency with our test session
    2. Creates an HTTP client for testing API endpoints
    3. Cleans up after the test
    """
    # Override the get_db dependency to use our test session
    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    # Create and yield the test client
    async with AsyncClient(
        app=app,
        base_url="http://test",  # Base URL for relative paths
        follow_redirects=True  # Automatically follow redirects
    ) as client:
        yield client

    # Cleanup: remove the dependency override
    app.dependency_overrides.clear()


@pytest.fixture
def test_app() -> FastAPI:
    """
    Create a test FastAPI application.

    Simple fixture that provides the FastAPI app instance for testing.
    """
    return app
