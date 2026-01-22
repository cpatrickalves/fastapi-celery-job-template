"""
Workflow Task Processing Module

This module handles asynchronous processing of workflow events using Celery.
It manages the lifecycle of event processing from database retrieval through
workflow execution and result storage.
"""

import logging
from contextlib import contextmanager
from datetime import datetime

from core.context import WorkflowContext
from database.event import Event
from database.repository import GenericRepository
from database.session import db_session
from worker.config import celery_app
from workflows.registry import get_workflow

# Import example workflow to ensure it's registered
import workflows.example_workflow  # noqa: F401

logger = logging.getLogger(__name__)


@celery_app.task(name="process_incoming_event")
def process_incoming_event(event_id: str):
    """Process an incoming event through its designated workflow.

    This Celery task handles the asynchronous processing of events by:
    1. Retrieving the event from the database
    2. Creating a WorkflowContext
    3. Getting the appropriate workflow from the registry
    4. Executing the workflow
    5. Storing the results

    Args:
        event_id: Unique identifier of the event to process
    """
    with contextmanager(db_session)() as session:
        repository = GenericRepository(session=session, model=Event)

        # Retrieve event from database
        db_event = repository.get(id=event_id)
        if db_event is None:
            raise ValueError(f"Event with id {event_id} not found")

        # Update status to processing
        db_event.status = "processing"
        db_event.started_at = datetime.now()
        repository.update(obj=db_event)

        try:
            # Create workflow context
            context = WorkflowContext(
                event_id=str(db_event.id),
                event_data=db_event.data,
            )

            # Get and execute workflow
            workflow = get_workflow(db_event.event_type)
            context = workflow.run(context)

            # Store results
            db_event.result = context.result
            db_event.status = context.status
            db_event.error = context.error
            db_event.context = context.model_dump(mode="json")
            db_event.completed_at = context.completed_at

        except Exception as e:
            logger.exception(f"Failed to process event {event_id}")
            db_event.status = "failed"
            db_event.error = f"{type(e).__name__}: {str(e)}"
            db_event.completed_at = datetime.now()

        repository.update(obj=db_event)
