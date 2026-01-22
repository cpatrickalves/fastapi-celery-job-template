"""
Workflow Playground

This playground is used to test workflows locally without Docker or database.
It demonstrates the simplified workflow pattern with direct execution.
"""

import logging
import sys
from pathlib import Path

# Add app and playground directories to path for imports
sys.path.append(str(Path(__file__).parent.parent / "app"))
sys.path.append(str(Path(__file__).parent.parent))

import nest_asyncio

from core.context import WorkflowContext
from workflows.registry import get_workflow, list_workflows

# Import workflows to ensure they're registered
import workflows.example_workflow  # noqa: F401

from playground.utils.event_loader import EventLoader

logging.basicConfig(level=logging.INFO)
nest_asyncio.apply()


def run_workflow(event_type: str, event_data: dict) -> WorkflowContext:
    """Run a workflow with the given event data.

    Args:
        event_type: The type of workflow to run
        event_data: The event data to process

    Returns:
        WorkflowContext: The completed context with results
    """
    # Create context
    context = WorkflowContext(
        event_id="playground-test",
        event_data=event_data,
    )

    # Get and run workflow
    workflow = get_workflow(event_type)
    return workflow.run(context)


if __name__ == "__main__":
    # List available workflows
    print("Available workflows:", list_workflows())
    print()

    # Load and run example event
    event = EventLoader.load_event(event_key="example_event")
    print(f"Loaded event: {event}")
    print()

    # Run workflow
    result = run_workflow(event["event_type"], event)

    # Print results
    print("=" * 50)
    print("WORKFLOW RESULT")
    print("=" * 50)
    print(f"Status: {result.status}")
    print(f"Result: {result.result}")
    print()
    print("Logs:")
    for log in result.logs:
        print(f"  {log}")
