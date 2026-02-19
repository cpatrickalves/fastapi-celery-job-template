"""
Tests for job cancellation feature.

Tests cover:
- Cancellation Redis flag management functions
- WorkflowContext cancellation methods
- BaseWorkflow cancellation between lifecycle hooks
"""

from datetime import datetime
from typing import Any
from unittest.mock import MagicMock

import pytest

from app.core.context import WorkflowContext
from app.worker.cancel import (
    CANCEL_KEY_PREFIX,
    CANCEL_TTL,
    clear_cancel,
    is_cancelled,
    request_cancel,
)
from app.workflows.base import BaseWorkflow


# ---------- Cancellation Functions ----------


class TestCancellationFunctions:
    """Tests for cancellation Redis flag management functions."""

    def test_request_cancel_sets_redis_flag(self) -> None:
        """request_cancel() should set a Redis key with TTL."""
        mock_redis = MagicMock()

        request_cancel(mock_redis, "job-123")

        mock_redis.set.assert_called_once_with(
            f"{CANCEL_KEY_PREFIX}job-123", "1", ex=CANCEL_TTL
        )

    def test_is_cancelled_returns_true_when_flag_set(self) -> None:
        """is_cancelled() should return True when the Redis key exists."""
        mock_redis = MagicMock()
        mock_redis.exists.return_value = 1

        assert is_cancelled(mock_redis, "job-123") is True
        mock_redis.exists.assert_called_once_with(f"{CANCEL_KEY_PREFIX}job-123")

    def test_is_cancelled_returns_false_when_no_flag(self) -> None:
        """is_cancelled() should return False when the Redis key doesn't exist."""
        mock_redis = MagicMock()
        mock_redis.exists.return_value = 0

        assert is_cancelled(mock_redis, "job-123") is False

    def test_clear_cancel_deletes_redis_flag(self) -> None:
        """clear_cancel() should delete the Redis key."""
        mock_redis = MagicMock()

        clear_cancel(mock_redis, "job-123")

        mock_redis.delete.assert_called_once_with(f"{CANCEL_KEY_PREFIX}job-123")


# ---------- WorkflowContext Cancellation ----------


class TestWorkflowContextCancellation:
    """Tests for cancellation methods on WorkflowContext."""

    def test_check_cancelled_returns_false_without_checker(
        self, sample_job_id: str, sample_job_data: dict[str, Any]
    ) -> None:
        """check_cancelled() should return False when no checker is set."""
        context = WorkflowContext(job_id=sample_job_id, job_data=sample_job_data)

        assert context.check_cancelled() is False

    def test_check_cancelled_delegates_to_checker(
        self, sample_job_id: str, sample_job_data: dict[str, Any]
    ) -> None:
        """check_cancelled() should call and return the checker result."""
        context = WorkflowContext(job_id=sample_job_id, job_data=sample_job_data)
        context._cancel_checker = lambda: True

        assert context.check_cancelled() is True

    def test_check_cancelled_returns_false_from_checker(
        self, sample_job_id: str, sample_job_data: dict[str, Any]
    ) -> None:
        """check_cancelled() should return False when checker returns False."""
        context = WorkflowContext(job_id=sample_job_id, job_data=sample_job_data)
        context._cancel_checker = lambda: False

        assert context.check_cancelled() is False

    def test_cancel_sets_status_and_timestamp(
        self, sample_job_id: str, sample_job_data: dict[str, Any]
    ) -> None:
        """cancel() should set status to 'cancelled' and record timestamp."""
        context = WorkflowContext(job_id=sample_job_id, job_data=sample_job_data)

        context.cancel()

        assert context.status == "cancelled"
        assert context.completed_at is not None

    def test_cancel_logs_message(
        self, sample_job_id: str, sample_job_data: dict[str, Any]
    ) -> None:
        """cancel() should log a cancellation message."""
        context = WorkflowContext(job_id=sample_job_id, job_data=sample_job_data)

        context.cancel()

        assert any("cancelled" in log.lower() for log in context.logs)

    def test_cancel_checker_excluded_from_model_dump(
        self, sample_job_id: str, sample_job_data: dict[str, Any]
    ) -> None:
        """_cancel_checker should not appear in serialized output."""
        context = WorkflowContext(job_id=sample_job_id, job_data=sample_job_data)
        context._cancel_checker = lambda: False

        dumped = context.model_dump(mode="json")

        assert "_cancel_checker" not in dumped


