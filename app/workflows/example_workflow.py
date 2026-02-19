"""
Example Workflow Module

This module demonstrates a simple workflow implementation.
It shows the basic structure: inheriting from BaseWorkflow
and implementing process().
"""

import time

from app.core.context import WorkflowContext
from app.workflows.base import BaseWorkflow


class ExampleWorkflow(BaseWorkflow):
    """Example workflow that demonstrates the basic structure.

    This workflow performs a simple transformation on the input message:
    - Converts the message to uppercase
    - Counts the words
    - Returns structured result

    This serves as a template for creating new workflows.
    """

    def process(self, context: WorkflowContext) -> None:
        """Process the job by transforming the message.

        Args:
            context: The workflow context containing job data
        """
        job = context.job_data

        context.set_progress(10.0, "Received job")
        context.log(f"Received job with message: {job['message']}")

        # Simulate long-running process
        context.set_progress(20.0, "Processing simulation started")
        time.sleep(30)
        context.set_progress(50.0, "Processing simulation halfway")
        time.sleep(20)
        context.set_progress(80.0, "Processing simulation complete")

        # Perform transformation
        processed_message = job["message"].upper()
        word_count = len(job["message"].split())

        context.log(f"Processing complete: {word_count} words processed")
        context.set_progress(90.0, "Finalizing result")

        # Set the result
        context.set_result(
            {
                "original": job["message"],
                "processed": processed_message,
                "word_count": word_count,
                "status": "success",
            }
        )

    def before_process(self, context: WorkflowContext) -> None:
        """Hook executed before processing.

        Args:
            context: The workflow context
        """
        context.log("Initializing example workflow")

    def after_process(self, context: WorkflowContext) -> None:
        """Hook executed after successful processing.

        Args:
            context: The workflow context
        """
        context.log("Example workflow finished successfully")
