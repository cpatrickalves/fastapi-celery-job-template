"""
Database Utility Module

This module provides utility functions for database operations.
It includes methods for retrieving connection strings and managing database sessions.
"""

from app.settings import settings


class DatabaseUtils:
    @staticmethod
    def get_connection_string() -> str:
        """Get synchronous PostgreSQL connection string."""
        return settings.database_url

    @staticmethod
    def get_async_connection_string() -> str:
        """Get asynchronous PostgreSQL connection string with asyncpg driver."""
        return settings.async_database_url
