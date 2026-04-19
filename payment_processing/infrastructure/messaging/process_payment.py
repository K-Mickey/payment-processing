import logging
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from payment_processing.infrastructure.db.repositories import PaymentRepository
from payment_processing.infrastructure.payment_gateway import PaymentProcessor

logger = logging.getLogger(__name__)


async def process_payment(session: AsyncSession, payment_id: UUID):
    repository = PaymentRepository(session)
    payment = await repository.get_by_id(payment_id)

    if payment is None:
        logger.warning("Payment not found %s", payment_id)
        return None

    if not payment.is_pending():
        logger.warning("Unexpected status=%s, payment_id=%s", payment.status, payment.payment_id)
        return None

    payment_processor = PaymentProcessor()
    result_payment = await payment_processor.process_payment()
    if result_payment:
        payment.success()
    else:
        payment.fail()

    await repository.update_payment_status(payment)

    return payment

