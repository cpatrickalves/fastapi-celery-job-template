"""
Workflow Task Processing Module

This module handles asynchronous processing of workflow jobs using Celery.
It manages the lifecycle of job processing from database retrieval through
workflow execution and result storage.
"""

from contextlib import contextmanager
from datetime import datetime

from app.core.context import WorkflowContext
from app.database.job import Job
from app.database.repository import GenericRepository
from app.database.session import db_session
from app.utils.logger import logger
from app.worker.cancel import clear_cancel, is_cancelled
from app.worker.config import celery_app, get_redis_client
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

        # If job was cancelled before worker picked it up, finalize immediately
        if db_job.status == "cancelled":
            redis_client = get_redis_client()
            db_job.status = "cancelled"
            db_job.cancelled_at = datetime.now()
            clear_cancel(redis_client, str(db_job.id))
            repository.update(obj=db_job)
            return {"job_id": job_id, "status": "cancelled"}

        # Atomically transition pending → processing to prevent race with cancellation
        transitioned = repository.conditional_update_status(
            id=job_id,
            from_status="pending",
            to_status="processing",
            started_at=datetime.now(),
        )
        if not transitioned:
            # Another process changed the status; re-read and handle
            session.refresh(db_job)
            if db_job.status == "cancelled":
                redis_client = get_redis_client()
                db_job.cancelled_at = datetime.now()
                clear_cancel(redis_client, str(db_job.id))
                repository.update(obj=db_job)
                return {"job_id": job_id, "status": "cancelled"}
            # Already processing (duplicate delivery) or other state — skip
            return {"job_id": job_id, "status": db_job.status}

        # Refresh in-memory object after the bulk UPDATE
        session.refresh(db_job)

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
            redis_client = get_redis_client()

            # Create workflow context
            context = WorkflowContext(
                job_id=str(db_job.id),
                job_data=db_job.data,
            )
            context._on_progress = persist_progress
            context._cancel_checker = lambda: is_cancelled(redis_client, str(db_job.id))

            # Get and execute workflow
            workflow = get_workflow(db_job.job_type)
            context = workflow.run(context)

            # If workflow didn't detect cancellation itself, re-check DB
            # (handles race where cancel was requested during process())
            if context.status not in ("cancelled", "failed"):
                session.refresh(db_job)
                if db_job.status == "cancelled":
                    context.cancel()

            # Build final values for conditional write
            final_values = {
                "result": context.result,
                "error": context.error,
                "context": context.model_dump(mode="json"),
                "completed_at": context.completed_at,
                "progress": 100.0 if context.status == "completed" else context.progress,
                "progress_message": context.progress_message,
            }
            if context.status == "cancelled":
                final_values["cancelled_at"] = datetime.now()
                clear_cancel(redis_client, str(db_job.id))

            # Conditional write: only update if still in "processing" state
            updated = repository.conditional_update_status(
                id=job_id,
                from_status="processing",
                to_status=context.status,
                **final_values,
            )
            if not updated:
                session.refresh(db_job)
                logger.warning(
                    f"Job {job_id} status changed to '{db_job.status}' during processing"
                )

            return {
                "job_id": job_id,
                "job_type": db_job.job_type,
                "status": context.status,
                "result": context.result,
            }

        except Exception as e:
            logger.exception(f"Failed to process job {job_id}")
            updated = repository.conditional_update_status(
                id=job_id,
                from_status="processing",
                to_status="failed",
                error=f"{type(e).__name__}: {str(e)}",
                completed_at=datetime.now(),
            )
            if not updated:
                session.refresh(db_job)
                logger.warning(
                    f"Job {job_id} exception handler: status is '{db_job.status}', "
                    f"skipping failed write"
                )

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
