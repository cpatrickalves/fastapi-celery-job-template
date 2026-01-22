"""
Workflow Context Module

This module defines the WorkflowContext class that carries state through
workflow execution. It provides a simplified container for event data,
results, logging, and status tracking.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class WorkflowContext(BaseModel):
    """Context object passed through workflow execution.

    This class serves as the primary state container during workflow processing.
    It holds the event data, accumulates results, tracks status, and provides
    logging capabilities.

    Attributes:
        event_id: Unique identifier of the event being processed
        event_data: The validated event data from the request
        result: Processing result set by the workflow
        metadata: Additional metadata for tracking/debugging
        logs: List of log messages generated during processing
        started_at: Timestamp when processing started
        completed_at: Timestamp when processing completed
        status: Current status (pending, processing, completed, failed)
        error: Error message if processing failed
    """

    event_id: str
    event_data: dict[str, Any]
    result: Any | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    logs: list[str] = Field(default_factory=list)
    started_at: datetime = Field(default_factory=datetime.now)
    completed_at: datetime | None = None
    status: str = "pending"
    error: str | None = None

    def log(self, message: str) -> None:
        """Add a log message to the context.

        Args:
            message: The log message to record
        """
        timestamp = datetime.now().isoformat()
        self.logs.append(f"[{timestamp}] {message}")

    def set_result(self, result: Any) -> None:
        """Set the processing result.

        Args:
            result: The result data from workflow processing
        """
        self.result = result

    def set_error(self, error: str) -> None:
        """Set an error message and mark status as failed.

        Args:
            error: The error message describing what went wrong
        """
        self.error = error
        self.status = "failed"

    def complete(self) -> None:
        """Mark the context as completed successfully."""
        self.status = "completed"
        self.completed_at = datetime.now()

    def fail(self, error: str) -> None:
        """Mark the context as failed with an error message.

        Args:
            error: The error message describing the failure
        """
        self.set_error(error)
        self.completed_at = datetime.now()
