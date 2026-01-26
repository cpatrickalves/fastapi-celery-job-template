# Development Guide

## Adding a New Job Type

### Step 1: Create Schema

```python
# app/schemas/my_schema.py
from typing import Literal

from pydantic import Field

from app.schemas.base import BaseJobSchema
from app.schemas.registry import register_schema

@register_schema("my_job")
class MyJobSchema(BaseJobSchema):
    job_type: Literal["my_job"] = "my_job"
    input_data: str = Field(..., description="Data to process")

    model_config = {
        "json_schema_extra": {
            "example": {"input_data": "sample data"}
        }
    }
```

### Step 2: Create Workflow

```python
# app/workflows/my_workflow.py
from app.core.context import WorkflowContext
from app.schemas.my_schema import MyJobSchema
from app.workflows.base import BaseWorkflow
from app.workflows.registry import register_workflow

@register_workflow("my_job")
class MyWorkflow(BaseWorkflow):
    job_schema = MyJobSchema

    def process(self, context: WorkflowContext) -> None:
        data = context.job_data["input_data"]
        context.log(f"Processing: {data}")

        # Your logic here
        result = data.upper()

        context.set_result({"output": result})

    def before_process(self, context: WorkflowContext) -> None:
        context.log("Starting workflow")

    def after_process(self, context: WorkflowContext) -> None:
        context.log("Workflow complete")

    def on_error(self, context: WorkflowContext, error: Exception) -> None:
        context.log(f"Error: {error}")
```

### Step 3: Register Imports

```python
# app/api/endpoint.py - add import
import app.schemas.my_schema  # noqa: F401

# app/worker/tasks.py - add import
import app.workflows.my_workflow  # noqa: F401
```

### Step 4: Test

```bash
# Restart services
scripts/stop.sh && scripts/start.sh

# Test endpoint
curl -X POST http://localhost:8000/jobs/my_job \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key-here" \
  -d '{"input_data": "test"}'
```

---

## API Reference

### Endpoints

Each registered job_type gets a dedicated endpoint:

| Method | Path | Description |
|--------|------|-------------|
| POST | `/jobs/{job_type}` | Submit a job (typed schema) |
| GET | `/jobs/{job_id}` | Get job status and result |
| GET | `/health` | Health check |

### Submit Job

```
POST /jobs/example
Content-Type: application/json
X-API-Key: your-api-key-here

{
  "message": "Hello World"
}
```

Response (202 Accepted):
```json
{
  "job_id": "uuid-here",
  "status": "pending",
  "message": "Job 'example' accepted for processing"
}
```

### Get Job Status

```
GET /jobs/{job_id}
X-API-Key: your-api-key-here
```

Response:
```json
{
  "job_id": "uuid-here",
  "job_type": "example",
  "status": "completed",
  "result": {"processed": "HELLO WORLD"},
  "error": null,
  "created_at": "2024-01-01T00:00:00",
  "started_at": "2024-01-01T00:00:01",
  "completed_at": "2024-01-01T00:00:02"
}
```

### Job Status Values

| Status | Description |
|--------|-------------|
| `pending` | Job queued, waiting for worker |
| `processing` | Worker is executing the workflow |
| `completed` | Workflow finished successfully |
| `failed` | Workflow raised an exception |

---

## Local Development

### Playground Testing

Test workflows without Docker:

```python
# playground/workflow_playground.py
import sys
sys.path.insert(0, "..")

from app.core.context import WorkflowContext
from app.workflows.my_workflow import MyWorkflow

context = WorkflowContext(
    job_id="test-123",
    job_data={"job_type": "my_job", "input_data": "test"}
)

workflow = MyWorkflow()
result = workflow.run(context)

print(f"Status: {result.status}")
print(f"Result: {result.result}")
print(f"Logs: {result.logs}")
```

### HTTP Playground

Test API with automatic polling:

```bash
cd playground
python http_playground.py
```

---

## Configuration

Environment variables in `.env`:

```bash
# Database
POSTGRES_HOST=db
POSTGRES_PORT=5432
POSTGRES_DB=launchpad
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your-password

# Redis
REDIS_HOST=redis
REDIS_PORT=6379

# API Authentication
API_KEYS=your-api-key-here
```

---

## Troubleshooting

### Container Issues

```bash
# Clean restart
scripts/stop.sh
docker volume rm launchpad_db_data launchpad_redis_data
scripts/start.sh
```

### View Logs

```bash
scripts/logs.sh
```

### Check Job in Database

```sql
SELECT id, job_type, status, error, created_at
FROM jobs
ORDER BY created_at DESC
LIMIT 10;
```
