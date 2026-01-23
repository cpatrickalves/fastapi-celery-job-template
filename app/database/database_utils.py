import os
from settings import settings

"""
Database Utility Module

This module provides utility functions for database operations.
It includes methods for retrieving connection strings and managing database sessions.
"""


class DatabaseUtils:
    @staticmethod
    def get_connection_string():
        db_host = settings.POSTGRES_HOST
        db_port = settings.POSTGRES_PORT
        db_name = settings.POSTGRES_DB
        db_user = settings.POSTGRES_USER
        db_password = settings.POSTGRES_PASSWORD

        return f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
