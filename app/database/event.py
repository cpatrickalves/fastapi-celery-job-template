"""
Event Database Model Module

This module defines the SQLAlchemy model for storing events in the database.
It provides storage for:
1. Raw event data (data column): Stores the original incoming event
2. Processing results (result column): Stores the workflow output
3. Status tracking: Processing state and timestamps
4. Context/logs (context column): Stores execution context for debugging
"""

import uuid
from datetime import datetime

from sqlalchemy import JSON, Column, DateTime, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID

from database.session import Base


class Event(Base):
    """SQLAlchemy model for storing events and their processing results.

    This model serves as the primary storage for incoming events,
    their processing status, and results.

    Attributes:
        id: Unique identifier for the event
        event_type: Type of event, used to route to appropriate workflow
        data: Raw event data as received from the API
        result: Processing results from the workflow
        status: Current processing status (pending, processing, completed, failed)
        error: Error message if processing failed
        context: Full workflow context for debugging (logs, metadata)
        created_at: When the event was created
        started_at: When processing started
        completed_at: When processing completed
        updated_at: When the event was last updated
    """

    __tablename__ = "events"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid1,
        doc="Unique identifier for the event",
    )
    event_type = Column(
        String(150),
        nullable=False,
        index=True,
        doc="Type of event, used to route to appropriate workflow",
    )
    data = Column(
        JSON,
        doc="Raw event data as received from the API endpoint",
    )
    result = Column(
        JSON,
        nullable=True,
        doc="Processing results from the workflow",
    )
    status = Column(
        String(50),
        default="pending",
        nullable=False,
        index=True,
        doc="Current processing status (pending, processing, completed, failed)",
    )
    error = Column(
        Text,
        nullable=True,
        doc="Error message if processing failed",
    )
    context = Column(
        JSON,
        nullable=True,
        doc="Full workflow context for debugging (logs, metadata)",
    )
    created_at = Column(
        DateTime,
        default=datetime.now,
        doc="Timestamp when the event was created",
    )
    started_at = Column(
        DateTime,
        nullable=True,
        doc="Timestamp when processing started",
    )
    completed_at = Column(
        DateTime,
        nullable=True,
        doc="Timestamp when processing completed",
    )
    updated_at = Column(
        DateTime,
        default=datetime.now,
        onupdate=datetime.now,
        doc="Timestamp when the event was last updated",
    )

    # Composite index for common queries
    __table_args__ = (
        Index("ix_events_status_created", "status", "created_at"),
    )
