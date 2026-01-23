"""
Example Job Schema Module

This module defines the schema for the example workflow.
It demonstrates the basic structure of a job schema.
"""

from typing import Literal, Optional

from pydantic import Field

from schemas.base import BaseJobSchema
from schemas.registry import register_schema


@register_schema("example")
class ExampleJobSchema(BaseJobSchema):
    """Schema for jobs processed by the example workflow.

    This schema demonstrates the basic structure of a job:
    - job_type: Identifies which workflow should process this job
    - message: The main payload to be processed
    - metadata: Optional tracking information

    Example:
        {
            "job_type": "example",
            "message": "Hello, World!",
            "metadata": {"source": "test"}
        }
    """

    job_type: Literal["example"] = Field(
        default="example",
        description="Job type identifier (always 'example' for this schema)",
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
                "job_type": "example",
                "message": "Hello, World!",
                "metadata": {"source": "test"},
            }
        }
    }
