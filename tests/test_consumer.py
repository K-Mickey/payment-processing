from decimal import Decimal
from unittest.mock import AsyncMock, Mock
from uuid import UUID

import pytest

from payment_processing.config import settings
from payment_processing.domain import Currency, Payment, PaymentStatus
from payment_processing.infrastructure.broker.consumer import get_payment_handler, process_payment
from payment_processing.infrastructure.db.models import Payment as PaymentModel
from payment_processing.infrastructure.db.repositories import SQLAlchemyPaymentRepository


async def create_payment(async_session) -> UUID:
    repository = SQLAlchemyPaymentRepository(async_session)
    payment = await repository.save(Payment.create(
        amount=Decimal("10.00"),
        currency=Currency.USD,
        description="Payment for order #123",
        metadata={"order_id": 123},
        idempotency_key='key',
        webhook_url="https://example.com/webhook",
    ))
    await async_session.commit()
    return payment.id


@pytest.mark.asyncio(loop_scope="session")
async def test_successful_payment_processing(async_session, async_session_factory):
    payment_id = await create_payment(async_session)

    message_mock = AsyncMock()
    notifier_mock = Mock()
    notifier_mock.notify = AsyncMock(return_value=True)

    await process_payment(
        msg={"payment_id": str(payment_id)},
        message=message_mock,
        logger=Mock(),
        handler=get_payment_handler(async_session_factory),
        notifier=notifier_mock,

    )

    result = await async_session.get(PaymentModel, payment_id)
    assert result.id == payment_id
    assert result.status in (PaymentStatus.SUCCESS, PaymentStatus.FAILED)
    assert result.processed_at

    message_mock.ack.assert_called_once()
    notifier_mock.notify.assert_called_once()


@pytest.mark.asyncio(loop_scope="session")
async def test_payment_processing_all_retries_fail(async_session, async_session_factory):
    payment_id = await create_payment(async_session)

    message_mock = AsyncMock()
    notifier_mock = Mock()
    notifier_mock.notify = AsyncMock(return_value=True)
    handler_mock = Mock()
    handler_mock.execute = AsyncMock(side_effect=Exception("Test exception"))

    await process_payment(
        msg={"payment_id": str(payment_id)},
        message=message_mock,
        logger=Mock(),
        handler=handler_mock,
        notifier=notifier_mock,

    )

    result = await async_session.get(PaymentModel, payment_id)
    assert result.id == payment_id
    assert result.status == PaymentStatus.PENDING
    assert result.processed_at is None

    assert handler_mock.execute.await_count == 3
    message_mock.nack.assert_called_once()
    notifier_mock.notify.assert_not_awaited()


@pytest.mark.asyncio(loop_scope="session")
async def test_successful_payment_webhook_retries( async_session, async_session_factory ):
    payment_id = await create_payment(async_session)

    message_mock = AsyncMock()
    notifier_mock = Mock()
    notifier_mock.notify = AsyncMock(side_effect=[False, False, True])

    await process_payment(
        msg={"payment_id": str(payment_id)},
        message=message_mock,
        logger=Mock(),
        handler=get_payment_handler(async_session_factory),
        notifier=notifier_mock,

    )

    result = await async_session.get(PaymentModel, payment_id)
    assert result.id == payment_id
    assert result.status in (PaymentStatus.SUCCESS, PaymentStatus.FAILED)
    assert result.processed_at

    message_mock.ack.assert_called_once()
    assert notifier_mock.notify.await_count == 3
