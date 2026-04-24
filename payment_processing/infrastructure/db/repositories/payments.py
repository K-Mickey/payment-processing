from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from payment_processing.domain import IdempotencyKey, Metadata, Money, Payment, PaymentStatus, WebhookUrl
from payment_processing.domain.interfaces import PaymentRepository
from payment_processing.infrastructure.db.models import Payment as PaymentModel


class SQLAlchemyPaymentRepository(PaymentRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, payment_id: UUID) -> Payment | None:
        payment = await self.session.get(PaymentModel, payment_id)
        if not payment:
            return None
        return self._to_domain(payment)

    async def get_by_idempotency_key(self, key: str) -> Payment | None:
        stmt = select(PaymentModel).where(PaymentModel.idempotency_key == key)
        model = await self.session.scalar(stmt)
        if not model:
            return None
        return self._to_domain(model)

    async def save(self, payment: Payment) -> Payment:
        model = self._to_model(payment)
        await self.session.merge(model)
        await self.session.flush()
        return self._to_domain(model)

    @staticmethod
    def _to_domain(payment_model: PaymentModel) -> Payment:
        return Payment(
            id=payment_model.id,
            amount=Money(payment_model.amount, payment_model.currency),
            description=payment_model.description,
            metadata=Metadata(payment_model.payment_metadata),
            idempotency_key=IdempotencyKey(payment_model.idempotency_key),
            webhook_url=WebhookUrl(payment_model.webhook_url),
            status=PaymentStatus(payment_model.status),
            created_at=payment_model.created_at,
            processed_at=payment_model.processed_at,
        )

    @staticmethod
    def _to_model(payment: Payment) -> PaymentModel:
        return PaymentModel(
            id=payment.id,
            amount=payment.amount.amount,
            currency=payment.amount.currency,
            description=payment.description,
            payment_metadata=payment.metadata.data,
            idempotency_key=payment.idempotency_key.value,
            webhook_url=payment.webhook_url.url,
            status=payment.status,
            created_at=payment.created_at,
            processed_at=payment.processed_at,
        )
