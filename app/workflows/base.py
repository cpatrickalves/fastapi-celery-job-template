"""
Base Workflow Module

This module defines the BaseWorkflow abstract class that all workflows must extend.
It provides lifecycle hooks (before_process, after_process, on_error) and handles
the execution flow automatically.
"""

from abc import ABC, abstractmethod
from typing import Optional, Type

from pydantic import BaseModel

from app.core.context import WorkflowContext
from app.utils.logger import logger


class BaseWorkflow(ABC):
    """Abstract base class for all workflows.

    Workflows must extend this class and implement the `process` method.
    The base class provides:
    - Automatic lifecycle management via `run()`
    - Optional hooks: before_process, after_process, on_error
    - Schema validation for job data
    - Error handling and status tracking

    Example:
        class MyWorkflow(BaseWorkflow):
            job_schema = MyJobSchema

            def process(self, context: WorkflowContext) -> None:
                # Your processing logic here
                data = context.job_data
                result = do_something(data)
                context.set_result(result)
    """

    job_schema: Optional[Type[BaseModel]] = None

    def run(self, context: WorkflowContext) -> WorkflowContext:
        """Execute the workflow with lifecycle hooks.

        This method orchestrates the full workflow execution:
        1. Validates job data against schema (if defined)
        2. Calls before_process hook
        3. Calls process (main logic)
        4. Calls after_process hook on success
        5. Calls on_error hook on failure

        Args:
            context: The workflow context containing job data

        Returns:
            WorkflowContext: The updated context with results or error
        """
        context.status = "processing"
        context.log(f"Starting workflow: {self.__class__.__name__}")

        try:
            # Validate job data if schema is defined
            if self.job_schema:
                self._validate_job(context)

            # Execute lifecycle
            self.before_process(context)
            self.process(context)
            self.after_process(context)

            # Mark as completed if not already failed
            if context.status != "failed":
                context.complete()
                context.log(f"Workflow completed: {self.__class__.__name__}")

        except Exception as e:
            error_msg = f"{type(e).__name__}: {str(e)}"
            logger.exception(f"Workflow failed: {error_msg}")
            context.fail(error_msg)
            self.on_error(context, e)

        return context

    def _validate_job(self, context: WorkflowContext) -> None:
        """Validate job data against the workflow's schema.

        Args:
            context: The workflow context containing job data

        Raises:
            ValidationError: If job data doesn't match schema
        """
        if self.job_schema:
            self.job_schema.model_validate(context.job_data)
            context.log("Job data validated successfully")

    @abstractmethod
    def process(self, context: WorkflowContext) -> None:
        """Main processing logic to be implemented by subclasses.

        This is where the actual workflow logic lives. Implementations should:
        - Read data from context.job_data
        - Perform processing
        - Store results via context.set_result()
        - Log progress via context.log()

        Args:
            context: The workflow context with job data and state
        """
        pass

    def before_process(self, context: WorkflowContext) -> None:
        """Hook called before process().

        Override this method to add pre-processing logic such as:
        - Setting up resources
        - Validating preconditions
        - Initializing state

        Args:
            context: The workflow context
        """
        pass

    def after_process(self, context: WorkflowContext) -> None:
        """Hook called after successful process().

        Override this method to add post-processing logic such as:
        - Cleanup
        - Sending notifications
        - Updating external systems

        Args:
            context: The workflow context
        """
        pass

    def on_error(self, context: WorkflowContext, error: Exception) -> None:
        """Hook called when an error occurs.

        Override this method to add custom error handling such as:
        - Sending alerts
        - Logging to external systems
        - Cleanup after failure

        Args:
            context: The workflow context
            error: The exception that was raised
        """
        pass
