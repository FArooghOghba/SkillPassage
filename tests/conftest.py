"""Test fixtures and configuration for pytest."""
from typing import AsyncGenerator

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
from tests.factories.user_factories import (
    UserFactory,
    UserProfileFactory,
)


# Register fixture plugins to make fixtures in other files discoverable
pytest_plugins = [
    "tests.fixtures.user_fixtures",
    "tests.fixtures.auth_fixtures",
    # Add other fixture modules here as needed:
    # "tests.fixtures.auth_fixtures",
    # "tests.fixtures.post_fixtures",
]


# --- Test Database Configuration ---

# Load database settings specifically for the test environment
# Reads connection details from .env.test
test_db_settings = DatabaseSettings(_env_file=".env.test")


# --- Core Test Fixtures ---


@pytest.fixture
async def engine() -> AsyncGenerator[AsyncEngine, None]:
    """Provide a SQLAlchemy AsyncEngine scoped per test function.

    This fixture establishes a connection pool to the **test database**
    defined by `test_db_settings`. It's crucial for interacting with the
    database in an async manner compatible with SQLAlchemy.

    **Scope:** Function (default `pytest.fixture` scope).
    - A new engine (and connection pool) is created for
    **each test function**.
    - Database tables (`Base.metadata`) are created before each test runs.
    - Database tables are dropped after each test finishes.
    - This scope ensures **strict test isolation** at the database level and
      aligns the engine's lifecycle with the **event loop created by
      pytest-asyncio for each test function**, preventing
      "different loop" errors.

    **Lifecycle:**
    1. Creates an `AsyncEngine` using the test database URL.
    2. Establishes a connection and runs `Base.metadata.create_all` to set up
       the schema defined in your models.
    3. `yields` the configured engine to the test function or other fixtures.
    4. After the test completes (or fails), it re-connects and runs
       `Base.metadata.drop_all` to clean up the database.
    5. Disposes of the engine's connection pool using `engine.dispose()`.

    Yields:
        AsyncEngine: The configured SQLAlchemy asynchronous engine instance.
    """
    engine = create_async_engine(
        url=test_db_settings.DATABASE_URL,  # Connect to the test database
        echo=False  # Set to True to log SQL queries executed by SQLAlchemy
    )

    # Setup: Create all tables defined in Base.metadata before the test runs.
    # Running create_all/drop_all within engine.begin()
    # ensures it uses a transaction.
    async with engine.begin() as conn:
        # Consider uncommenting drop_all if you need absolute certainty
        # of a clean slate, though create_all won't fail if tables exist.
        # await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)  # Create tables

    # Provide the engine instance to the test context
    yield engine

    # Teardown: Drop all tables and dispose of the engine after the test.
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    # Close all connections in the pool gracefully.
    await engine.dispose()


@pytest.fixture
async def async_session_maker(
    engine: AsyncEngine
) -> async_sessionmaker[AsyncSession]:
    """Provide a factory for creating new AsyncSession instances.

    This fixture configures an `async_sessionmaker` which acts as a factory
    or blueprint for creating new database sessions. It's bound to the
    function-scoped `engine` fixture, ensuring sessions are created using
    the correct engine for the current test's event loop.

    **Scope:** Function
    (derived from its dependency on the function-scoped `engine`).
    - A new session maker is configured for each test function.

    **Configuration:**
    - Bound to the `engine` created for the specific test.
    - `expire_on_commit=False`: This setting is often useful in tests. It
      prevents SQLAlchemy from expiring (detaching) ORM objects after a
      transaction commits (or, more relevantly here, after a `flush`). This
      allows accessing object attributes even if the session state changes,
      which can simplify assertions after database operations, although the
      `db_session` fixture primarily relies on rollback.

    Args:
        engine: The function-scoped `AsyncEngine` provided by
        the `engine` fixture.

    Returns:
        async_sessionmaker[AsyncSession]: A factory function to create new
                                          `AsyncSession` objects.
    """
    return async_sessionmaker(
        bind=engine,  # Bind the factory to the specific test's engine
        expire_on_commit=False  # Keep objects accessible after flush/commit
    )


@pytest.fixture
async def db_session(
    async_session_maker: async_sessionmaker[AsyncSession]
) -> AsyncGenerator[AsyncSession, None]:
    """Provide a transactional database session scoped per test function.

    This is the primary fixture for interacting with the database within
    individual tests. It creates an `AsyncSession` using the function-scoped
    `async_session_maker` and manages its lifecycle within a transaction.

    **Scope:** Function (default `pytest.fixture` scope).
    - A new, isolated database session is created for each test function.

    **Transaction Management:**
    1. Begins a new transaction when the session is created (`async with`).
    2. `yields` the session object to the test function.
    3. **Crucially, after the test completes (regardless of success
    or failure), it performs an `await session.rollback()`.
       ** This discards *any* changes made during the test,
       ensuring each test starts with a clean slate relative to
       database state changes made by other tests and maintaining
       test isolation.
    4. The `async with` block ensures the session is properly
    closed afterward.

    Args:
        async_session_maker: The function-scoped session factory provided by
                             the `async_session_maker` fixture.

    Yields:
        AsyncSession: The active, transactional database session for the test.
    """
    async with async_session_maker() as session:
        # Provide the session for the test
        yield session

        # Rollback any changes made during the test to ensure isolation
        # The 'async with' context manager handles session.close()
        # automatically
        await session.rollback()


