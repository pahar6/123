from typing import Sequence, TypeVar

from sqlalchemy import select, ChunkedIteratorResult, delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from loguru import logger

T = TypeVar("T", bound='Base')


class BaseQuery:

    @classmethod
    async def get_or_create(cls: type[T], session: AsyncSession, defaults=None, **kwargs) -> tuple[T, bool]:
        instance = await cls.get_or_none(session, **kwargs)
        if instance is not None:
            return instance, False
        instance = await cls.create(session, **kwargs, **(defaults or {}))
        return instance, True

    @classmethod
    async def get(cls: type[T], session: AsyncSession, **kwargs) -> T:
        result = await session.execute(select(cls).filter_by(**kwargs))
        return result.unique().scalar_one()

    @classmethod
    async def get_loaded(cls: type[T], session: AsyncSession, load: str, **kwargs) -> T:
        result = await session.execute(select(cls).filter_by(**kwargs).options(selectinload(load)))
        return result.unique().scalar_one()

    @classmethod
    async def get_or_none(cls: type[T], session: AsyncSession, **kwargs) -> T | None:
        result = await session.execute(select(cls).filter_by(**kwargs))
        return result.unique().scalar_one_or_none()

    @classmethod
    async def create(cls: type[T], session: AsyncSession, **kwargs) -> T:
        # ignore extra kwargs
        valid_columns = {c.name for c in cls.__table__.columns}
        kwargs = {k: v for k, v in kwargs.items() if k in valid_columns}
        language_code = kwargs.get('language_code')
        if language_code:
            if language_code != 'ru':
                kwargs['language_code'] = 'en'
        instance = cls(**kwargs)
        session.add(instance)
        return instance

    # two method to delete instance. One is classmethod, another is instance method

    # удаление по условиям
    @classmethod
    async def delete(cls: type[T], session: AsyncSession, *expr) -> Sequence[int]:
        res: ChunkedIteratorResult = await session.execute(delete(cls).where(*expr).returning(cls.id))
        return res.scalars().fetchall()

    async def delete_instance(self, session: AsyncSession) -> None:
        await session.delete(self)

    @classmethod
    async def all(cls: type[T], session: AsyncSession) -> list[T]:
        result = await session.execute(select(cls))
        return result.scalars().unique().all()

    def update(self: T, **kwargs) -> None:
        for attr, value in kwargs.items():
            if hasattr(self, attr):
                setattr(self, attr, value)

    @classmethod
    async def filter(
            cls: type[T],
            session: AsyncSession,
            *expr,
            limit: int | None = None,
            offset: int | None = None,
    ) -> list[T]:
        query = select(cls).where(*expr).limit(limit).offset(offset)
        result = await session.execute(query)
        return result.unique().scalars().all()


    @classmethod
    async def count(cls: type[T], session: AsyncSession, *expr) -> int:
        query = select(func.count(cls.id)).where(*expr)
        result = await session.execute(query)
        return result.scalar_one()
