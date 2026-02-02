"""
Schema Registry Module

This module provides a registration system for job schemas.
Schemas are registered by job_type and used for validation.
"""

from typing import Type

from app.workflows.schemas.base import BaseJobSchema

# Internal registry mapping job_type -> schema class
_schema_registry: dict[str, Type[BaseJobSchema]] = {}


def _register_schema(job_type: str, schema_class: Type[BaseJobSchema]) -> None:
    """Register a schema class for a given job type (internal use).

    Called by register_workflow() in the workflow registry when a schema
    is provided. Not intended for direct external use.

    Args:
        job_type: The job type string this schema validates
        schema_class: The schema class to register

    Raises:
        ValueError: If a schema is already registered for the job_type
    """
    if job_type in _schema_registry:
        raise ValueError(
            f"Schema already registered for job_type '{job_type}': "
            f"{_schema_registry[job_type].__name__}"
        )
    _schema_registry[job_type] = schema_class


def get_schema(job_type: str) -> Type[BaseJobSchema]:
    """Get the schema class for the given job type.

    Args:
        job_type: The job type to look up

    Returns:
        The registered schema class

    Raises:
        KeyError: If no schema is registered for the job type
    """
    if job_type not in _schema_registry:
        available = ", ".join(_schema_registry.keys()) if _schema_registry else "none"
        raise KeyError(
            f"No schema registered for job_type '{job_type}'. "
            f"Available schemas: {available}"
        )
    return _schema_registry[job_type]


def schema_exists(job_type: str) -> bool:
    """Check if a schema exists for the given job type.

    Args:
        job_type: The job type to check

    Returns:
        True if a schema is registered, False otherwise
    """
    return job_type in _schema_registry


def list_schemas() -> list[str]:
    """List all registered schema job types.

    Returns:
        List of registered job type strings
    """
    return list(_schema_registry.keys())


def get_all_schemas() -> dict[str, Type[BaseJobSchema]]:
    """Get all registered schemas for endpoint generation.

    Returns:
        Dictionary mapping job_type to schema class
    """
    return dict(_schema_registry)


def validate_job(job_data: dict) -> BaseJobSchema:
    """Validate job data against its registered schema.

    Args:
        job_data: The raw job data to validate

    Returns:
        Validated schema instance

    Raises:
        KeyError: If no schema is registered for the job type
        ValidationError: If the data doesn't match the schema
    """
    job_type = job_data.get("job_type")
    if not job_type:
        raise ValueError("Job data must contain 'job_type' field")

    schema_class = get_schema(job_type)
    return schema_class.model_validate(job_data)


def clear_registry() -> None:
    """Clear the schema registry. Primarily for testing."""
    _schema_registry.clear()
