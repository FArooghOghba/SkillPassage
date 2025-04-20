"""
Application configuration settings using Pydantic BaseSettings.

This module contains settings for database connection and authentication
configuration, loaded from environment variables.
"""
from datetime import timedelta

from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
)


class DatabaseSettings(BaseSettings):
    """
    Database configuration settings.

    Attributes:
        DATABASE_URL: SQLAlchemy connection string for the database
    """

    DATABASE_URL: str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


class AuthSettings(BaseSettings):
    """
    Authentication configuration settings.

    Attributes:
        JWT_SECRET_KEY: Secret key for JWT token signing
        JWT_ALGORITHM: Algorithm used for JWT token signing (default: "HS256")
        JWT_ACCESS_TOKEN_EXPIRE_MINUTES: Access token expiration in minutes
    """

    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    @property
    def access_token_expire_delta(self) -> timedelta:
        """Get access token expiration as timedelta."""
        return timedelta(minutes=self.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


# Default instances using .env
db_settings = DatabaseSettings()
auth_settings = AuthSettings()
