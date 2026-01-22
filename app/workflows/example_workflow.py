"""
Example Workflow Module

This module demonstrates a simple workflow implementation.
It shows the basic structure: inheriting from BaseWorkflow,
using the register_workflow decorator, and implementing process().
"""

import time

from core.context import WorkflowContext
from schemas.example_schema import ExampleEventSchema
from workflows.base import BaseWorkflow
from workflows.registry import register_workflow


@register_workflow("example")
class ExampleWorkflow(BaseWorkflow):
    """Example workflow that demonstrates the basic structure.

    This workflow performs a simple transformation on the input message:
    - Converts the message to uppercase
    - Counts the words
    - Returns structured result

    This serves as a template for creating new workflows.
    """

    event_schema = ExampleEventSchema

    def process(self, context: WorkflowContext) -> None:
        """Process the event by transforming the message.

        Args:
            context: The workflow context containing event data
        """
        event = context.event_data

        context.log(f"Received event with message: {event['message']}")

        # Simulate long-running process
        context.log("Starting 20-second processing simulation...")
        time.sleep(20)
        context.log("Processing simulation complete")

        # Perform transformation
        processed_message = event["message"].upper()
        word_count = len(event["message"].split())

        context.log(f"Processing complete: {word_count} words processed")

        # Set the result
        context.set_result(
            {
                "original": event["message"],
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
