"""
Tests for job cancellation feature.

Tests cover:
- Cancellation Redis flag management functions
- WorkflowContext cancellation methods
- BaseWorkflow cancellation between lifecycle hooks
- Worker task cancellation handling (_process_job_impl)
"""

from datetime import datetime
from typing import Any
from unittest.mock import MagicMock, patch

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


# ---------- Worker Task Cancellation ----------


class TestWorkerTaskCancellation:
    """Tests for _process_job_impl cancellation handling."""

    def _make_db_job(self, job_id, status="pending") -> MagicMock:
        """Create a mock DB job object."""
        job = MagicMock()
        job.id = job_id
        job.status = status
        job.data = {"job_type": "test", "message": "hello"}
        job.job_type = "test"
        job.started_at = None
        job.cancelled_at = None
        return job

    @patch("app.worker.tasks.get_redis_client")
    @patch("app.worker.tasks.clear_cancel")
    @patch("app.worker.tasks.db_session")
    def test_cancelling_job_finalized_before_processing(
        self, mock_db_session, mock_clear_cancel, mock_get_redis
    ) -> None:
        """Worker should finalize as cancelled if job is 'cancelling' at pickup."""
        from app.worker.tasks import _process_job_impl

        db_job = self._make_db_job("job-1", status="cancelling")
        mock_session = MagicMock()
        mock_repo = MagicMock()
        mock_repo.get.return_value = db_job

        # Patch the contextmanager and repository
        mock_db_session.return_value = iter([mock_session])
        mock_redis = MagicMock()
        mock_get_redis.return_value = mock_redis

        with patch("app.worker.tasks.GenericRepository", return_value=mock_repo):
            result = _process_job_impl("job-1")

        assert result["status"] == "cancelled"
        assert db_job.status == "cancelled"
        assert db_job.cancelled_at is not None
        mock_clear_cancel.assert_called_once_with(mock_redis, "job-1")

    @patch("app.worker.tasks.get_redis_client")
    @patch("app.worker.tasks.clear_cancel")
    @patch("app.worker.tasks.db_session")
    def test_cancelled_job_finalized_before_processing(
        self, mock_db_session, mock_clear_cancel, mock_get_redis
    ) -> None:
        """Worker should finalize if job is already 'cancelled' at pickup."""
        from app.worker.tasks import _process_job_impl

        db_job = self._make_db_job("job-2", status="cancelled")
        mock_session = MagicMock()
        mock_repo = MagicMock()
        mock_repo.get.return_value = db_job

        mock_db_session.return_value = iter([mock_session])
        mock_redis = MagicMock()
        mock_get_redis.return_value = mock_redis

        with patch("app.worker.tasks.GenericRepository", return_value=mock_repo):
            result = _process_job_impl("job-2")

        assert result["status"] == "cancelled"
        assert db_job.cancelled_at is not None

    @patch("app.worker.tasks.get_redis_client")
    @patch("app.worker.tasks.is_cancelled")
    @patch("app.worker.tasks.clear_cancel")
    @patch("app.worker.tasks.get_workflow")
    @patch("app.worker.tasks.db_session")
    def test_cancel_detected_after_workflow_via_db_recheck_cancelling(
        self,
        mock_db_session,
        mock_get_workflow,
        mock_clear_cancel,
        mock_is_cancelled,
        mock_get_redis,
    ) -> None:
        """Worker should detect cancel via DB re-check when status is 'cancelling'."""
        from app.worker.tasks import _process_job_impl

        db_job = self._make_db_job("job-3", status="processing")
        mock_session = MagicMock()
        mock_repo = MagicMock()
        mock_repo.get.return_value = db_job

        mock_db_session.return_value = iter([mock_session])
        mock_redis = MagicMock()
        mock_get_redis.return_value = mock_redis

        # Redis flag is NOT set (cancel arrived after Redis check but before DB write)
        mock_is_cancelled.return_value = False

        # Workflow completes normally (status="completed")
        class NormalWorkflow(BaseWorkflow):
            def process(self, context: WorkflowContext) -> None:
                context.set_result({"done": True})

        mock_workflow = NormalWorkflow()
        mock_get_workflow.return_value = mock_workflow

        # Simulate DB refresh showing "cancelling"
        def fake_refresh(obj):
            obj.status = "cancelling"

        mock_session.refresh.side_effect = fake_refresh

        with patch("app.worker.tasks.GenericRepository", return_value=mock_repo):
            result = _process_job_impl("job-3")

        assert result["status"] == "cancelled"
        assert db_job.status == "cancelled"
        mock_clear_cancel.assert_called_once()

    @patch("app.worker.tasks.get_redis_client")
    @patch("app.worker.tasks.is_cancelled")
    @patch("app.worker.tasks.clear_cancel")
    @patch("app.worker.tasks.get_workflow")
    @patch("app.worker.tasks.db_session")
    def test_cancel_detected_after_workflow_via_db_recheck_cancelled(
        self,
        mock_db_session,
        mock_get_workflow,
        mock_clear_cancel,
        mock_is_cancelled,
        mock_get_redis,
    ) -> None:
        """Worker should detect cancel via DB re-check when status is 'cancelled'."""
        from app.worker.tasks import _process_job_impl

        db_job = self._make_db_job("job-4", status="processing")
        mock_session = MagicMock()
        mock_repo = MagicMock()
        mock_repo.get.return_value = db_job

        mock_db_session.return_value = iter([mock_session])
        mock_redis = MagicMock()
        mock_get_redis.return_value = mock_redis

        mock_is_cancelled.return_value = False

        class NormalWorkflow(BaseWorkflow):
            def process(self, context: WorkflowContext) -> None:
                context.set_result({"done": True})

        mock_get_workflow.return_value = NormalWorkflow()

        # Simulate DB refresh showing "cancelled" (endpoint sets it directly now)
        def fake_refresh(obj):
            obj.status = "cancelled"

        mock_session.refresh.side_effect = fake_refresh

        with patch("app.worker.tasks.GenericRepository", return_value=mock_repo):
            result = _process_job_impl("job-4")

        assert result["status"] == "cancelled"
        assert db_job.status == "cancelled"
        mock_clear_cancel.assert_called_once()

    @patch("app.worker.tasks.get_redis_client")
    @patch("app.worker.tasks.clear_cancel")
    @patch("app.worker.tasks.db_session")
    def test_race_condition_cancel_during_pending_to_processing(
        self, mock_db_session, mock_clear_cancel, mock_get_redis
    ) -> None:
        """If cancel races with pending→processing transition, job should finalize as cancelled."""
        from app.worker.tasks import _process_job_impl

        db_job = self._make_db_job("job-5", status="pending")
        mock_session = MagicMock()
        mock_repo = MagicMock()
        mock_repo.get.return_value = db_job

        # conditional_update_status returns False — another process changed the status
        mock_repo.conditional_update_status.return_value = False

        mock_db_session.return_value = iter([mock_session])
        mock_redis = MagicMock()
        mock_get_redis.return_value = mock_redis

        # Simulate refresh showing status changed to "cancelling" by the cancel endpoint
        def fake_refresh(obj):
            obj.status = "cancelling"

        mock_session.refresh.side_effect = fake_refresh

        with patch("app.worker.tasks.GenericRepository", return_value=mock_repo):
            result = _process_job_impl("job-5")

        assert result["status"] == "cancelled"
        assert db_job.status == "cancelled"
        assert db_job.cancelled_at is not None
        mock_clear_cancel.assert_called_once_with(mock_redis, "job-5")
