# Architecture

## Overview

FastAPI Celery Job Template implements a job-driven async processing architecture:

```
┌─────────────────────────────────────────────────────────────┐
│                      Client Request                          │
│               POST /jobs/{job_type} + JSON                   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      FastAPI Layer                           │
│  • Validate against typed Pydantic schema                    │
│  • Store Job in PostgreSQL (status=pending)                  │
│  • Queue Celery task                                         │
│  • Return 202 Accepted with job_id                           │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Redis Message Queue                       │
│                   Task: process_job(job_id)                  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     Celery Worker                            │
│  • Fetch Job from DB                                         │
│  • Create WorkflowContext                                    │
│  • Execute: workflow.run(context)                            │
│  • Store result in DB (status=completed/failed)              │
└─────────────────────────────────────────────────────────────┘
```

---

## Core Components

### Job Model

Stores all job data and processing results:

```python
class Job(Base):
    __tablename__ = "jobs"

    id = Column(UUID, primary_key=True)
    job_type = Column(String, index=True)      # Routes to workflow
    data = Column(JSON)                         # Input data
    result = Column(JSON)                       # Processing result
    status = Column(String, index=True)         # pending/processing/completed/failed/cancelled
    error = Column(Text)                        # Error message if failed
    context = Column(JSON)                      # Full WorkflowContext for debugging
    progress = Column(Float, default=0.0)       # Progress percentage (0-100)
    progress_message = Column(String)           # Human-readable progress status
    created_at = Column(DateTime)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)             # Set for all terminal states
    cancelled_at = Column(DateTime)             # Set when job is cancelled
```

### WorkflowContext

State container that flows through workflow execution:

```python
class WorkflowContext(BaseModel):
    job_id: str
    job_data: dict[str, Any]
    result: Any | None = None
    metadata: dict[str, Any] = {}        # Tracking/debugging metadata
    logs: list[str] = []
    status: str = "pending"
    error: str | None = None
    progress: float = 0.0
    progress_message: str | None = None

    def log(self, message: str) -> None: ...
    def set_result(self, result: Any) -> None: ...
    def set_progress(self, value: float, message: str | None = None) -> None: ...
    def complete(self) -> None: ...
    def fail(self, error: str) -> None: ...
    def cancel(self) -> None: ...
```

The `metadata` field can store contextual information such as:
- **Request tracking**: `user_id`, `session_id`, `request_id`
- **Source identification**: `source_system`, `api_version`, `client_type`
- **Debugging**: `correlation_id`, `trace_id`, `environment`
- **Auditing**: `timestamp`, `ip_address`, `user_agent`
- **Business context**: `tenant_id`, `organization_id`, `region`

### BaseWorkflow

Abstract base class for all workflows:

```python
class BaseWorkflow(ABC):
    job_schema: Type[BaseModel] | None = None

    def is_cancelled(self) -> bool:
        """Check if cancellation was requested (for use inside process())."""
        ...

    def run(
        self,
        context: WorkflowContext,
        cancel_checker: Callable[[], bool] | None = None,
        on_progress: Callable[[float, str | None], None] | None = None,
    ) -> WorkflowContext:
        # Validates, executes hooks, checks cancellation, handles errors
        ...

    @abstractmethod
    def process(self, context: WorkflowContext) -> None:
        """Implement your processing logic here."""
        pass

    def before_process(self, context) -> None: pass
    def after_process(self, context) -> None: pass
    def on_error(self, context, error) -> None: pass
```

---

## Registry System

All workflows and schemas are registered centrally in `app/workflows/config.py` via explicit `register_workflow()` calls. This replaces decorator-based registration and enables feature flags.

### Schema Definition

Schemas define validation and OpenAPI docs per job_type:

```python
class ExampleJobSchema(BaseJobSchema):
    job_type: Literal["example"] = "example"
    message: str = Field(..., min_length=1)
    metadata: Optional[dict] = Field(
        default=None,
        description="Optional metadata for tracking and debugging"
    )
```

All schemas inherit from `BaseJobSchema`, which provides the `job_type` and `metadata` fields.

### Workflow Definition

Workflow classes contain the processing logic:

```python
class ExampleWorkflow(BaseWorkflow):
    def process(self, context: WorkflowContext) -> None:
        context.set_result({"done": True})
```

