# Getting Started

## Introduction

FastAPI Celery Job Template is a production-ready template for building job-driven async processing applications. It provides a robust architecture combining FastAPI, PostgreSQL, Redis, and Celery for reliable background task processing.

### Key Features

- **Job-Driven Architecture**: Typed endpoints per job type with full OpenAPI documentation
- **Async Processing**: Celery workers for reliable background job execution
- **Production Infrastructure**: PostgreSQL, Redis, Docker, Alembic migrations
- **Extensible Workflows**: Simple base class with lifecycle hooks

### How It Works

```
POST /jobs/{job_type} → Validate Schema → Store in DB → Queue Task → 202 Accepted
                                                              ↓
                              Worker polls → Execute Workflow → Store Result
```

---

## Installation

### Prerequisites

- Python 3.12+
- Docker and Docker Compose
- Git

### Setup

```bash
# Clone repository
git clone https://github.com/cpatrickalves/fastapi-celery-job-template.git
cd fastapi-celery-job-template

# Setup environment
cp app/.env.example app/.env

# Start services
scripts/start.sh

# Apply migrations
cd app && ./migrate.sh
```

---

## Quick Start

### 1. Start Services

```bash
scripts/start.sh
```

### 2. Submit a Job

```bash
curl -X POST http://localhost:8080/jobs/example \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello World",
    "metadata": {
      "user_id": "user_123",
      "source_system": "web_app"
    }
  }'
```

> **Note**: The `metadata` field is optional and can include tracking information like `user_id`, `source_system`, `request_id`, `correlation_id`, or any contextual data useful for monitoring, debugging, and auditing.

Response:
```json
{"job_id": "abc-123", "status": "pending", "message": "Job 'example' accepted"}
```

### 3. Check Job Status

```bash
curl http://localhost:8080/jobs/{job_id}
```

Response (after processing):
```json
{
  "job_id": "abc-123",
  "job_type": "example",
  "status": "completed",
  "result": {"processed": "HELLO WORLD", "word_count": 2}
}
```

### 4. Explore the API

Open http://localhost:8080/docs for interactive Swagger documentation.

### 5. Stop Services

```bash
scripts/stop.sh
```

---

## Project Structure

```
app/
├── api/
│   ├── endpoint.py      # Job endpoints (dynamic per job_type)
│   └── router.py        # Router configuration
├── core/
│   └── context.py       # WorkflowContext
├── database/
│   ├── job.py           # Job model
│   ├── repository.py    # Generic repository
│   └── session.py       # DB session management
├── schemas/
│   ├── base.py          # BaseJobSchema
│   ├── registry.py      # Schema registry
│   └── example_schema.py
├── workflows/
│   ├── base.py          # BaseWorkflow
│   ├── registry.py      # Workflow registry
│   └── example_workflow.py
├── worker/
│   ├── config.py        # Celery configuration
│   └── tasks.py         # process_job task
└── main.py              # FastAPI application

scripts/
├── start.sh             # Start Docker services
├── stop.sh              # Stop services
└── logs.sh              # View logs

playground/
├── workflow_playground.py   # Test workflows locally
└── http_playground.py       # Test API with polling
```
