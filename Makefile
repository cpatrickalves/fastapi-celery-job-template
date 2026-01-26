.PHONY: help format test run build up down logs dtest

.DEFAULT_GOAL := help

help:
	@echo "Available commands:"
	@echo "  help   - Show this help message"
	@echo "  format - Format code using ruff formatter"
	@echo "  test   - Run all tests with coverage report"
	@echo "  run    - Start API development server with hot reload on port 8000"
	@echo "  build  - Build Docker images for the application"
	@echo "  up     - Start Docker containers in detached mode"
	@echo "  down   - Stop and remove Docker containers"
	@echo "  logs   - Show Docker container logs"
	@echo "  dtest  - Run tests inside Docker container"

format:
	@echo "Formatting code using ruff..."
	uv run ruff format .

test:
	@echo "Running tests with coverage..."
	ENVIRONMENT=testing uv run pytest --cov

run:
	@echo "Starting API development server on port 8000..."
	uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

build:
	@echo "Building Docker images..."
	docker compose build

up:
	@echo "Starting Docker containers..."
	docker compose up -d

down:
	@echo "Stopping Docker containers..."
	docker compose down

logs:
	@echo "Showing Docker logs..."
	docker compose logs -f

dtest:
	@echo "Running tests inside Docker container..."
	docker compose run --rm -e ENVIRONMENT=testing api uv run pytest -v tests/
