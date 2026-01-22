"""
Example Event Schema Module

This module defines the schema for the example workflow.
It demonstrates the basic structure of an event schema.
"""

from typing import Literal, Optional

from pydantic import Field

from schemas.base import BaseEventSchema
from schemas.registry import register_schema


@register_schema("example")
class ExampleEventSchema(BaseEventSchema):
    """Schema for events processed by the example workflow.

    This schema demonstrates the basic structure of an event:
    - event_type: Identifies which workflow should process this event
    - message: The main payload to be processed
    - metadata: Optional tracking information

    Example:
        {
            "event_type": "example",
            "message": "Hello, World!",
            "metadata": {"source": "test"}
        }
    """

    event_type: Literal["example"] = Field(
        default="example",
        description="Event type identifier (always 'example' for this schema)",
    )
    message: str = Field(
        ...,
        description="The message to be processed by the workflow",
        min_length=1,
    )
    metadata: Optional[dict] = Field(
        default=None,
        description="Optional metadata for tracking and debugging",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "event_type": "example",
                "message": "Hello, World!",
                "metadata": {"source": "test"},
            }
        }
    }
