"""
Tests for BaseWorkflow.

Tests the workflow execution lifecycle including hooks,
validation, and error handling.
"""

from typing import Any, Literal

import pytest
from pydantic import Field, ValidationError

from app.core.context import WorkflowContext
from app.workflows.schemas.base import BaseJobSchema
from app.workflows.base import BaseWorkflow


class TestWorkflowExecution:
    """Tests for workflow execution lifecycle."""

    def test_workflow_run_completes_successfully(
        self, sample_job_id: str, sample_job_data: dict[str, Any]
    ) -> None:
        """run() should complete workflow and set status to 'completed'."""

        class SimpleWorkflow(BaseWorkflow):
            def process(self, context: WorkflowContext) -> None:
                context.set_result({"done": True})

        workflow = SimpleWorkflow()
        context = WorkflowContext(job_id=sample_job_id, job_data=sample_job_data)

        result = workflow.run(context)

        assert result.status == "completed"
        assert result.result == {"done": True}
        assert result.completed_at is not None

    def test_workflow_run_sets_processing_status(
        self, sample_job_id: str, sample_job_data: dict[str, Any]
    ) -> None:
        """run() should set status to 'processing' during execution."""
        status_during_process = None

        class StatusCheckWorkflow(BaseWorkflow):
            def process(self, context: WorkflowContext) -> None:
                nonlocal status_during_process
                status_during_process = context.status

        workflow = StatusCheckWorkflow()
        context = WorkflowContext(job_id=sample_job_id, job_data=sample_job_data)

        workflow.run(context)

        assert status_during_process == "processing"

    def test_workflow_run_logs_start_and_completion(
        self, sample_job_id: str, sample_job_data: dict[str, Any]
    ) -> None:
        """run() should log workflow start and completion."""

        class LoggingWorkflow(BaseWorkflow):
            def process(self, context: WorkflowContext) -> None:
                pass

        workflow = LoggingWorkflow()
        context = WorkflowContext(job_id=sample_job_id, job_data=sample_job_data)

        workflow.run(context)

        log_text = " ".join(context.logs)
        assert "Starting workflow" in log_text
        assert "completed" in log_text.lower()


class TestWorkflowHooks:
    """Tests for workflow lifecycle hooks."""

    def test_before_process_called_before_process(
        self, sample_job_id: str, sample_job_data: dict[str, Any]
    ) -> None:
        """before_process() should be called before process()."""
        call_order: list[str] = []

        class HookWorkflow(BaseWorkflow):
            def before_process(self, context: WorkflowContext) -> None:
                call_order.append("before")

            def process(self, context: WorkflowContext) -> None:
                call_order.append("process")

        workflow = HookWorkflow()
        context = WorkflowContext(job_id=sample_job_id, job_data=sample_job_data)

        workflow.run(context)

        assert call_order == ["before", "process"]

    def test_after_process_called_after_process(
        self, sample_job_id: str, sample_job_data: dict[str, Any]
    ) -> None:
        """after_process() should be called after process()."""
        call_order: list[str] = []

        class HookWorkflow(BaseWorkflow):
            def process(self, context: WorkflowContext) -> None:
                call_order.append("process")

            def after_process(self, context: WorkflowContext) -> None:
                call_order.append("after")

        workflow = HookWorkflow()
        context = WorkflowContext(job_id=sample_job_id, job_data=sample_job_data)

        workflow.run(context)

        assert call_order == ["process", "after"]

    def test_full_lifecycle_order(
        self, sample_job_id: str, sample_job_data: dict[str, Any]
    ) -> None:
        """All hooks should be called in correct order."""
        call_order: list[str] = []

        class FullHookWorkflow(BaseWorkflow):
            def before_process(self, context: WorkflowContext) -> None:
                call_order.append("before")

            def process(self, context: WorkflowContext) -> None:
                call_order.append("process")

            def after_process(self, context: WorkflowContext) -> None:
                call_order.append("after")

        workflow = FullHookWorkflow()
        context = WorkflowContext(job_id=sample_job_id, job_data=sample_job_data)

        workflow.run(context)

        assert call_order == ["before", "process", "after"]


