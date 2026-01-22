"""
Schema Registry Module

This module provides a registration system for event schemas.
Schemas are registered by event_type and used for validation.
"""

from typing import Callable, Type

from pydantic import BaseModel

from schemas.base import BaseEventSchema

# Internal registry mapping event_type -> schema class
_schema_registry: dict[str, Type[BaseEventSchema]] = {}


def register_schema(event_type: str) -> Callable[[Type[BaseModel]], Type[BaseModel]]:
    """Decorator to register a schema class for a given event type.

    Usage:
        @register_schema("example")
        class ExampleEventSchema(BaseEventSchema):
            message: str

    Args:
        event_type: The event type string this schema validates

    Returns:
        Decorator function that registers the schema class
    """

    def decorator(cls: Type[BaseModel]) -> Type[BaseModel]:
        if event_type in _schema_registry:
            raise ValueError(
                f"Schema already registered for event_type '{event_type}': "
                f"{_schema_registry[event_type].__name__}"
            )
        _schema_registry[event_type] = cls
        return cls

    return decorator


def get_schema(event_type: str) -> Type[BaseEventSchema]:
    """Get the schema class for the given event type.

    Args:
        event_type: The event type to look up

    Returns:
        The registered schema class

    Raises:
        KeyError: If no schema is registered for the event type
    """
    if event_type not in _schema_registry:
        available = ", ".join(_schema_registry.keys()) if _schema_registry else "none"
        raise KeyError(
            f"No schema registered for event_type '{event_type}'. "
            f"Available schemas: {available}"
        )
    return _schema_registry[event_type]


def schema_exists(event_type: str) -> bool:
    """Check if a schema exists for the given event type.

    Args:
        event_type: The event type to check

    Returns:
        True if a schema is registered, False otherwise
    """
    return event_type in _schema_registry


def list_schemas() -> list[str]:
    """List all registered schema event types.

    Returns:
        List of registered event type strings
    """
    return list(_schema_registry.keys())


def validate_event(event_data: dict) -> BaseEventSchema:
    """Validate event data against its registered schema.

    Args:
        event_data: The raw event data to validate

    Returns:
        Validated schema instance

    Raises:
        KeyError: If no schema is registered for the event type
        ValidationError: If the data doesn't match the schema
    """
    event_type = event_data.get("event_type")
    if not event_type:
        raise ValueError("Event data must contain 'event_type' field")

    schema_class = get_schema(event_type)
    return schema_class.model_validate(event_data)


def clear_registry() -> None:
    """Clear the schema registry. Primarily for testing."""
    _schema_registry.clear()
