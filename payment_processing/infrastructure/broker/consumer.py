import asyncio
import logging
from uuid import UUID

from faststream import AckPolicy, Depends, FastStream, Logger
from faststream.rabbit import RabbitBroker, RabbitMessage
from sqlalchemy.ext.asyncio import async_sessionmaker

from payment_processing.application.handlers import ProcessPaymentHandler
from payment_processing.config import settings
from payment_processing.domain import Payment
from payment_processing.infrastructure.broker.queues import (
    DeadLetterExchange,
    DeadLetterQueue,
    NewPaymentQueue,
    PaymentExchange,
)
from payment_processing.infrastructure.db import dispose_db, get_session_factory, init_db
from payment_processing.infrastructure.db.repositories import SqlAlchemyUnitOfWork
from payment_processing.infrastructure.payment_gateway import FakePaymentProcessor
from payment_processing.infrastructure.webhook import AiohttpWebhookNotifier

broker = RabbitBroker(settings.broker_url)
app = FastStream(broker)


@app.on_startup
async def setup():
    init_db(settings.db)


@app.after_startup
async def bind_dlq():
    exchange = await broker.declare_exchange(DeadLetterExchange)
    queue = await broker.declare_queue(DeadLetterQueue)
    await queue.bind(exchange=exchange, routing_key=DeadLetterQueue.name)


@app.on_shutdown
async def shutdown():
    await broker.stop()
    await dispose_db()


def get_payment_handler(session_factory: async_sessionmaker = Depends(get_session_factory)):
    return ProcessPaymentHandler(
        uow_factory=SqlAlchemyUnitOfWork(session_factory),
        payment_processor=FakePaymentProcessor(),
    )


def get_notifier():
    return AiohttpWebhookNotifier(timeout=settings.webhook_timeout)


@broker.subscriber(
    queue=NewPaymentQueue,
    exchange=PaymentExchange,
    ack_policy=AckPolicy.MANUAL,
)
async def process_payment(
    msg,
    message: RabbitMessage,
    logger: Logger,
    handler: ProcessPaymentHandler = Depends(get_payment_handler),
    notifier: AiohttpWebhookNotifier = Depends(get_notifier),
):

    payment_id = UUID(msg["payment_id"])
    max_attempts = settings.payment_processing_max_retries
    base_delay = settings.payment_processing_base_delay

    payment: Payment | None = None
    for attempt in range(max_attempts):
        try:
            payment = await handler.execute(payment_id)
            logger.info(f"Processed payment {payment_id}")
            await message.ack()
            break

        except Exception as e:
            logger.exception(f"Attempt {attempt + 1} failed to process payment {payment_id}: {e}")

        if attempt == max_attempts - 1:
            await message.nack(requeue=False)
            logger.error(f"Payment {payment_id} moved to DLQ")
            break

        delay = base_delay * 2**attempt
        await asyncio.sleep(delay)

    if payment:
        await notify_with_retry(notifier, payment, logger)


async def notify_with_retry(notifier: AiohttpWebhookNotifier, payment: Payment, logger) -> None:
    max_attempts = settings.webhook_max_retries
    base_delay = settings.webhook_base_delay
    for attempt in range(max_attempts):
        logger.debug("Sending webhook for payment %s, attempt %s", payment.id, attempt + 1)
        notify = await notifier.notify(
            payment_id=payment.id,
            status=payment.status,
            webhook_url=payment.webhook_url.url,
        )

        if notify or attempt == max_attempts - 1:
            break

        delay = base_delay * 2**attempt
        await asyncio.sleep(delay)


def main():
    logging.basicConfig(
        level=settings.log_level,
        format=settings.log_format,
    )
    asyncio.run(app.run())


if __name__ == "__main__":
    main()
