"""
Pytest configuration and shared fixtures.

This module provides common fixtures used across test modules.
"""

from typing import Any, Generator

import pytest


@pytest.fixture
def sample_job_data() -> dict[str, Any]:
    """Provide sample job data for testing."""
    return {
        "job_type": "example",
        "message": "Hello, World!",
        "metadata": {"source": "test"},
    }


@pytest.fixture
def sample_job_id() -> str:
    """Provide a sample job ID for testing."""
    return "550e8400-e29b-41d4-a716-446655440000"


@pytest.fixture(autouse=True)
def reset_registries() -> Generator[None, None, None]:
    """Reset registries before and after each test to ensure isolation."""
    from app.workflows.config import _reset_registered
    from app.workflows.schemas.registry import clear_registry as clear_schema_registry
    from app.workflows.registry import clear_registry as clear_workflow_registry

    clear_workflow_registry()
    clear_schema_registry()
    _reset_registered()
    yield
    clear_workflow_registry()
    clear_schema_registry()
    _reset_registered()
