import asyncio
import logging
from asyncio import CancelledError, sleep

from faststream.rabbit import RabbitBroker
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from payment_processing.config import settings
from payment_processing.infrastructure.broker.queues import PaymentExchange
from payment_processing.infrastructure.db import dispose_db, get_session_factory, init_db
from payment_processing.infrastructure.db.enums import AggregateType
from payment_processing.infrastructure.db.models import Outbox
from payment_processing.infrastructure.db.repositories import SQLAlchemyOutboxRepository
from payment_processing.utils import datetime_now

logger = logging.getLogger(__name__)
broker = RabbitBroker(settings.broker_url)


def main():
    logging.basicConfig(
        level=settings.log_level,
        format=settings.log_format,
    )
    asyncio.run(run())


async def run():
    await broker.start()
    init_db(settings.db)
    logger.debug("Broker started")

    try:
        session_factory = await get_session_factory()
        await run_publisher(
            session_factory=session_factory,
            batch_size=settings.outbox_batch_size,
            pool_interval=settings.outbox_pool_interval,
        )

    finally:
        await broker.stop()
        await dispose_db()
        logger.debug("Broker stopped")


async def run_publisher(
    session_factory: async_sessionmaker,
    batch_size: int,
    pool_interval: float,
) -> None:
    logger.debug("Running outbox producer")
    while True:
        await sleep(pool_interval)
        try:
            async with session_factory() as session:
                async with session.begin():
                    publish_messages = await publish_events(
                        session=session,
                        batch_size=batch_size,
                    )
                    logger.debug("Published %s messages", publish_messages)
        except KeyboardInterrupt, CancelledError:
            logger.debug("Outbox producer interrupted")
            break
        except Exception as e:
            logger.exception(e)


async def publish_events(session: AsyncSession, batch_size: int) -> int:
    repository = SQLAlchemyOutboxRepository(session)
    events = await repository.fetch_pending_events(batch_size)
    logger.debug("Found %s messages to publish", len(events))

    publish_messages = 0
    for event in events:
        try:
            await publish_event(event)
            event.published_at = datetime_now()
            event.last_error = None
            publish_messages += 1

        except Exception as e:
            logger.exception(e)
            event.last_error = str(e)

    return publish_messages


async def publish_event(event: Outbox) -> None:
    match event.aggregate_type:
        case AggregateType.PAYMENT:
            await broker.publish(
                message=dict(event.payload),
                exchange=PaymentExchange,
                routing_key=event.routing_key,
                headers=event.headers,
                message_id=str(event.id),
                persist=True,
            )
            logger.debug("Published outbox %s to queue %s", event.id, event.routing_key)
        case _:
            raise ValueError(f"Aggregate type {event.aggregate_type} not supported")


if __name__ == "__main__":
    main()
