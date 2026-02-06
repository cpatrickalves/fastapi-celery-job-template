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
    status = Column(String, index=True)         # pending/processing/completed/failed
    error = Column(Text)                        # Error message if failed
    context = Column(JSON)                      # Full WorkflowContext for debugging
    created_at = Column(DateTime)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
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

    def log(self, message: str) -> None: ...
    def set_result(self, result: Any) -> None: ...
    def complete(self) -> None: ...
    def fail(self, error: str) -> None: ...
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

    def run(self, context: WorkflowContext) -> WorkflowContext:
        # Validates, executes hooks, handles errors
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

## Database Migrations

Using Alembic for schema evolution:

```bash
# Create migration
cd app && ./makemigration.sh "description"

# Apply migrations
./migrate.sh
```

Migrations are stored in `app/database/migrations/versions/`.
