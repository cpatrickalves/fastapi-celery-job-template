import psycopg2
import redis

from utils.logger import logger
from settings import settings


def check_postgres_health() -> dict:
    """Check if PostgreSQL database is responding."""
    try:
        conn = psycopg2.connect(
            dbname=settings.POSTGRES_DB,
            user=settings.POSTGRES_USER,
            password=settings.POSTGRES_PASSWORD,
            host=settings.POSTGRES_HOST,
            port=settings.POSTGRES_PORT,
            connect_timeout=5,
        )
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.close()
        conn.close()
        return {
            "status": "healthy",
            "message": "Database connection successful",
        }
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "message": f"Database connection failed: {str(e)}",
        }


def check_redis_health() -> dict:
    """Check if Redis is responding."""
    try:
        r = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            socket_connect_timeout=5,
        )
        r.ping()
        return {
            "status": "healthy",
            "message": "Redis connection successful",
        }
    except Exception as e:
        logger.error(f"Redis health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "message": f"Redis connection failed: {str(e)}",
        }


def check_celery_workers() -> dict:
    """Check if Celery workers are running."""
    try:
        from worker.config import celery_app

        inspector = celery_app.control.inspect()
        stats = inspector.stats()
        if stats:
            return {
                "status": "healthy",
                "message": "Celery workers are running",
                "workers": len(stats),
            }
        else:
            logger.warning("No Celery workers are running.")
            return {
                "status": "unhealthy",
                "message": "No Celery workers are running",
            }
    except Exception as e:
        logger.error(f"Celery health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "message": f"Celery check failed: {str(e)}",
        }
