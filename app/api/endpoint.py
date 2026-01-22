"""
Event Submission Endpoint Module

This module defines the FastAPI endpoints for event ingestion and retrieval.
It implements the "accept-and-delegate" pattern where:
- Events are immediately accepted if valid
- Processing is handled asynchronously via Celery
- A 202 Accepted response indicates successful queueing

Endpoints:
- POST /: Submit a new event for processing
- GET /{event_id}: Retrieve event status and results
"""

import json
from http import HTTPStatus
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from starlette.responses import Response

from database.event import Event
from database.repository import GenericRepository
from database.session import db_session
from schemas.registry import validate_event, schema_exists
from worker.config import celery_app
from workflows.registry import workflow_exists

# Import schemas to ensure they're registered
import schemas.example_schema  # noqa: F401

router = APIRouter()


class EventResponse(BaseModel):
    """Response model for event submission."""

    event_id: str
    status: str
    message: str


class EventStatusResponse(BaseModel):
    """Response model for event status query."""

    event_id: str
    event_type: str
    status: str
    result: Any | None = None
    error: str | None = None
    created_at: str | None = None
    started_at: str | None = None
    completed_at: str | None = None


@router.post("/", response_model=EventResponse, status_code=HTTPStatus.ACCEPTED)
def submit_event(
    data: dict,
    session: Session = Depends(db_session),
) -> Response:
    """Submit an event for asynchronous processing.

    This endpoint receives events, validates them against registered schemas,
    stores them in the database, and queues them for processing.

    Args:
        data: The event data containing at minimum an 'event_type' field
        session: Database session injected by FastAPI dependency

    Returns:
        Response: 202 Accepted response with event_id

    Raises:
        HTTPException: 400 if event_type is missing or invalid
        HTTPException: 422 if event data validation fails
    """
    # Extract and validate event_type
    event_type = data.get("event_type")
    if not event_type:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail="Event data must contain 'event_type' field",
        )

    # Check if workflow exists for this event type
    if not workflow_exists(event_type):
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail=f"No workflow registered for event_type '{event_type}'",
        )

    # Validate event data against schema if registered
    if schema_exists(event_type):
        try:
            validated = validate_event(data)
            event_data = validated.model_dump(mode="json")
        except Exception as e:
            raise HTTPException(
                status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
                detail=f"Event validation failed: {str(e)}",
            )
    else:
        event_data = data

    # Store event in database
    repository = GenericRepository(session=session, model=Event)
    event = Event(data=event_data, event_type=event_type)
    repository.create(obj=event)

    # Queue processing task
    celery_app.send_task(
        "process_incoming_event",
        args=[str(event.id)],
    )

    # Return acceptance response
    return Response(
        content=json.dumps({
            "event_id": str(event.id),
            "status": "pending",
            "message": "Event accepted for processing",
        }),
        status_code=HTTPStatus.ACCEPTED,
        media_type="application/json",
    )


@router.get("/{event_id}", response_model=EventStatusResponse)
def get_event_status(
    event_id: UUID,
    session: Session = Depends(db_session),
) -> EventStatusResponse:
    """Get the status and result of an event.

    Args:
        event_id: The UUID of the event to retrieve
        session: Database session injected by FastAPI dependency

    Returns:
        EventStatusResponse: The event status and results

    Raises:
        HTTPException: 404 if event not found
    """
    repository = GenericRepository(session=session, model=Event)
    event = repository.get(id=event_id)

    if event is None:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail=f"Event with id '{event_id}' not found",
        )

    return EventStatusResponse(
        event_id=str(event.id),
        event_type=event.event_type,
        status=event.status,
        result=event.result,
        error=event.error,
        created_at=event.created_at.isoformat() if event.created_at else None,
        started_at=event.started_at.isoformat() if event.started_at else None,
        completed_at=event.completed_at.isoformat() if event.completed_at else None,
    )
