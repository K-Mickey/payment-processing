from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from payment_processing.infrastructure.db.models import Outbox as OutboxModel
from payment_processing.infrastructure.messaging import Outbox


class OutboxRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all(self) -> list[Outbox]:
        rows = await self.session.scalars(select(OutboxModel))
        return [Outbox(**row.model_dump()) for row in rows]
