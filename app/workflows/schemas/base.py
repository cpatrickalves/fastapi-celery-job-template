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
        metadata: Optional metadata for tracking, debugging, and auditing.
                  Common use cases:
                  - Request tracking: user_id, session_id, request_id
                  - Source identification: source_system, api_version, client_type
                  - Debugging: correlation_id, trace_id, environment
                  - Auditing: timestamp, ip_address, user_agent
                  - Business context: tenant_id, organization_id, region
    """

    job_type: str = Field(
        ...,
        description="Job type identifier used to route to the appropriate workflow",
    )
    metadata: Optional[dict] = Field(
        default=None,
        description=(
            "Optional metadata for tracking, debugging, and auditing. "
            "Use for request tracking (user_id, session_id), source identification "
            "(source_system, client_type), debugging (correlation_id, trace_id), "
            "or business context (tenant_id, organization_id)."
        ),
    )

    model_config = {
        "extra": "allow",  # Allow additional fields for flexibility
    }
