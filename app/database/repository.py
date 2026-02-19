"""
Generic Repository Module

This module provides both synchronous and asynchronous generic repositories
for database operations. It supports basic CRUD operations and additional
methods for querying and updating data.
"""

from typing import Generic, List, Optional, Type, TypeVar

from sqlalchemy import desc, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

T = TypeVar("T")


class GenericRepository(Generic[T]):
    """Synchronous repository for Celery workers and other sync contexts."""

    def __init__(self, session: Session, model: Type[T]):
        self.session = session
        self.model = model

    def create(self, obj: T) -> T:
        self.session.add(obj)
        self.session.commit()
        return obj

    def get(self, id: str) -> Optional[T]:
        return self.session.query(self.model).filter(self.model.id == id).first()

    def get_all(self) -> List[T]:
        return self.session.query(self.model).all()

    def update(self, obj: T) -> T:
        self.session.merge(obj)
        self.session.commit()
        return obj

    def delete(self, id: str) -> None:
        obj = self.get(id)
        if obj:
            self.session.delete(obj)
            self.session.commit()

    def get_latest(self, n: int = 1) -> List[T]:
        return (
            self.session.query(self.model).order_by(desc(self.model.id)).limit(n).all()
        )

    def count(self) -> int:
        return self.session.query(self.model).count()

    def conditional_update_status(
        self, id: str, from_status: str, to_status: str, **extra_fields
    ) -> bool:
        """Atomically update status only if current status matches from_status.

        Returns True if the update succeeded (rowcount > 0).
        """
        stmt = (
            update(self.model)
            .where(self.model.id == id, self.model.status == from_status)
            .values(status=to_status, **extra_fields)
        )
        result = self.session.execute(stmt)
        self.session.commit()
        return result.rowcount > 0

    def exists(self, **kwargs) -> bool:
        return self.session.query(
            self.model.query.filter_by(**kwargs).exists()
        ).scalar()


class AsyncGenericRepository(Generic[T]):
    """Asynchronous repository for FastAPI endpoints."""

    def __init__(self, session: AsyncSession, model: Type[T]):
        self.session = session
        self.model = model

    async def create(self, obj: T) -> T:
        self.session.add(obj)
        await self.session.flush()
        await self.session.refresh(obj)
        return obj

    async def get(self, id: str) -> Optional[T]:
        result = await self.session.execute(
            select(self.model).where(self.model.id == id)
        )
        return result.scalar_one_or_none()

    async def get_all(self) -> List[T]:
        result = await self.session.execute(select(self.model))
        return list(result.scalars().all())

    async def update(self, obj: T) -> T:
        merged = await self.session.merge(obj)
        await self.session.flush()
        return merged

    async def delete(self, id: str) -> None:
        obj = await self.get(id)
        if obj:
            await self.session.delete(obj)
            await self.session.flush()

    async def get_latest(self, n: int = 1) -> List[T]:
        result = await self.session.execute(
            select(self.model).order_by(desc(self.model.id)).limit(n)
        )
        return list(result.scalars().all())

    async def count(self) -> int:
        result = await self.session.execute(
            select(func.count()).select_from(self.model)
        )
        return result.scalar_one()

    async def exists(self, **kwargs) -> bool:
        stmt = select(self.model).filter_by(**kwargs).limit(1)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None
