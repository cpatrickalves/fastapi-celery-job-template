"""
Workflow Configuration Module

Central registration point for all workflows and their schemas.
Add new workflows here instead of using decorators or side-effect imports.
"""

_registered = False


def register_all_workflows() -> None:
    """Register all application workflows and their schemas.

    This function is idempotent — safe to call multiple times (e.g. from
    both tasks.py and endpoint.py in the same process during tests).

    To add a new workflow, import its class and schema, then call
    register_workflow() below.
    """
    global _registered
    if _registered:
        return

    from app.workflows.registry import register_workflow
    from app.workflows.example_workflow import ExampleWorkflow
    from app.workflows.schemas.example_schema import ExampleJobSchema

    register_workflow(
        job_type="example",
        workflow=ExampleWorkflow,
        schema=ExampleJobSchema,
    )

    _registered = True


def _reset_registered() -> None:
    """Reset the registration guard. For testing only."""
    global _registered
    _registered = False
