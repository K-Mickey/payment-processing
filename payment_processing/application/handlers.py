import logging
from uuid import UUID

from sqlalchemy.exc import IntegrityError

from payment_processing.application.commands import CreatePaymentCommand
from payment_processing.application.dto import PaymentDTO
from payment_processing.domain import Currency, Payment
from payment_processing.domain.interfaces import (
    PaymentProcessor,
    PaymentRepository,
    UnitOfWork,
)

logger = logging.getLogger(__name__)


class GetPaymentHandler:
    def __init__(self, payment_repo: PaymentRepository):
        self._payment_repo = payment_repo

    async def execute(self, payment_id: UUID) -> PaymentDTO | None:
        payment = await self._payment_repo.get_by_id(payment_id)
        if payment is None:
            return None
        return PaymentDTO.from_entity(payment)


class CreatePaymentHandler:
    def __init__(self, uow_factory: UnitOfWork):
        self._uow_factory = uow_factory

    async def execute(self, cmd: CreatePaymentCommand) -> PaymentDTO:
        async with self._uow_factory as uow:
            existing = await uow.payments.get_by_idempotency_key(cmd.idempotency_key)
            if existing:
                logger.debug(
                    f"Idempotent request for key {cmd.idempotency_key}, returning existing payment {existing.id}"
                )
                return PaymentDTO.from_entity(existing)

            payment = Payment.create(
                amount=cmd.amount,
                currency=Currency(cmd.currency),
                description=cmd.description,
                metadata=cmd.metadata,
                idempotency_key=cmd.idempotency_key,
                webhook_url=cmd.webhook_url,
            )

            await uow.payments.save(payment)
            logger.debug("Saved payment %s", payment.id)

            event = await uow.outbox.add_payment_created(payment)
            logger.debug("Saved event %s", event.id)

            try:
                await uow.commit()
            except IntegrityError:
                await uow.rollback()
                logger.warning("Payment with idempotency key %s already exists", cmd.idempotency_key)
                existing = await uow.payments.get_by_idempotency_key(cmd.idempotency_key)
                if existing:
                    return PaymentDTO.from_entity(existing)
                raise

        return PaymentDTO.from_entity(payment)


class ProcessPaymentHandler:
    def __init__(
        self,
        uow_factory: UnitOfWork,
        payment_processor: PaymentProcessor,
    ):
        self._uow_factory = uow_factory
        self._processor = payment_processor

    async def execute(self, payment_id: UUID) -> Payment | None:
        async with self._uow_factory as uow:
            payment = await uow.payments.get_by_id(payment_id)
            if payment is None:
                logger.error(f"Payment {payment_id} not found")
                return None

            if payment.is_processed:
                logger.warning(f"Payment {payment.id} already processed with status {payment.status}")
                return payment

            success = await self._processor.process(payment)
            if success:
                payment.mark_as_succeeded()
                logger.info(f"Payment {payment.id} succeeded")
            else:
                payment.mark_as_failed()
                logger.warning(f"Payment {payment.id} failed")

            await uow.payments.save(payment)

        return payment
