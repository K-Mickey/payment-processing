from uuid import UUID

from sqlalchemy import exists, select
from sqlalchemy.ext.asyncio import AsyncSession

from payment_processing.domain import Payment
from payment_processing.domain.errors import PaymentNotFoundError
from payment_processing.infrastructure.db.models import Outbox as OutboxModel
from payment_processing.infrastructure.db.models import Payment as PaymentModel
from payment_processing.infrastructure.messaging import Outbox


class PaymentRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_with_outbox(self, payment: Payment, outbox: Outbox) -> Payment:
        payment_model = PaymentModel.create(**payment.model_dump())
        self.session.add(payment_model)

        outbox_model = OutboxModel(**outbox.model_dump())
        self.session.add(outbox_model)

        await self.session.flush()
        await self.session.commit()

        return Payment(**payment_model.model_dump())

    async def get_by_id(self, payment_id: UUID) -> Payment:
        payment = await self.session.get(PaymentModel, payment_id)
        if not payment:
            raise PaymentNotFoundError(payment_id)
        return Payment(**payment.model_dump())

    async def exists_by_idempotency_key(self, idempotency_key: str) -> bool:
        stmt = exists(PaymentModel).where(PaymentModel.idempotency_key == idempotency_key)
        return await self.session.scalar(stmt.select())

    async def get_all(self) -> list[Payment]:
        payments = await self.session.scalars(select(PaymentModel))
        return [Payment(**payment.model_dump()) for payment in payments]
