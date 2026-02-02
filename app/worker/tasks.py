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
from app.worker.config import celery_app
from app.workflows.registry import get_workflow

# Import example workflow to ensure it's registered
import app.workflows.example_workflow  # noqa: F401


@celery_app.task(name="process_job")
def process_job(job_id: str):
    """Process a job through its designated workflow.

    This Celery task handles the asynchronous processing of jobs by:
    1. Retrieving the job from the database
    2. Creating a WorkflowContext
    3. Getting the appropriate workflow from the registry
    4. Executing the workflow
    5. Storing the results

    Args:
        job_id: Unique identifier of the job to process
    """
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

            # Create workflow context
            context = WorkflowContext(
                job_id=str(db_job.id),
                job_data=db_job.data,
            )
            context._on_progress = persist_progress

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

        except Exception as e:
            logger.exception(f"Failed to process job {job_id}")
            db_job.status = "failed"
            db_job.error = f"{type(e).__name__}: {str(e)}"
            db_job.completed_at = datetime.now()

        repository.update(obj=db_job)
