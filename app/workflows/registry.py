"""
Workflow Registry Module

This module provides a simple registration system for workflows.
Workflows are registered by job_type and can be retrieved for execution.
"""

from typing import Type

from app.workflows.base import BaseWorkflow


# Internal registry mapping job_type -> workflow class
_registry: dict[str, Type[BaseWorkflow]] = {}


def register_workflow(
    job_type: str,
    workflow: Type[BaseWorkflow],
    schema: type | None = None,
) -> None:
    """Register a workflow class (and optional schema) for a given job type.

    Usage:
        register_workflow("example", ExampleWorkflow, ExampleJobSchema)

    Args:
        job_type: The job type string that triggers this workflow
        workflow: The workflow class to register
        schema: Optional schema class for job validation

    Raises:
        ValueError: If a workflow is already registered for the job_type
    """
    if job_type in _registry:
        raise ValueError(
            f"Workflow already registered for job_type '{job_type}': "
            f"{_registry[job_type].__name__}"
        )
    _registry[job_type] = workflow

    if schema is not None:
        workflow.job_schema = schema
        from app.workflows.schemas.registry import _register_schema

        _register_schema(job_type, schema)

    from app.worker.tasks import register_celery_task

    register_celery_task(job_type)


def get_workflow(job_type: str) -> BaseWorkflow:
    """Get a workflow instance for the given job type.

    Args:
        job_type: The job type to look up

    Returns:
        An instance of the registered workflow class

    Raises:
        KeyError: If no workflow is registered for the job type
    """
    if job_type not in _registry:
        available = ", ".join(_registry.keys()) if _registry else "none"
        raise KeyError(
            f"No workflow registered for job_type '{job_type}'. "
            f"Available workflows: {available}"
        )
    return _registry[job_type]()


def workflow_exists(job_type: str) -> bool:
    """Check if a workflow exists for the given job type.

    Args:
        job_type: The job type to check

    Returns:
        True if a workflow is registered, False otherwise
    """
    return job_type in _registry


def list_workflows() -> list[str]:
    """List all registered workflow job types.

    Returns:
        List of registered job type strings
    """
    return list(_registry.keys())


def clear_registry() -> None:
    """Clear the workflow registry. Primarily for testing."""
    _registry.clear()
