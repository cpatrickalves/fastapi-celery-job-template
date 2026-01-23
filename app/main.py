"""GenAI Launchpad API - Event-driven workflow processing.

This is the main entry point for the FastAPI application that provides
REST API endpoints for event-driven workflow processing.
"""

import os

from dotenv import load_dotenv
from utils.logger import logger
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from database.migrations import run_migrations
from api.router import router as api_router
from api.health_router import router as health_router
from settings import settings

load_dotenv()

# Application settings
VERSION = os.getenv("VERSION", "1.0.0")
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
PROJECT_NAME = os.getenv("PROJECT_NAME", "genai-launchpad")

api_description = """
Event-driven workflow processing API.

## Features

- **Event Submission**: Submit events for asynchronous processing
- **Status Tracking**: Check the status and results of submitted events
- **Workflow Routing**: Events are automatically routed to registered workflows based on `event_type`

## Authentication

Configure authentication middleware as needed for your deployment.
"""

# Initialize FastAPI application
app = FastAPI(
    title=f"{PROJECT_NAME} API",
    description=api_description,
    version=VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Configure CORS middleware
origins = [
    "http://localhost:3000",
    "http://localhost:8000",
    "http://localhost:8080",
]

if ENVIRONMENT == "production":
    # In production, configure specific allowed origins
    allowed_origins = os.getenv("ALLOWED_ORIGINS", "")
    if allowed_origins:
        origins = [origin.strip() for origin in allowed_origins.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(api_router)
app.include_router(health_router)


@app.on_event("startup")
async def startup_event():
    """Log application startup information."""
    logger.info("=" * 50)
    logger.info(f"{PROJECT_NAME} API v{settings.VERSION} starting up")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info("Documentation available at: /docs")
    logger.info("=" * 50)

    if settings.ENVIRONMENT != "testing":
        run_migrations()


@app.on_event("shutdown")
async def shutdown_event():
    """Log application shutdown information."""
    logger.info(f"{PROJECT_NAME} API shutting down")


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled exceptions.

    Args:
        request: The FastAPI request object
        exc: The exception that was raised

    Returns:
        JSONResponse with error details
    """
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error occurred"},
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=ENVIRONMENT == "development",
        log_level="info",
    )