# ---------- BaseWorkflow Cancellation ----------


class TestBaseWorkflowCancellation:
    """Tests for cancellation checks in BaseWorkflow.run()."""

    def test_cancellation_after_before_process_skips_process(
        self, sample_job_id: str, sample_job_data: dict[str, Any]
    ) -> None:
        """If cancelled after before_process(), process() should not run."""
        process_called = False
        cancel_after_before = False

        class CancelAfterBeforeWorkflow(BaseWorkflow):
            def before_process(self, context: WorkflowContext) -> None:
                nonlocal cancel_after_before
                cancel_after_before = True

            def process(self, context: WorkflowContext) -> None:
                nonlocal process_called
                process_called = True

        context = WorkflowContext(job_id=sample_job_id, job_data=sample_job_data)
        # Return True only after before_process has been called
        context._cancel_checker = lambda: cancel_after_before

        workflow = CancelAfterBeforeWorkflow()
        result = workflow.run(context)

        assert result.status == "cancelled"
        assert process_called is False

    def test_cancellation_after_process_skips_after_process(
        self, sample_job_id: str, sample_job_data: dict[str, Any]
    ) -> None:
        """If cancelled after process(), after_process() should not run."""
        after_called = False
        cancel_after_process = False

        class CancelAfterProcessWorkflow(BaseWorkflow):
            def process(self, context: WorkflowContext) -> None:
                nonlocal cancel_after_process
                cancel_after_process = True
                context.set_result({"partial": True})

            def after_process(self, context: WorkflowContext) -> None:
                nonlocal after_called
                after_called = True

        context = WorkflowContext(job_id=sample_job_id, job_data=sample_job_data)
        # Return True only after process has been called
        context._cancel_checker = lambda: cancel_after_process

        workflow = CancelAfterProcessWorkflow()
        result = workflow.run(context)

        assert result.status == "cancelled"
        assert after_called is False

    def test_no_cancellation_runs_full_lifecycle(
        self, sample_job_id: str, sample_job_data: dict[str, Any]
    ) -> None:
        """When not cancelled, full lifecycle should execute normally."""
        call_order: list[str] = []

        class FullLifecycleWorkflow(BaseWorkflow):
            def before_process(self, context: WorkflowContext) -> None:
                call_order.append("before")

            def process(self, context: WorkflowContext) -> None:
                call_order.append("process")

            def after_process(self, context: WorkflowContext) -> None:
                call_order.append("after")

        context = WorkflowContext(job_id=sample_job_id, job_data=sample_job_data)
        context._cancel_checker = lambda: False

        workflow = FullLifecycleWorkflow()
        result = workflow.run(context)

        assert call_order == ["before", "process", "after"]
        assert result.status == "completed"

    def test_cancelled_workflow_does_not_mark_completed(
        self, sample_job_id: str, sample_job_data: dict[str, Any]
    ) -> None:
        """A cancelled workflow should stay 'cancelled', not 'completed'."""

        class SimpleWorkflow(BaseWorkflow):
            def process(self, context: WorkflowContext) -> None:
                pass

        context = WorkflowContext(job_id=sample_job_id, job_data=sample_job_data)
        context._cancel_checker = lambda: True  # Immediately cancelled

        workflow = SimpleWorkflow()
        result = workflow.run(context)

        assert result.status == "cancelled"
        assert result.completed_at is not None
