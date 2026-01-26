"""
Tests for WorkflowContext.

Tests the core state container that flows through workflow execution,
including status transitions, logging, and result handling.
"""

from datetime import datetime
from typing import Any

import pytest

from app.core.context import WorkflowContext


class TestWorkflowContextCreation:
    """Tests for WorkflowContext initialization."""

    def test_create_context_with_required_fields(
        self, sample_job_id: str, sample_job_data: dict[str, Any]
    ) -> None:
        """Context should initialize with job_id and job_data."""
        context = WorkflowContext(job_id=sample_job_id, job_data=sample_job_data)

        assert context.job_id == sample_job_id
        assert context.job_data == sample_job_data
        assert context.status == "pending"
        assert context.result is None
        assert context.error is None
        assert context.logs == []

    def test_context_has_started_at_timestamp(
        self, sample_job_id: str, sample_job_data: dict[str, Any]
    ) -> None:
        """Context should have a started_at timestamp on creation."""
        before = datetime.now()
        context = WorkflowContext(job_id=sample_job_id, job_data=sample_job_data)
        after = datetime.now()

        assert before <= context.started_at <= after


class TestWorkflowContextStatusTransitions:
    """Tests for status transition methods."""

    def test_complete_sets_status_and_timestamp(
        self, sample_job_id: str, sample_job_data: dict[str, Any]
    ) -> None:
        """complete() should set status to 'completed' and record timestamp."""
        context = WorkflowContext(job_id=sample_job_id, job_data=sample_job_data)

        context.complete()

        assert context.status == "completed"
        assert context.completed_at is not None

    def test_fail_sets_status_error_and_timestamp(
        self, sample_job_id: str, sample_job_data: dict[str, Any]
    ) -> None:
        """fail() should set status to 'failed', record error and timestamp."""
        context = WorkflowContext(job_id=sample_job_id, job_data=sample_job_data)
        error_msg = "Something went wrong"

        context.fail(error_msg)

        assert context.status == "failed"
        assert context.error == error_msg
        assert context.completed_at is not None

    def test_set_error_marks_status_as_failed(
        self, sample_job_id: str, sample_job_data: dict[str, Any]
    ) -> None:
        """set_error() should set error message and mark status as failed."""
        context = WorkflowContext(job_id=sample_job_id, job_data=sample_job_data)

        context.set_error("Error occurred")

        assert context.error == "Error occurred"
        assert context.status == "failed"


class TestWorkflowContextResults:
    """Tests for result handling."""

    def test_set_result_stores_value(
        self, sample_job_id: str, sample_job_data: dict[str, Any]
    ) -> None:
        """set_result() should store the result value."""
        context = WorkflowContext(job_id=sample_job_id, job_data=sample_job_data)
        result = {"processed": True, "count": 42}

        context.set_result(result)

        assert context.result == result

    def test_set_result_accepts_various_types(
        self, sample_job_id: str, sample_job_data: dict[str, Any]
    ) -> None:
        """set_result() should accept different result types."""
        context = WorkflowContext(job_id=sample_job_id, job_data=sample_job_data)

        # Test with string
        context.set_result("success")
        assert context.result == "success"

        # Test with list
        context.set_result([1, 2, 3])
        assert context.result == [1, 2, 3]

        # Test with None
        context.set_result(None)
        assert context.result is None


class TestWorkflowContextLogging:
    """Tests for logging functionality."""

    def test_log_adds_timestamped_message(
        self, sample_job_id: str, sample_job_data: dict[str, Any]
    ) -> None:
        """log() should add a timestamped message to logs list."""
        context = WorkflowContext(job_id=sample_job_id, job_data=sample_job_data)

        context.log("Processing started")

        assert len(context.logs) == 1
        assert "Processing started" in context.logs[0]
        # Verify timestamp format [ISO timestamp]
        assert context.logs[0].startswith("[")

    def test_multiple_logs_preserve_order(
        self, sample_job_id: str, sample_job_data: dict[str, Any]
    ) -> None:
        """Multiple log() calls should preserve message order."""
        context = WorkflowContext(job_id=sample_job_id, job_data=sample_job_data)

        context.log("First")
        context.log("Second")
        context.log("Third")

        assert len(context.logs) == 3
        assert "First" in context.logs[0]
        assert "Second" in context.logs[1]
        assert "Third" in context.logs[2]
