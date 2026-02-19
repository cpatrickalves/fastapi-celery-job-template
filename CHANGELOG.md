# Changelog

All notable changes to this project will be documented in this file.

## [0.10.0] - 2026-02-19

### Added
- Endpoint to cancel running Celery jobs (`POST /jobs/{job_id}/cancel`)
- Shared Redis connection pool to prevent connection leaks
- `cancelled_at` timestamp field on Job model for cancellation tracking
- Kanchi integration for real-time Celery task monitoring with Basic Auth and credential generation script
- Dynamic Celery task registration per `job_type` with job-specific endpoint names
- Kanchi frontend configuration environment variables in `.env.example` and `docker-compose.yml`

### Fixed
- Race condition in pending→processing transition using conditional UPDATE
- Event-loop blocking and duplicate revoke in cancel endpoint
- Docstring formatting inconsistency in Job model
- Alembic fileConfig conflict with loguru when running programmatically

### Changed
- Replaced `CancellationService` class with plain functions
- Updated README.md and getting-started.md with comprehensive documentation improvements
- Cancellation tests updated to use plain functions instead of service class

## [0.9.3] - 2026-02-06

### Added
- Metadata in Celery `process_job` task with job events enabled and structured result return
- Real-time progress tracking for jobs with `progress` and `progress_message` fields
- Centralized explicit workflow registration in `app/workflows/config.py`
- Schemas reorganized into the `workflows` module
- `metadata` field in schemas for tracking, debugging, and auditing
- API Key authentication on FastAPI endpoints with tests
- Health check endpoint for PostgreSQL, Redis, and Celery
- Structured logging with Loguru
- HTTP playground with polling support for processing tests
- Makefile with common development commands (format, test, Docker)
- Database migrations with Alembic
- Middleware, logging, and FastAPI application lifecycle management
- Application settings via `pydantic-settings`
- Environment configuration template (`.env.example`)
- Comprehensive project documentation (installation, architecture, development)
- Docker support with unified Dockerfile and Docker Compose
- Dependency management with UV

### Changed
- Renamed project to 'fastapi-celery-job-template'
- Replaced decorator-based registration with centralized explicit registration
- Refactored to support async operations with SQLAlchemy
- Refactored workflows for async execution
- Refactored project structure into the `app` package
- Updated Python to version 3.12.8

### Removed
- Removed `@register_workflow` and `@register_schema` decorator system
- Removed `requirements.txt` in favor of `pyproject.toml` with UV
