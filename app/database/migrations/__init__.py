import logging
from pathlib import Path

from alembic import command
from alembic.config import Config

logger = logging.getLogger(__name__)


def run_migrations() -> None:
    """Run pending Alembic migrations on application startup."""
    try:
        alembic_ini = Path(__file__).parent.parent.parent / "alembic.ini"
        alembic_cfg = Config(str(alembic_ini))

        logger.info("[database] Checking for pending database migrations...")
        command.upgrade(alembic_cfg, "head")
        logger.info("[database] Database migrations completed successfully.")

    except Exception as e:
        logger.error(f"[database] Failed to run database migrations: {e}")
        raise
