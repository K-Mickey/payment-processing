from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from payment_processing.domain import Payment
from payment_processing.domain.interfaces import OutboxRepository
from payment_processing.infrastructure.db.enums import AggregateType, RoutingKey
from payment_processing.infrastructure.db.models import Outbox
from payment_processing.utils import datetime_now, uuid


class SQLAlchemyOutboxRepository(OutboxRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add_payment_created(self, payment: Payment) -> Outbox:
        model = Outbox(
            id=uuid(),
            aggregate_type=AggregateType.PAYMENT,
            aggregate_id=payment.id,
            routing_key=RoutingKey.PAYMENT_NEW,
            payload={"payment_id": str(payment.id)},
            headers={},
            created_at=datetime_now(),
            published_at=None,
            last_error=None,
        )
        self.session.add(model)
        await self.session.flush()
        return model

    async def fetch_pending_events(self, limit: int = 10) -> Sequence[Outbox]:
        stmt = (
            select(Outbox)
            .where(Outbox.published_at.is_(None))
            .order_by(Outbox.created_at)
            .limit(limit)
            .with_for_update(skip_locked=True)
        )
        rows = await self.session.scalars(stmt)
        return rows.all()
