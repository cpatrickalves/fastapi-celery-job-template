import os

import redis
from celery import Celery
from dotenv import load_dotenv

load_dotenv()


def get_redis_url():
    """
    Get the Redis URL for Celery configuration.

    Returns:
        str: The Redis URL.
    """
    redis_host = f"{os.getenv('PROJECT_NAME')}_redis"
    return f"redis://{redis_host}:6379/0"


def get_celery_config():
    """
    Get the Celery configuration.

    Returns:
        dict: The Celery configuration.
    """
    redis_url = get_redis_url()
    return {
        "broker_url": redis_url,
        "result_backend": redis_url,
        "task_serializer": "json",
        "accept_content": ["json"],
        "result_serializer": "json",
        "enable_utc": True,
        "broker_connection_retry_on_startup": True,
        "worker_send_task_events": True,
        "task_send_sent_event": True,
        "worker_heartbeat_interval": 2,
    }


_redis_pool = None


def get_redis_client():
    global _redis_pool
    if _redis_pool is None:
        _redis_pool = redis.ConnectionPool.from_url(
            get_redis_url(),
            max_connections=int(os.environ.get("REDIS_MAX_CONNECTIONS", "20")),
            socket_timeout=5,
            socket_connect_timeout=5,
        )
    return redis.Redis(connection_pool=_redis_pool)


celery_app = Celery("tasks")
celery_app.config_from_object(get_celery_config())

# Automatically discover and register tasks
celery_app.autodiscover_tasks(["app.worker"], force=True)
