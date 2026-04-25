from asyncio import CancelledError, create_task, sleep
from decimal import Decimal
from unittest.mock import patch

import pytest
from faststream.rabbit import TestRabbitBroker
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from payment_processing.domain import Currency, Payment
from payment_processing.infrastructure.broker.producer import broker, publish_event, publish_events, run_publisher
from payment_processing.infrastructure.broker.queues import NewPaymentQueue, PaymentExchange
from payment_processing.infrastructure.db.models import Outbox
from payment_processing.infrastructure.db.repositories import SQLAlchemyOutboxRepository
from payment_processing.utils import uuid


async def add_outboxes_to_db(async_session: AsyncSession, count: int = 1):
    repository = SQLAlchemyOutboxRepository(async_session)
    for _ in range(count):
        await repository.add_payment_created(
            Payment.create(
                amount=Decimal("10.00"),
                currency=Currency.USD,
                description="Payment for order #123",
                metadata={"order_id": 123},
                idempotency_key=str(uuid()),
                webhook_url="https://example.com/webhook",
            )
        )

    await async_session.commit()


@pytest.mark.asyncio(loop_scope="session")
async def test_publish_events_success(async_session: AsyncSession):
    await add_outboxes_to_db(async_session, count=10)

    collected_messages = []

    @broker.subscriber(queue=NewPaymentQueue, exchange=PaymentExchange)
    async def test_handler(msg):
        collected_messages.append(msg)

    async with TestRabbitBroker(broker):
        published = await publish_events(async_session, batch_size=5)
        assert published == 5

    assert len(collected_messages) == 5

    result = await async_session.execute(select(Outbox))
    outboxes = result.scalars().all()

    processed = list(filter(lambda outbox: outbox.published_at, outboxes))
    assert len(processed) == 5


@pytest.mark.asyncio(loop_scope="session")
async def test_publish_events_partial_failure(async_session):
    await add_outboxes_to_db(async_session, count=3)

    collected_messages = []

    @broker.subscriber(queue=NewPaymentQueue, exchange=PaymentExchange)
    async def test_handler(msg):
        collected_messages.append(msg)

    counter = 0

    async def fake_publish(event):
        nonlocal counter
        counter += 1
        if counter == 2:
            raise Exception("Test exception")
        return await publish_event(event)

    with patch("payment_processing.infrastructure.broker.producer.publish_event", fake_publish):
        async with TestRabbitBroker(broker):
            published = await publish_events(async_session, batch_size=5)

            assert published == 2

    assert len(collected_messages) == 2

    result = await async_session.execute(select(Outbox))
    outboxes = result.scalars().all()

    assert len(list(filter(lambda outbox: outbox.published_at, outboxes))) == 2

    failed_outbox = list(filter(lambda outbox: outbox.published_at is None, outboxes))
    assert len(failed_outbox) == 1

    failed_outbox = failed_outbox[0]
    assert failed_outbox.last_error == "Test exception"


@pytest.mark.asyncio(loop_scope="session")
async def test_run_publisher(async_session, async_session_factory):
    await add_outboxes_to_db(async_session, count=10)

    collected_messages = []

    @broker.subscriber(queue=NewPaymentQueue, exchange=PaymentExchange)
    async def test_handler(msg):
        collected_messages.append(msg)

    async with TestRabbitBroker(broker):
        task = create_task(run_publisher(
            session_factory=async_session_factory,
            batch_size=5,
            pool_interval=0.1,
        ))

        await sleep(2)
        task.cancel()
        try:
            await task
        except CancelledError:
            pass

    assert len(collected_messages) == 10

    result = await async_session.execute(select(Outbox))
    outboxes = result.scalars().all()

    assert all(outbox.published_at for outbox in outboxes)
