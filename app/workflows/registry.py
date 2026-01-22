"""
Workflow Registry Module

This module provides a simple registration system for workflows.
Workflows are registered by event_type and can be retrieved for execution.
"""

from typing import Callable, Type

from workflows.base import BaseWorkflow

# Internal registry mapping event_type -> workflow class
_registry: dict[str, Type[BaseWorkflow]] = {}


def register_workflow(event_type: str) -> Callable[[Type[BaseWorkflow]], Type[BaseWorkflow]]:
    """Decorator to register a workflow class for a given event type.

    Usage:
        @register_workflow("example")
        class ExampleWorkflow(BaseWorkflow):
            def process(self, context):
                ...

    Args:
        event_type: The event type string that triggers this workflow

    Returns:
        Decorator function that registers the workflow class
    """

    def decorator(cls: Type[BaseWorkflow]) -> Type[BaseWorkflow]:
        if event_type in _registry:
            raise ValueError(
                f"Workflow already registered for event_type '{event_type}': "
                f"{_registry[event_type].__name__}"
            )
        _registry[event_type] = cls
        return cls

    return decorator


def get_workflow(event_type: str) -> BaseWorkflow:
    """Get a workflow instance for the given event type.

    Args:
        event_type: The event type to look up

    Returns:
        An instance of the registered workflow class

    Raises:
        KeyError: If no workflow is registered for the event type
    """
    if event_type not in _registry:
        available = ", ".join(_registry.keys()) if _registry else "none"
        raise KeyError(
            f"No workflow registered for event_type '{event_type}'. "
            f"Available workflows: {available}"
        )
    return _registry[event_type]()


def workflow_exists(event_type: str) -> bool:
    """Check if a workflow exists for the given event type.

    Args:
        event_type: The event type to check

    Returns:
        True if a workflow is registered, False otherwise
    """
    return event_type in _registry


def list_workflows() -> list[str]:
    """List all registered workflow event types.

    Returns:
        List of registered event type strings
    """
    return list(_registry.keys())


def clear_registry() -> None:
    """Clear the workflow registry. Primarily for testing."""
    _registry.clear()
