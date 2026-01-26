"""
Workflow Registry Module

This module provides a simple registration system for workflows.
Workflows are registered by job_type and can be retrieved for execution.
"""

from typing import Callable, Type

from app.workflows.base import BaseWorkflow

# Internal registry mapping job_type -> workflow class
_registry: dict[str, Type[BaseWorkflow]] = {}


def register_workflow(
    job_type: str,
) -> Callable[[Type[BaseWorkflow]], Type[BaseWorkflow]]:
    """Decorator to register a workflow class for a given job type.

    Usage:
        @register_workflow("example")
        class ExampleWorkflow(BaseWorkflow):
            def process(self, context):
                ...

    Args:
        job_type: The job type string that triggers this workflow

    Returns:
        Decorator function that registers the workflow class
    """

    def decorator(cls: Type[BaseWorkflow]) -> Type[BaseWorkflow]:
        if job_type in _registry:
            raise ValueError(
                f"Workflow already registered for job_type '{job_type}': "
                f"{_registry[job_type].__name__}"
            )
        _registry[job_type] = cls
        return cls

    return decorator


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
