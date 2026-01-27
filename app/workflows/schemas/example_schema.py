"""
Example Job Schema Module

This module defines the schema for the example workflow.
It demonstrates the basic structure of a job schema.
"""

from typing import Literal, Optional

from pydantic import Field

from app.workflows.schemas.base import BaseJobSchema
from app.workflows.schemas.registry import register_schema


@register_schema("example")
class ExampleJobSchema(BaseJobSchema):
    """Schema for jobs processed by the example workflow.

    This schema demonstrates the basic structure of a job:
    - job_type: Identifies which workflow should process this job
    - message: The main payload to be processed
    - metadata: Optional tracking information for debugging and auditing

    Example:
        {
            "job_type": "example",
            "message": "Hello, World!",
            "metadata": {
                "user_id": "user_123",
                "source_system": "web_app",
                "request_id": "req_abc123",
                "environment": "production"
            }
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
        description=(
            "Optional metadata for tracking and debugging. "
            "Examples: user_id, source_system, request_id, correlation_id, "
            "tenant_id, environment, or any contextual information useful for "
            "monitoring, troubleshooting, and auditing."
        ),
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "job_type": "example",
                "message": "Hello, World!",
                "metadata": {
                    "user_id": "user_123",
                    "source_system": "web_app",
                    "request_id": "req_abc123",
                    "environment": "production",
                },
            }
        }
    }
