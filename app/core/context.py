"""
Workflow Context Module

This module defines the WorkflowContext class that carries state through
workflow execution. It provides a simplified container for job data,
results, logging, and status tracking.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class WorkflowContext(BaseModel):
    """Context object passed through workflow execution.

    This class serves as the primary state container during workflow processing.
    It holds the job data, accumulates results, tracks status, and provides
    logging capabilities.

    Attributes:
        job_id: Unique identifier of the job being processed
        job_data: The validated job data from the request
        result: Processing result set by the workflow
        metadata: Additional metadata for tracking/debugging
        logs: List of log messages generated during processing
        started_at: Timestamp when processing started
        completed_at: Timestamp when processing completed
        status: Current status (pending, processing, completed, failed)
        error: Error message if processing failed
        progress: Processing progress percentage (0.0 to 100.0)
        progress_message: Optional human-readable progress status message
    """

    job_id: str
    job_data: dict[str, Any]
    result: Any | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    logs: list[str] = Field(default_factory=list)
    started_at: datetime = Field(default_factory=datetime.now)
    completed_at: datetime | None = None
    status: str = "pending"
    error: str | None = None
    progress: float = 0.0
    progress_message: str | None = None

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

    def set_progress(self, value: float, message: str | None = None) -> None:
        """Update progress percentage and optionally persist to storage.

        Args:
            value: Progress percentage (0.0 to 100.0)
            message: Optional human-readable progress message

        Raises:
            ValueError: If value is not between 0 and 100
        """
        if not 0.0 <= value <= 100.0:
            raise ValueError(f"Progress must be between 0 and 100, got {value}")

        self.progress = value
        self.progress_message = message
        self.log(f"Progress: {value:.1f}%" + (f" - {message}" if message else ""))

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

    def cancel(self) -> None:
        """Mark the context as cancelled by user request."""
        self.status = "cancelled"
        self.completed_at = datetime.now()
        self.log("Job cancelled by user request")