### Central Registration

Workflows and schemas are wired together in `app/workflows/config.py`:

```python
from app.workflows.registry import register_workflow

register_workflow(
    job_type="example",
    workflow=ExampleWorkflow,
    schema=ExampleJobSchema,
)
```

---

## Worker System

### Celery Task

```python
@celery_app.task(name="process_job")
def process_job(job_id: str):
    # 1. Fetch job from DB
    # 2. Update status to "processing"
    # 3. Create WorkflowContext
    # 4. Get workflow from registry
    # 5. Execute workflow.run(context)
    # 6. Store result/error in DB
```

### Scaling

Add more workers for increased throughput:

```yaml
# docker-compose.yml
celery_worker:
  deploy:
    replicas: 3
```

---

## Job Cancellation

Jobs can be cancelled at any point before they reach a terminal state (`completed`, `failed`, `cancelled`). Cancellation uses a cooperative model -- running tasks are not forcefully killed.

### Cancel Flow

```
POST /jobs/{job_id}/cancel
        │
        ▼
┌───────────────────────────────────────────────────┐
│  Atomic UPDATE: status → "cancelled"              │
│  WHERE status NOT IN (completed, failed, cancelled)│
│  Sets cancelled_at + completed_at                 │
│  Commits to DB immediately                        │
└───────────────────────────────────────────────────┘
        │
        ▼ (best-effort, errors logged but not raised)
┌───────────────────────────────────────────────────┐
│  1. Set Redis cancellation flag                   │
│  2. Revoke Celery task (cooperative, no SIGTERM)  │
└───────────────────────────────────────────────────┘
        │
        ▼
  Return 200 { job_id, status: "cancelled" }
```

### How the Worker Detects Cancellation

The worker checks for cancellation at multiple points:

1. **Before processing**: If the job is already `cancelled` when the worker picks it up, it finalizes immediately
2. **During pending-to-processing transition**: Uses a conditional UPDATE (`WHERE status = 'pending'`). If the transition fails (cancel arrived first), the worker exits
3. **Between lifecycle hooks**: `BaseWorkflow.run()` calls `is_cancelled()` after `before_process()` and after `process()`
4. **Inside `process()`**: Workflow authors can call `self.is_cancelled()` for long-running operations
5. **After workflow completes**: The worker re-reads the job from the DB. If the status was changed to `cancelled` during processing, it respects the DB state

### Conditional Final Write

The worker never unconditionally overwrites the job status. Both the success path and the exception handler use `conditional_update_status(from_status="processing")`. If the cancel endpoint already set the status to `cancelled`, the conditional write returns 0 affected rows and the worker logs a warning.

### Cancellation in Custom Workflows

For long-running workflows, check `self.is_cancelled()` inside `process()`:

```python
class MyWorkflow(BaseWorkflow):
    def process(self, context: WorkflowContext) -> None:
        for chunk in large_dataset:
            if self.is_cancelled():
                return  # BaseWorkflow.run() will call context.cancel()
            process(chunk)
            context.set_progress(...)
```

### Status Transitions

```
pending ──→ processing ──→ completed
   │            │
   │            ├──→ failed
   │            │
   └────────────┴──→ cancelled
```

Terminal states (`completed`, `failed`, `cancelled`) cannot be changed.

### Force Termination

The cancel endpoint accepts an optional `force=true` query parameter:

```
POST /jobs/{job_id}/cancel?force=true
```

When `force=true`, the endpoint sends `SIGTERM` to the worker process via Celery's `revoke(terminate=True)` in addition to the cooperative cancellation steps. This is a **last resort** for tasks that are stuck and ignoring cooperative cancellation.

**Caveats:**
- SIGTERM kills the **worker OS process**, not the individual task. If the worker picked up a different task, it kills the wrong one.
- The worker process will be restarted by the container orchestrator (Docker, Kubernetes), but any in-progress work on that process is lost.
- Default (`force=false`) cooperative cancellation is sufficient for well-behaved workflows that check `self.is_cancelled()`.

---

## Database Migrations

Using Alembic for schema evolution:

```bash
# Create migration
cd app && ./makemigration.sh "description"

# Apply migrations
./migrate.sh
```

Migrations are stored in `app/database/migrations/versions/`.
