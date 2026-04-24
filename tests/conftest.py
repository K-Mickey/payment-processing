from typing import AsyncGenerator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from payment_processing.api.main import create_app
from payment_processing.config import settings
from payment_processing.infrastructure.db import dispose_db, init_db
from payment_processing.infrastructure.db.models import Base


@pytest_asyncio.fixture(scope="session")
async def db_engine() -> AsyncGenerator[AsyncEngine, None]:
    init_db(settings.db)
    from payment_processing.infrastructure.db.factory import engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await dispose_db()


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
    payment_app = create_app()
    return AsyncClient(transport=ASGITransport(payment_app), base_url="http://test")
