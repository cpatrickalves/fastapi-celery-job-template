from fastapi import APIRouter

from app.utils.health_checks import (
    check_postgres_health,
    check_celery_workers,
    check_redis_health,
)
from app.settings import settings

router = APIRouter(
    prefix="",
    responses={404: {"description": "Not found"}},
    tags=["Health"],
)


@router.get("/health", include_in_schema=True)
async def health_check():
    """Health check endpoint to verify application and dependencies status.

    Returns:
        dict: Overall status and individual component health checks
    """
    postgres_status = check_postgres_health()
    redis_status = check_redis_health()
    celery_status = check_celery_workers()

    checks = {
        "postgres": postgres_status,
        "redis": redis_status,
        "celery": celery_status,
    }

    overall_status = (
        "healthy"
        if all(check["status"] == "healthy" for check in checks.values())
        else "unhealthy"
    )

    return {
        "status": overall_status,
        "version": settings.VERSION,
        "checks": checks,
    }
