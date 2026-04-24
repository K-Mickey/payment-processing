from typing import Self

from sqlalchemy.ext.asyncio import async_sessionmaker

from payment_processing.domain.interfaces import UnitOfWork
from payment_processing.infrastructure.db.repositories.outbox import SQLAlchemyOutboxRepository
from payment_processing.infrastructure.db.repositories.payments import SQLAlchemyPaymentRepository


class SqlAlchemyUnitOfWork(UnitOfWork):
    def __init__(self, session_factory: async_sessionmaker):
        self.session_factory = session_factory

    async def __aenter__(self) -> Self:
        self.session = self.session_factory()
        self.payments = SQLAlchemyPaymentRepository(self.session)
        self.outbox = SQLAlchemyOutboxRepository(self.session)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            await self.session.commit()
        else:
            await self.session.rollback()
        await self.session.close()

    async def commit(self):
        await self.session.commit()

    async def rollback(self):
        await self.session.rollback()
