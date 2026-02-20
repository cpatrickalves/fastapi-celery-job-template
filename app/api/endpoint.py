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
- POST /{job_id}/cancel: Cancel a pending or running job
"""

import asyncio
import json
from datetime import datetime
from http import HTTPStatus
from typing import Any, Callable, Type
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import Response

from app.database.job import Job
from app.database.repository import AsyncGenericRepository
from app.database.session import get_db
from app.utils.logger import logger
from app.worker.cancel import request_cancel
from app.worker.config import celery_app, get_redis_client
from app.workflows.config import register_all_workflows
from app.workflows.schemas.base import BaseJobSchema
from app.workflows.schemas.registry import get_all_schemas
from app.workflows.registry import workflow_exists

register_all_workflows()

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
    progress: float = 0.0
    progress_message: str | None = None
    result: Any | None = None
    error: str | None = None
    created_at: str | None = None
    started_at: str | None = None
    completed_at: str | None = None
    cancelled_at: str | None = None


class CancelJobResponse(BaseModel):
    """Response model for job cancellation.

    Status will be "cancelled" on success.
    """

    job_id: str
    status: str


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

        # Queue processing task (use job.id as Celery task_id for revocation)
        celery_app.send_task(
            job_type,
            args=[
                str(job.id),
                {
                    "job_type": job_type,
                    "job_data": job_data,
                },
            ],
            task_id=str(job.id),
        )

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
            tags=["Jobs"],
            summary=f"Submit {job_type} job",
            description=description,
        )


# Register all job type endpoints
register_job_endpoints()


@router.get("/{job_id}", response_model=JobStatusResponse, tags=["Jobs"])
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
    job = await repository.get(id=str(job_id))

    if job is None:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail=f"Job with id '{job_id}' not found",
        )

    created_at_value = (
        job.created_at.isoformat() if job.created_at is not None else None
    )
    started_at_value = (
        job.started_at.isoformat() if job.started_at is not None else None
    )
    completed_at_value = (
        job.completed_at.isoformat() if job.completed_at is not None else None
    )

    cancelled_at_value = (
        job.cancelled_at.isoformat() if job.cancelled_at is not None else None
    )

    return JobStatusResponse(
        job_id=str(job.id),
        job_type=str(job.job_type),
        status=str(job.status),
        progress=float(job.progress) if job.progress is not None else 0.0,
        progress_message=job.progress_message,
        result=job.result,
        error=str(job.error) if job.error is not None else None,
        created_at=created_at_value,
        started_at=started_at_value,
        completed_at=completed_at_value,
        cancelled_at=cancelled_at_value,
    )


# Non-cancellable terminal states
_NON_CANCELLABLE_STATUSES = {"completed", "failed", "cancelled"}


@router.post(
    "/{job_id}/cancel",
    response_model=CancelJobResponse,
    tags=["Jobs"],
    summary="Cancel a job",
    description="Cancel a pending or running job. Returns 409 if the job is already completed, failed, or cancelled.",
)
async def cancel_job(
    job_id: UUID,
    session: AsyncSession = Depends(get_db),
) -> CancelJobResponse:
    """Cancel a pending or running job using cooperative cancellation.

    Sets the job status to "cancelled" in the database, then makes best-effort
    attempts to set a Redis cancellation flag and revoke the Celery task.
    Running tasks are not forcefully terminated -- they detect cancellation
    via Redis flag checks between workflow lifecycle hooks.

    Args:
        job_id: The UUID of the job to cancel
        session: Database session injected by FastAPI dependency

    Returns:
        CancelJobResponse with job_id and status "cancelled"

    Raises:
        HTTPException: 404 if job not found, 409 if job is in a terminal state
    """
    # Atomic conditional UPDATE to avoid TOCTOU race
    result = await session.execute(
        update(Job)
        .where(Job.id == str(job_id))
        .where(Job.status.notin_(_NON_CANCELLABLE_STATUSES))
        .values(status="cancelled", cancelled_at=datetime.now(), completed_at=datetime.now())
    )
    await session.commit()  # Durably persist cancellation before side-effects

    if result.rowcount == 0:
        # Determine why: 404, idempotent, or 409
        repository = AsyncGenericRepository(session=session, model=Job)
        job = await repository.get(id=str(job_id))
        if job is None:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND,
                detail=f"Job with id '{job_id}' not found",
            )
        if job.status == "cancelled":
            return CancelJobResponse(job_id=str(job.id), status="cancelled")
        raise HTTPException(
            status_code=HTTPStatus.CONFLICT,
            detail="Job cannot be cancelled",
        )

    # Best-effort: set Redis flag + revoke Celery task
    # If these fail, the worker's post-workflow DB re-check catches the cancellation
    try:
        redis_client = get_redis_client()
        await asyncio.to_thread(request_cancel, redis_client, str(job_id))
    except Exception:
        logger.warning(f"Failed to set Redis cancel flag for job {job_id}", exc_info=True)

    try:
        await asyncio.to_thread(
            celery_app.control.revoke, str(job_id), terminate=False
        )
    except Exception:
        logger.warning(f"Failed to revoke Celery task for job {job_id}", exc_info=True)

    return CancelJobResponse(job_id=str(job_id), status="cancelled")
