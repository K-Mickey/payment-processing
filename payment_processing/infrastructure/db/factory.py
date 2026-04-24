from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from payment_processing.config import DBSettings

engine: AsyncEngine | None = None
session_factory: async_sessionmaker[AsyncSession] | None = None


def init_db(config: DBSettings) -> None:
    global engine
    global session_factory
    engine = create_async_engine(
        url=config.dsn,
        echo=config.echo,
        pool_size=config.pool_size,
        max_overflow=config.max_overflow,
        pool_timeout=config.pool_timeout,
        pool_recycle=config.pool_recycle,
        pool_pre_ping=config.pool_pre_ping,
        future=True,
    )
    session_factory = async_sessionmaker(
        bind=engine,
        expire_on_commit=False,
        autoflush=False,
    )


async def dispose_db() -> None:
    global engine
    if engine is not None:
        await engine.dispose()
        engine = None


async def get_session_factory() -> async_sessionmaker[AsyncSession]:
    global session_factory
    if session_factory is None:
        raise RuntimeError("Database not initialized")
    return session_factory


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    session_factory = await get_session_factory()
    async with session_factory() as session:
        yield session
