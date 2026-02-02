"""
Tests for Workflow Registry.

Tests the registration and retrieval of workflows by job_type.
"""

import pytest

from app.core.context import WorkflowContext
from app.workflows.base import BaseWorkflow
from app.workflows.registry import (
    clear_registry,
    get_workflow,
    list_workflows,
    register_workflow,
    workflow_exists,
)


class TestWorkflowRegistration:
    """Tests for workflow registration."""

    def test_register_workflow(self) -> None:
        """register_workflow() should register a workflow class."""

        class TestWorkflow(BaseWorkflow):
            def process(self, context: WorkflowContext) -> None:
                pass

        register_workflow("test_job", workflow=TestWorkflow)

        assert workflow_exists("test_job")

    def test_get_workflow_returns_instance(self) -> None:
        """get_workflow() should return an instance of the registered workflow."""

        class MyWorkflow(BaseWorkflow):
            def process(self, context: WorkflowContext) -> None:
                pass

        register_workflow("my_job", workflow=MyWorkflow)

        workflow = get_workflow("my_job")

        assert isinstance(workflow, MyWorkflow)

    def test_register_duplicate_raises_error(self) -> None:
        """Registering the same job_type twice should raise ValueError."""

        class FirstWorkflow(BaseWorkflow):
            def process(self, context: WorkflowContext) -> None:
                pass

        class SecondWorkflow(BaseWorkflow):
            def process(self, context: WorkflowContext) -> None:
                pass

        register_workflow("duplicate", workflow=FirstWorkflow)

        with pytest.raises(ValueError, match="already registered"):
            register_workflow("duplicate", workflow=SecondWorkflow)


class TestWorkflowRetrieval:
    """Tests for workflow retrieval."""

    def test_get_workflow_unknown_raises_keyerror(self) -> None:
        """get_workflow() with unknown job_type should raise KeyError."""
        with pytest.raises(KeyError, match="No workflow registered"):
            get_workflow("unknown_job")

    def test_workflow_exists_returns_false_for_unknown(self) -> None:
        """workflow_exists() should return False for unregistered job_type."""
        assert workflow_exists("nonexistent") is False

    def test_workflow_exists_returns_true_for_registered(self) -> None:
        """workflow_exists() should return True for registered job_type."""

        class ExistsWorkflow(BaseWorkflow):
            def process(self, context: WorkflowContext) -> None:
                pass

        register_workflow("exists_test", workflow=ExistsWorkflow)

        assert workflow_exists("exists_test") is True


class TestWorkflowListing:
    """Tests for listing workflows."""

    def test_list_workflows_empty_initially(self) -> None:
        """list_workflows() should return empty list when no workflows registered."""
        assert list_workflows() == []

    def test_list_workflows_returns_registered_types(self) -> None:
        """list_workflows() should return all registered job_types."""

        class WorkflowA(BaseWorkflow):
            def process(self, context: WorkflowContext) -> None:
                pass

        class WorkflowB(BaseWorkflow):
            def process(self, context: WorkflowContext) -> None:
                pass

        register_workflow("job_a", workflow=WorkflowA)
        register_workflow("job_b", workflow=WorkflowB)

        workflows = list_workflows()

        assert "job_a" in workflows
        assert "job_b" in workflows
        assert len(workflows) == 2


class TestRegistryClear:
    """Tests for registry clearing."""

    def test_clear_registry_removes_all_workflows(self) -> None:
        """clear_registry() should remove all registered workflows."""

        class ToClearWorkflow(BaseWorkflow):
            def process(self, context: WorkflowContext) -> None:
                pass

        register_workflow("to_clear", workflow=ToClearWorkflow)

        assert workflow_exists("to_clear")

        clear_registry()

        assert workflow_exists("to_clear") is False
        assert list_workflows() == []
