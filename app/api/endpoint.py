"""
Job Submission Endpoint Module

This module defines the FastAPI endpoints for job ingestion and retrieval.
It implements the "accept-and-delegate" pattern where:
- Jobs are immediately accepted if valid
- Processing is handled asynchronously via Celery
- A 202 Accepted response indicates successful queueing

Endpoints:
- POST /{job_type}: Submit a new job for processing (typed per job_type)
- GET /{job_id}: Retrieve job status and results
"""

import json
from http import HTTPStatus
from typing import Any, Callable, Type
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import Response

from app.database.job import Job
from app.database.repository import AsyncGenericRepository
from app.database.session import get_db
from app.schemas.base import BaseJobSchema
from app.schemas.registry import get_all_schemas
from app.worker.config import celery_app
from app.workflows.registry import workflow_exists

# Import schemas to ensure they're registered before endpoint generation
import app.schemas.example_schema  # noqa: F401

router = APIRouter()


class JobResponse(BaseModel):
    """Response model for job submission."""

    job_id: str
    status: str
    message: str


class JobStatusResponse(BaseModel):
    """Response model for job status query."""

    job_id: str
    job_type: str
    status: str
    result: Any | None = None
    error: str | None = None
    created_at: str | None = None
    started_at: str | None = None
    completed_at: str | None = None


def create_job_endpoint(
    job_type: str, schema_class: Type[BaseJobSchema]
) -> Callable[..., Response]:
    """Factory function to create a typed endpoint for a specific job type.

    Args:
        job_type: The job type identifier
        schema_class: The Pydantic schema class for this job type

    Returns:
        A FastAPI endpoint function with the correct type annotations
    """

    async def endpoint(
        data: BaseJobSchema,  # Will be overwritten by __annotations__
        session: AsyncSession = Depends(get_db),
    ) -> Response:
        """Submit a job for asynchronous processing."""
        # Convert validated Pydantic model to dict for storage
        job_data = data.model_dump(mode="json")

        # Verify workflow exists for this job type
        if not workflow_exists(job_type):
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail=f"No workflow registered for job_type '{job_type}'",
            )

        # Store job in database
        repository = AsyncGenericRepository(session=session, model=Job)
        job = Job(data=job_data, job_type=job_type)
        await repository.create(obj=job)

        # Queue processing task
        celery_app.send_task("process_job", args=[str(job.id)])

        # Return acceptance response
        return Response(
            content=json.dumps(
                {
                    "job_id": str(job.id),
                    "status": "pending",
                    "message": f"Job '{job_type}' accepted for processing",
                }
            ),
            status_code=HTTPStatus.ACCEPTED,
            media_type="application/json",
        )

    # Set dynamic type annotation for FastAPI to use in OpenAPI generation
    endpoint.__annotations__ = {
        "data": schema_class,
        "session": AsyncSession,
        "return": Response,
    }
    endpoint.__name__ = f"submit_{job_type}_job"
    endpoint.__doc__ = f"Submit a {job_type} job for asynchronous processing."

    return endpoint


def register_job_endpoints() -> None:
    """Register a typed endpoint for each registered schema.

    This function iterates over all registered schemas and creates
    a dedicated POST endpoint for each job type with proper OpenAPI
    documentation.
    """
    schemas = get_all_schemas()

    for job_type, schema_class in schemas.items():
        endpoint_func = create_job_endpoint(job_type, schema_class)

        # Extract description from schema docstring or use default
        description = (
            schema_class.__doc__
            or f"Submit a {job_type} job for asynchronous processing."
        )

        router.add_api_route(
            path=f"/{job_type}",
            endpoint=endpoint_func,
            methods=["POST"],
            response_model=JobResponse,
            status_code=HTTPStatus.ACCEPTED,
            tags=[job_type],
            summary=f"Submit {job_type} job",
            description=description,
        )


# Register all job type endpoints
register_job_endpoints()


@router.get("/{job_id}", response_model=JobStatusResponse, tags=["jobs"])
async def get_job_status(
    job_id: UUID,
    session: AsyncSession = Depends(get_db),
) -> JobStatusResponse:
    """Get the status and result of a job.

    Args:
        job_id: The UUID of the job to retrieve
        session: Database session injected by FastAPI dependency

    Returns:
        JobStatusResponse: The job status and results

    Raises:
        HTTPException: 404 if job not found
    """
    repository = AsyncGenericRepository(session=session, model=Job)
    job = await repository.get(id=job_id)

    if job is None:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail=f"Job with id '{job_id}' not found",
        )

    return JobStatusResponse(
        job_id=str(job.id),
        job_type=job.job_type,
        status=job.status,
        result=job.result,
        error=job.error,
        created_at=job.created_at.isoformat() if job.created_at else None,
        started_at=job.started_at.isoformat() if job.started_at else None,
        completed_at=job.completed_at.isoformat() if job.completed_at else None,
    )
