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
from workflows.config import register_all_workflows
from workflows.registry import get_workflow, list_workflows

register_all_workflows()

from playground.utils.job_loader import JobLoader

logging.basicConfig(level=logging.INFO)
nest_asyncio.apply()


def run_workflow(job_type: str, job_data: dict) -> WorkflowContext:
    """Run a workflow with the given job data.

    Args:
        job_type: The type of workflow to run
        job_data: The job data to process

    Returns:
        WorkflowContext: The completed context with results
    """
    # Create context
    context = WorkflowContext(
        job_id="playground-test",
        job_data=job_data,
    )

    # Get and run workflow
    workflow = get_workflow(job_type)
    return workflow.run(context)


if __name__ == "__main__":
    # List available workflows
    print("Available workflows:", list_workflows())
    print()

    # Load and run example job
    job = JobLoader.load_job(job_key="example_job")
    print(f"Loaded job: {job}")
    print()

    # Run workflow
    result = run_workflow(job["job_type"], job)

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
