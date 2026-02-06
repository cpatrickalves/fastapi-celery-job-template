# FastAPI Celery Job Template

## Overview

FastAPI Celery Job Template is a production-ready, Docker-based framework for building job-driven asynchronous processing applications. It combines FastAPI, Celery, PostgreSQL, and Redis in a modular architecture that enables agile development without compromising flexibility.

The template is ideal for applications that need to process long-running tasks, complex workflows, or operations that cannot block HTTP requests. Through a distributed queue system and asynchronous workers, the application processes jobs efficiently while maintaining complete traceability of each task's lifecycle.

## Features

* **REST API with FastAPI**: Typed endpoints per job_type with automatic OpenAPI/Swagger documentation
* **Async Processing**: Celery workers for background task execution
* **Queue System**: Redis as message broker for efficient task management
* **Status Tracking**: Complete job lifecycle tracking (pending, processing, completed, failed)
* **Data Persistence**: PostgreSQL for storing jobs, results, and execution context
* **Automatic Migrations**: Alembic for database schema versioning and migration
* **API Key Authentication**: Endpoint protection via `X-API-Key` header
* **Real-Time Monitoring**: Kanchi dashboard for Celery task tracking
* **Health Checks**: Monitoring endpoints for service health verification
* **Containerization**: Docker Compose for orchestrating all services
* **Hot Reload**: Development with auto-reload for both API and workers

## Project Structure

```bash
.
├── app/                     # Application source code
│   ├── alembic.ini          # Alembic configuration for migrations
│   ├── api/                 # REST API endpoints
│   ├── core/                # Core components (WorkflowContext)
│   ├── database/            # Models, sessions, and migrations
│   ├── main.py              # FastAPI application entry point
│   ├── settings.py          # Application settings (pydantic-settings)
│   ├── utils/               # Utilities (logger, health checks)
│   ├── worker/              # Celery configuration and tasks
│   └── workflows/           # Job processing workflows
├── docker-compose.yml       # Service orchestration (API, Workers, DB, Redis, Kanchi)
├── docs/                    # Detailed documentation
│   ├── 01-getting-started.md
│   ├── 02-architecture.md
│   ├── 03-development.md
│   └── 04-monitoring.md
├── Makefile                 # Development commands (format, test, Docker)
├── playground/              # Scripts for testing and experimentation
│   ├── http_playground.py   # HTTP tests with polling
│   └── workflow_playground.py  # Local workflow tests
├── pyproject.toml           # Project configuration and dependencies (uv)
├── scripts/                 # Helper scripts
│   ├── logs.sh              # Log viewing
│   ├── start.sh             # Service initialization
│   └── stop.sh              # Service shutdown
└── tests/                   # Automated tests
    ├── conftest.py
    ├── test_auth.py
    ├── test_base_workflow.py
    ├── test_context.py
    ├── test_schema_registry.py
    └── test_workflow_registry.py
```

## Prerequisites

- `Python 3.12+`
- `Docker` and `Docker Compose`
- `uv`: Python package manager (for local development)
- `Git`

## Technologies Used

* **FastAPI** - Modern, high-performance web framework
* **Celery** - Distributed queue system for async processing
* **PostgreSQL** - Relational database
* **Redis** - Message broker and cache
* **Alembic** - Database migration management
* **Pydantic** - Data validation and settings
* **Kanchi** - Real-time Celery task monitoring
* **Docker** - Containerization and service orchestration
* **Loguru** - Structured logging system

## Installation

### 1. Clone the repository

```bash
git clone <repository-url>
cd fastapi-celery-job-template
```

### 2. Configure environment variables

Copy `.env.example` to `.env` and fill in the required variables:

```bash
cp .env.example .env
```

Key variables:
- `POSTGRES_PASSWORD` - Database password
- `API_KEYS` - API keys for authentication (comma-separated)
- `KANCHI_AUTH_PASSWORD_HASH` - Kanchi password hash (generate with `python docs/generate_kanchi_password.py`)

### 3. Start the services

```bash
make up
```

This will start: PostgreSQL, Redis, FastAPI API, Celery Worker, and Kanchi (monitoring).

Database migrations run automatically on API startup.

## Running the Project

### Access the API documentation

After starting the services, visit:

* **Swagger UI**: http://localhost:8080/docs
* **ReDoc**: http://localhost:8080/redoc

### Submit a job

```bash
curl -X POST http://localhost:8080/jobs/example \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key-1" \
  -d '{"message": "Hello World"}'
```

Expected response:
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "message": "Job 'example' accepted"
}
```

### Check job status

```bash
curl http://localhost:8080/jobs/{job_id} \
  -H "X-API-Key: your-api-key-1"
```

### Monitor tasks

Access the Kanchi dashboard at http://localhost:3000 to track tasks in real time.

### Useful commands (Makefile)

```bash
make help      # Show all available commands
make format    # Format code using ruff
make test      # Run tests with coverage
make run       # Start dev server (port 8000, hot reload)
make build     # Build Docker images
make up        # Start Docker containers
make down      # Stop Docker containers
make logs      # Show Docker logs
make dtest     # Run tests inside Docker
```

### Stop the services

```bash
make down
```

## Notes and Restrictions

* All `/jobs` endpoints require authentication via `X-API-Key` header
* Jobs are processed asynchronously - the API returns `202 Accepted` immediately
* The Celery worker is configured with `concurrency=1` by default; adjust as needed for production
* Database migrations run automatically on API startup (except in the testing environment)
* Redis is used both as Celery's message broker and for caching
* In production, set the `ALLOWED_ORIGINS` variable to restrict CORS

## Common Issues

| Problem | Solution |
|---------|----------|
| Containers won't start | Check that ports 5432, 6379, 8080, and 3000 are available |
| Database connection error | Verify that `POSTGRES_*` variables are correct in `.env` |
| Jobs stuck in "pending" | Check if the Celery worker is running: `docker compose logs celery_worker` |
| 403 error on endpoints | Confirm the `X-API-Key` header is present and matches a value in `API_KEYS` in `.env` |
| Kanchi not showing tasks | Verify that `celery -E` (events) is enabled on the worker |

## Additional Documentation

For detailed information on architecture, development, and monitoring:

1. **[Getting Started](docs/01-getting-started.md)** - Quick start guide
2. **[Architecture](docs/02-architecture.md)** - System design, components, and data flow
3. **[Development](docs/03-development.md)** - How to add new job types and API reference
4. **[Monitoring](docs/04-monitoring.md)** - Kanchi setup and usage for monitoring

## Maintainers

- **Patrick Alves** (cpatrickalves@gmail.com)
