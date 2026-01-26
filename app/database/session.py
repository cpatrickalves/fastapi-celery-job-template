"""
Async Database Session Module

This module provides async database engine, session factory, and dependency
injection for FastAPI routes using SQLAlchemy 2.0 async patterns.
"""

from collections.abc import AsyncGenerator
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.settings import settings
from app.utils.logger import logger


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""

    pass


# Async engine and session factory for FastAPI endpoints
async_engine = create_async_engine(
    settings.async_database_url,
    echo=settings.ENVIRONMENT == "development",
    future=True,
)

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    expire_on_commit=False,
)


# Sync engine and session factory for Celery workers and migrations
sync_engine = create_engine(
    settings.database_url,
    echo=settings.ENVIRONMENT == "development",
)

SyncSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=sync_engine,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Async database session dependency for FastAPI endpoints.

    Yields a database session that is automatically closed
    after the request completes.

    Usage in routes:
        @app.get("/items")
        async def get_items(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception as ex:
            await session.rollback()
            logger.error(ex)
            raise ex


def db_session() -> Generator[Session, None, None]:
    """Sync database session for Celery workers.

    This function provides a synchronous database session for
    background task processing where async is not supported.
    """
    session: Session = SyncSessionLocal()
    try:
        yield session
        session.commit()
    except Exception as ex:
        session.rollback()
        logger.error(ex)
        raise ex
    finally:
        session.close()


async def init_db() -> None:
    """Initialize the database by creating all tables.

    Call this during application startup.
    """
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """Dispose of the async database engine.

    Call this during application shutdown.
    """
    await async_engine.dispose()
