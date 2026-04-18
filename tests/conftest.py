from typing import AsyncGenerator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from payment_processing.api import app as payment_app
from payment_processing.config import settings
from payment_processing.infrastructure.db import get_session
from payment_processing.infrastructure.db.models import Base


@pytest_asyncio.fixture(scope="session")
async def db_engine() -> AsyncGenerator[AsyncEngine, None]:
    engine = create_async_engine(url=settings.db.dsn)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function", loop_scope="session")
async def async_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    async_session = async_sessionmaker(
        bind=db_engine,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )

    async with async_session() as session:
        yield session

        await session.rollback()

        for table in reversed(Base.metadata.sorted_tables):
            await session.execute(text(f"TRUNCATE {table.name} CASCADE;"))
            await session.commit()


@pytest_asyncio.fixture(scope="session")
async def async_client(db_engine) -> AsyncClient:
    async def get_test_session() -> AsyncGenerator[AsyncSession, None]:
        session_factory = async_sessionmaker(
            bind=db_engine,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )
        async with session_factory() as session:
            yield session

    payment_app.dependency_overrides[get_session] = get_test_session
    return AsyncClient(transport=ASGITransport(payment_app), base_url="http://test")
