# Architecture

## Overview

Launchpad implements a job-driven async processing architecture:

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
    logs: list[str] = []
    status: str = "pending"
    error: str | None = None

    def log(self, message: str) -> None: ...
    def set_result(self, result: Any) -> None: ...
    def complete(self) -> None: ...
    def fail(self, error: str) -> None: ...
```

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

### Schema Registry

Maps job_type to Pydantic schema for validation and OpenAPI docs:

```python
@register_schema("example")
class ExampleJobSchema(BaseJobSchema):
    message: str = Field(..., min_length=1)
```

### Workflow Registry

Maps job_type to workflow class for execution:

```python
@register_workflow("example")
class ExampleWorkflow(BaseWorkflow):
    job_schema = ExampleJobSchema

    def process(self, context: WorkflowContext) -> None:
        context.set_result({"done": True})
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
