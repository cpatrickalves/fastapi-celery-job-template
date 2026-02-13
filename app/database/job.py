"""
Job Database Model Module

This module defines the SQLAlchemy model for storing jobs in the database.
It provides storage for:
1. Raw job data (data column): Stores the original incoming job
2. Processing results (result column): Stores the workflow output
3. Status tracking: Processing state and timestamps
4. Context/logs (context column): Stores execution context for debugging
"""

import uuid
from datetime import datetime

from sqlalchemy import JSON, Column, DateTime, Float, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID

from app.database.session import Base


class Job(Base):
    """SQLAlchemy model for storing jobs and their processing results.

    This model serves as the primary storage for incoming jobs,
    their processing status, and results.

    Attributes:
        id: Unique identifier for the job
        job_type: Type of job, used to route to appropriate workflow
        data: Raw job data as received from the API
        result: Processing results from the workflow
        status: Current processing status (pending, processing, completed, failed)
        error: Error message if processing failed
        context: Full workflow context for debugging (logs, metadata)
        progress: Processing progress percentage (0-100)
        progress_message: Optional human-readable progress status message
        created_at: When the job was created
        started_at: When processing started
        completed_at: When processing completed
        updated_at: When the job was last updated
    """

    __tablename__ = "jobs"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid1,
        doc="Unique identifier for the job",
    )
    job_type = Column(
        String(150),
        nullable=False,
        index=True,
        doc="Type of job, used to route to appropriate workflow",
    )
    data = Column(
        JSON,
        doc="Raw job data as received from the API endpoint",
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
    progress = Column(
        Float,
        default=0.0,
        nullable=False,
        server_default="0",
        doc="Processing progress percentage (0-100)",
    )
    progress_message = Column(
        String(500),
        nullable=True,
        doc="Human-readable progress status message",
    )
    created_at = Column(
        DateTime,
        default=datetime.now,
        doc="Timestamp when the job was created",
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
    cancelled_at = Column(
        DateTime,
        nullable=True,
        doc="Timestamp when the job was cancelled",
    )
    updated_at = Column(
        DateTime,
        default=datetime.now,
        onupdate=datetime.now,
        doc="Timestamp when the job was last updated",
    )

    # Composite index for common queries
    __table_args__ = (Index("ix_jobs_status_created", "status", "created_at"),)
