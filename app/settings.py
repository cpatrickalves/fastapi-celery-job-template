"""
Application Settings Module

This module uses pydantic-settings to manage configuration variables,
allowing for easy loading from environment variables or a .env file.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from pydantic_settings import BaseSettings, SettingsConfigDict
import tomli
from app.utils.logger import logger


class Settings(BaseSettings):
    """Defines the application's configuration settings."""

    # Application
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    PROJECT_NAME: str = "fastapi-celery-job-template"

    # Database
    POSTGRES_HOST: str = ""
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = ""
    POSTGRES_USER: str = ""
    POSTGRES_PASSWORD: str = ""

    # Redis
    REDIS_HOST: str = ""
    REDIS_PORT: int = 6379

    # CORS
    ALLOWED_ORIGINS: str = ""

    # API Key Authentication
    API_KEYS: str = "Python42"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    def __init__(self, **values: Any) -> None:
        """Initialize Settings and validate required environment variables.

        Args:
            **values: Arbitrary keyword arguments for settings initialization.
        """
        try:
            super().__init__(**values)

            logger.info("=" * 50)
            logger.info(f"ENVIRONMENT: {self.ENVIRONMENT.upper()}")
            logger.info("=" * 50)

            # Skip validation in testing environment
            if self.ENVIRONMENT == "testing":
                logger.info("Testing environment - skipping validation")
            else:
                self._validate_required_vars()
                self._load_version_from_pyproject()

            logger.info("Settings loaded successfully.")

        except Exception as exc:
            logger.error(f"Settings initialization failed: {exc}")
            sys.exit(1)

    def _validate_required_vars(self) -> None:
        """Validate that required environment variables are set."""
        required_vars = (
            "POSTGRES_HOST",
            "POSTGRES_DB",
            "POSTGRES_USER",
            "POSTGRES_PASSWORD",
        )

        for var in required_vars:
            if not getattr(self, var):
                logger.error(f"{var} environment variable is not set.")
                sys.exit(1)

    def _load_version_from_pyproject(self) -> None:
        """Load version from pyproject.toml if available."""
        try:
            pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
            if pyproject_path.exists():
                with open(pyproject_path, "rb") as f:
                    data = tomli.load(f)
                    self.VERSION = data.get("project", {}).get("version", self.VERSION)
        except ImportError:
            logger.debug("tomli not installed, using default version")
        except Exception as exc:
            logger.debug(f"Could not load version from pyproject.toml: {exc}")

    @property
    def database_url(self) -> str:
        """Build the database URL from components."""
        return (
            f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def async_database_url(self) -> str:
        """Build the async database URL with asyncpg driver."""
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def redis_url(self) -> str:
        """Build the Redis URL from components."""
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/0"


# Global settings instance
settings: Settings

try:
    settings = Settings()
except Exception as exc:
    logger.error(f"Failed to load settings: {exc}")
    sys.exit(1)
