"""
Base Event Schema Module

This module defines the base schema for all events. All event schemas
should inherit from BaseEventSchema to ensure consistent structure.
"""

from typing import Optional

from pydantic import BaseModel, Field


class BaseEventSchema(BaseModel):
    """Base schema for all events.

    All event schemas should inherit from this class to ensure
    consistent structure and behavior.

    Attributes:
        event_type: Identifier for the type of event, used to route
                   to the appropriate workflow
        metadata: Optional metadata for tracking/debugging
    """

    event_type: str = Field(
        ...,
        description="Event type identifier used to route to the appropriate workflow",
    )
    metadata: Optional[dict] = Field(
        default=None,
        description="Optional metadata for tracking and debugging",
    )

    model_config = {
        "extra": "allow",  # Allow additional fields for flexibility
    }