class TestWorkflowErrorHandling:
    """Tests for workflow error handling."""

    def test_exception_in_process_marks_failed(
        self, sample_job_id: str, sample_job_data: dict[str, Any]
    ) -> None:
        """Exception in process() should mark context as failed."""

        class FailingWorkflow(BaseWorkflow):
            def process(self, context: WorkflowContext) -> None:
                raise ValueError("Processing failed")

        workflow = FailingWorkflow()
        context = WorkflowContext(job_id=sample_job_id, job_data=sample_job_data)

        result = workflow.run(context)

        assert result.status == "failed"
        assert "ValueError" in result.error
        assert "Processing failed" in result.error

    def test_on_error_called_on_exception(
        self, sample_job_id: str, sample_job_data: dict[str, Any]
    ) -> None:
        """on_error() should be called when exception occurs."""
        error_received = None

        class ErrorHandlerWorkflow(BaseWorkflow):
            def process(self, context: WorkflowContext) -> None:
                raise RuntimeError("Test error")

            def on_error(self, context: WorkflowContext, error: Exception) -> None:
                nonlocal error_received
                error_received = error

        workflow = ErrorHandlerWorkflow()
        context = WorkflowContext(job_id=sample_job_id, job_data=sample_job_data)

        workflow.run(context)

        assert error_received is not None
        assert isinstance(error_received, RuntimeError)

    def test_after_process_not_called_on_error(
        self, sample_job_id: str, sample_job_data: dict[str, Any]
    ) -> None:
        """after_process() should not be called when process() raises."""
        after_called = False

        class FailingWorkflow(BaseWorkflow):
            def process(self, context: WorkflowContext) -> None:
                raise Exception("Fail")

            def after_process(self, context: WorkflowContext) -> None:
                nonlocal after_called
                after_called = True

        workflow = FailingWorkflow()
        context = WorkflowContext(job_id=sample_job_id, job_data=sample_job_data)

        workflow.run(context)

        assert after_called is False


class TestWorkflowSchemaValidation:
    """Tests for job schema validation in workflows."""

    def test_workflow_validates_job_data_against_schema(
        self, sample_job_id: str
    ) -> None:
        """Workflow should validate job_data against job_schema if defined."""

        class TestSchema(BaseJobSchema):
            job_type: Literal["test"] = "test"
            message: str = Field(..., min_length=1)

        class ValidatingWorkflow(BaseWorkflow):
            job_schema = TestSchema

            def process(self, context: WorkflowContext) -> None:
                context.set_result({"validated": True})

        workflow = ValidatingWorkflow()
        valid_data = {"job_type": "test", "message": "Hello"}
        context = WorkflowContext(job_id=sample_job_id, job_data=valid_data)

        result = workflow.run(context)

        assert result.status == "completed"
        assert "validated successfully" in " ".join(result.logs)

    def test_workflow_fails_on_invalid_schema(self, sample_job_id: str) -> None:
        """Workflow should fail if job_data doesn't match schema."""

        class StrictSchema(BaseJobSchema):
            job_type: Literal["strict"] = "strict"
            required_field: str

        class StrictWorkflow(BaseWorkflow):
            job_schema = StrictSchema

            def process(self, context: WorkflowContext) -> None:
                pass

        workflow = StrictWorkflow()
        invalid_data = {"job_type": "strict"}  # missing required_field
        context = WorkflowContext(job_id=sample_job_id, job_data=invalid_data)

        result = workflow.run(context)

        assert result.status == "failed"
        assert result.error is not None

    def test_workflow_without_schema_skips_validation(
        self, sample_job_id: str, sample_job_data: dict[str, Any]
    ) -> None:
        """Workflow without job_schema should skip validation."""

        class NoSchemaWorkflow(BaseWorkflow):
            job_schema = None

            def process(self, context: WorkflowContext) -> None:
                context.set_result({"no_validation": True})

        workflow = NoSchemaWorkflow()
        context = WorkflowContext(job_id=sample_job_id, job_data=sample_job_data)

        result = workflow.run(context)

        assert result.status == "completed"
