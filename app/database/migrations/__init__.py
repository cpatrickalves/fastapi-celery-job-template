from pathlib import Path

from alembic import command
from alembic.config import Config
from utils.logger import logger


def run_migrations() -> None:
    """Run pending Alembic migrations on application startup."""
    try:
        alembic_ini = Path(__file__).parent.parent.parent / "alembic.ini"
        alembic_cfg = Config(str(alembic_ini))

        logger.info("Checking for pending database migrations...")
        command.upgrade(alembic_cfg, "head")
        logger.info("Database migrations completed successfully.")

    except Exception as e:
        logger.error(f"Failed to run database migrations: {e}")
        raise
