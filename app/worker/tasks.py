"""
Workflow Task Processing Module

This module handles asynchronous processing of workflow jobs using Celery.
It manages the lifecycle of job processing from database retrieval through
workflow execution and result storage.
"""

from contextlib import contextmanager
from datetime import datetime

import redis

from app.core.context import WorkflowContext
from app.database.job import Job
from app.database.repository import GenericRepository
from app.database.session import db_session
from app.services.cancellation import CancellationService
from app.utils.logger import logger
from app.worker.config import celery_app, get_redis_url
from app.workflows.registry import get_workflow

_dynamic_tasks: dict[str, object] = {}


def _process_job_impl(job_id: str, meta: dict | None = None):
    """Shared processing logic for all job tasks."""
    meta = meta or {}

    with contextmanager(db_session)() as session:
        repository = GenericRepository(session=session, model=Job)

        # Retrieve job from database
        db_job = repository.get(id=job_id)
        if db_job is None:
            raise ValueError(f"Job with id {job_id} not found")

        # Update status to processing
        db_job.status = "processing"
        db_job.started_at = datetime.now()
        repository.update(obj=db_job)

        try:
            # Progress persistence callback
            def persist_progress(value: float, message: str | None) -> None:
                try:
                    db_job.progress = value
                    db_job.progress_message = message
                    repository.update(obj=db_job)
                except Exception:
                    logger.warning(
                        f"Failed to persist progress for job {job_id}",
                        exc_info=True,
                    )

            # Set up cancellation checker
            redis_client = redis.Redis.from_url(get_redis_url())
            cancel_service = CancellationService(redis_client)

            # Create workflow context
            context = WorkflowContext(
                job_id=str(db_job.id),
                job_data=db_job.data,
            )
            context._on_progress = persist_progress
            context._cancel_checker = lambda: cancel_service.is_cancelled(
                str(db_job.id)
            )

            # Get and execute workflow
            workflow = get_workflow(db_job.job_type)
            context = workflow.run(context)

            # Store results
            db_job.result = context.result
            db_job.status = context.status
            db_job.error = context.error
            db_job.context = context.model_dump(mode="json")
            db_job.completed_at = context.completed_at
            db_job.progress = (
                100.0 if context.status == "completed" else context.progress
            )
            db_job.progress_message = context.progress_message

            # Clean up cancellation flag if job was cancelled
            if context.status == "cancelled":
                db_job.cancelled_at = datetime.now()
                cancel_service.clear(str(db_job.id))

            repository.update(obj=db_job)

            return {
                "job_id": job_id,
                "job_type": db_job.job_type,
                "status": context.status,
                "result": context.result,
            }

        except Exception as e:
            logger.exception(f"Failed to process job {job_id}")
            db_job.status = "failed"
            db_job.error = f"{type(e).__name__}: {str(e)}"
            db_job.completed_at = datetime.now()

            repository.update(obj=db_job)

            return {"job_id": job_id, "status": "failed", "error": str(e)}


@celery_app.task(name="process_job")
def process_job(job_id: str, meta: dict | None = None):
    """Fallback task for backward compatibility."""
    return _process_job_impl(job_id, meta)


def register_celery_task(job_type: str):
    """Register a Celery task named after the job_type."""
    if job_type in _dynamic_tasks:
        return
    task = celery_app.task(name=job_type)(_process_job_impl)
    _dynamic_tasks[job_type] = task


def clear_celery_tasks():
    """Clear dynamic tasks. For testing only."""
    _dynamic_tasks.clear()


from app.workflows.config import register_all_workflows  # noqa: E402

register_all_workflows()