@pytest.fixture
async def client(
        db_session: AsyncSession,
        test_app: FastAPI
) -> AsyncGenerator[AsyncClient, None]:
    """Create a test client for the FastAPI application.

    Provide an HTTP test client (`httpx.AsyncClient`) for making API requests.
    This fixture creates a test client configured to interact with the FastAPI
    application (`test_app`). It automatically handles overriding the
    application's database dependency (`get_db`) to inject the isolated,
    transactional `db_session` fixture for the duration of the test.

    **Scope:** Function (default `pytest.fixture` scope).
    - A new test client is created for each test function.

    **Dependency Override:**
    1. Defines an `override_get_db` function that yields the `db_session`
       provided by the fixture for the current test.
    2. Patches the `test_app.dependency_overrides` dictionary, mapping the
       original `get_db` dependency to the `override_get_db` function.
    3. Any API endpoint called via this client that depends on `get_db` will
       receive the test's `db_session` instead of the real one.

    **Client Configuration:**
    - `app=test_app`: The FastAPI application instance to test against.
    - `base_url="http://test"`: A dummy base URL required by `httpx`. Allows
      using relative paths like `/api/v1/users` in tests.
    - `follow_redirects=True`: Configures the client to automatically follow
      HTTP redirects (status codes 3xx).

    **Lifecycle:**
    1. Applies the dependency override.
    2. Creates and `yields` the configured `AsyncClient`.
    3. After the test completes, it **clears** the `dependency_overrides` to
       prevent the override from affecting subsequent tests, ensuring
       isolation.

    Args:
        db_session: The function-scoped database session from `db_session`
        fixture.
        test_app: The FastAPI application instance from `test_app` fixture.

    Yields:
        AsyncClient: The configured HTTPX asynchronous test client.
    """
    # Override the get_db dependency to use our test session
    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        """Yield the test database session."""
        yield db_session

    # Apply the override to the FastAPI app
    test_app.dependency_overrides[get_db] = override_get_db

    # Create and yield the test client within an async context manager
    async with AsyncClient(
        app=test_app,  # type: ignore
        base_url="http://test",  # Base URL for relative paths
        follow_redirects=True  # Automatically follow redirects
    ) as client:
        # Provide the client to the test
        yield client

    # Teardown: Remove the dependency override after the test
    test_app.dependency_overrides.clear()


@pytest.fixture
def test_app() -> FastAPI:
    """Provides the FastAPI application instance for testing.

    **Scope:** Function (default `pytest.fixture` scope).

    A simple fixture that returns the globally imported `app` instance from
    `src.main`. This is often used as a dependency for other fixtures,
    like the `client` fixture, which needs the app object to interact with.

    Returns:
        FastAPI: The main application instance.
    """
    return app


@pytest.fixture(autouse=True)
def set_session_for_factories(db_session: AsyncSession) -> None:
    """Automatically injects the test DB session into factory_boy factories.

    This is an `autouse` fixture, meaning it runs automatically for every
    test function without needing to be explicitly requested as an argument
    by the test function itself. Its primary purpose is convenience for using
    `factory_boy` factories that require a database session.

    **Scope:** Function (default `pytest.fixture` scope). Runs once per test.

    **Functionality:**
    - It depends on the `db_session` fixture.
    - It sets the `_meta.sqlalchemy_session` attribute on specified factory
      classes (e.g., `UserFactory`) to the current test's `db_session`.
    - This allows calling factories like `await UserFactory()` within tests
      or other fixtures without manually passing the session, as the factory
      will automatically use the session provided by this fixture.

    **Important:** Remember to add any other factory classes that need the
    session configured here.

    Args:
        db_session: The function-scoped database session from `db_session`
        fixture. This dependency ensures this fixture runs after `db_session`
        is ready and triggers its execution for every test.
    """
    UserFactory._meta.sqlalchemy_session = db_session
    UserProfileFactory._meta.sqlalchemy_session = db_session
    # Add other factories here as needed:
    # OtherFactory._meta.sqlalchemy_session = db_session
    # Example: PostFactory._meta.sqlalchemy_session = db_session
    # Example: CommentFactory._meta.sqlalchemy_session = db_session
