"""
Base Job Schema Module

This module defines the base schema for all jobs. All job schemas
should inherit from BaseJobSchema to ensure consistent structure.
"""

from typing import Optional

from pydantic import BaseModel, Field


class BaseJobSchema(BaseModel):
    """Base schema for all jobs.

    All job schemas should inherit from this class to ensure
    consistent structure and behavior.

    Attributes:
        job_type: Identifier for the type of job, used to route
                  to the appropriate workflow
        metadata: Optional metadata for tracking/debugging
    """

    job_type: str = Field(
        ...,
        description="Job type identifier used to route to the appropriate workflow",
    )
    metadata: Optional[dict] = Field(
        default=None,
        description="Optional metadata for tracking and debugging",
    )

    model_config = {
        "extra": "allow",  # Allow additional fields for flexibility
    }
