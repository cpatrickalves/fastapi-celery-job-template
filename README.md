# GenAI Launchpad

## Overview

**Launchpad** is a template for job-driven asynchronous processing, designed for production applications that require scalable and reliable background processing.

The template offers a modular architecture that integrates the best tools and design patterns to enable agile development without compromising flexibility. Through a distributed queue system and asynchronous workers, Launchpad processes jobs efficiently while maintaining complete traceability of each task's lifecycle.

Ideal for applications that need to process long-running tasks, complex workflows, or operations that cannot block HTTP requests, the template provides a solid foundation for building robust and scalable systems.

## Features

* **REST API with FastAPI**: Endpoints for job submission and querying
* **Asynchronous Processing**: Celery workers for background task execution
* **Queue System**: Redis for efficient task queue management
* **Status Tracking**: Complete lifecycle tracking of jobs (pending, processing, completed, failed)
* **Data Persistence**: PostgreSQL for storing jobs, results, and execution context
* **Automatic Migrations**: Alembic for database schema versioning and migration
* **Health Checks**: Monitoring endpoints for service health verification
* **Containerization**: Docker Compose for orchestrating all services
* **Hot Reload**: Development with auto-reload for both API and workers

## Project Structure

```bash
.
├── CLAUDE.md                # Documentation for AI assistant
├── Dockerfile               # Docker configuration for API and workers
├── README.md                # This file
├── app/                     # Application source code
│   ├── alembic.ini          # Alembic configuration for migrations
│   ├── api/                 # REST API endpoints
│   ├── core/                # Core components (context, commands)
│   ├── database/            # Models, sessions, and migrations
│   ├── main.py              # FastAPI application entry point
│   ├── schemas/             # Pydantic schemas for validation
│   ├── settings.py          # Application settings
│   ├── start.sh             # Container initialization script
│   ├── utils/               # Utilities (logger, health checks)
│   ├── worker/              # Celery configuration and tasks
│   └── workflows/           # Job processing workflows
├── docker-compose.yml       # Service orchestration (API, workers, DB, Redis)
├── docs/                    # Detailed documentation
│   ├── 01-getting-started.md
│   ├── 02-architecture.md
│   └── 03-development.md
├── playground/              # Scripts for testing and experimentation
│   ├── http_playground.py
│   ├── utils/
│   └── workflow_playground.py
├── pyproject.toml           # Project configuration and dependencies (uv)
└── scripts/                 # Helper scripts
    ├── logs.sh              # Log viewing
    ├── start.sh             # Service initialization
    └── stop.sh              # Service shutdown
```

## Prerequisites

* **Python 3.12+**: Programming language
* **Docker**: For service containerization
* **Docker Compose**: For container orchestration
* **uv**: Python package manager (optional, for local development)

## Technologies Used

* **FastAPI**: Modern, high-performance web framework
* **Celery**: Distributed queue system for asynchronous processing
* **PostgreSQL**: Relational database
* **Redis**: Message broker and cache
* **Alembic**: Database migration management
* **Pydantic**: Data validation and settings
* **Uvicorn**: High-performance ASGI server
* **Loguru**: Advanced logging system

## Installation

### 1. Clone the repository

```bash
git clone <repository-url>
cd genai-launchpad
```

### 2. Configure environment variables

Copy the `.env.example` file to `.env` and configure the required variables:

```bash
cp .env.example .env
```

### 3. Start the services

```bash
./scripts/start.sh
```

This command will:
- Build Docker images
- Start PostgreSQL, Redis, API, and Celery Workers
- Run database migrations automatically

## Running the Project

### Check service status

```bash
docker compose -p launchpad ps
```

### Access API documentation

After starting the services, access:

* **Swagger UI**: http://localhost:8080/docs
* **ReDoc**: http://localhost:8080/redoc

### Submit a job

```bash
curl -X POST http://localhost:8080/jobs/example \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello World"}'
```

Expected response:
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "created_at": "2024-01-23T15:30:00"
}
```

### Query job status

```bash
curl http://localhost:8080/jobs/{job_id}
```

### View logs

```bash
# Logs from all services
./scripts/logs.sh

# Logs from a specific service
docker compose -p launchpad logs -f api
docker compose -p launchpad logs -f celery_worker
```

### Stop the services

```bash
./scripts/stop.sh
```

## Additional Documentation

For detailed information about architecture, development, and troubleshooting, see:

1. **[Getting Started](docs/01-getting-started.md)** - Quick start guide and project structure
2. **[Architecture](docs/02-architecture.md)** - System design, components, and data flow
3. **[Development](docs/03-development.md)** - How to add new job types and API reference

