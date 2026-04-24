from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from payment_processing.config import settings
from payment_processing.domain import PaymentStatus
from payment_processing.infrastructure.db.enums import AggregateType, RoutingKey
from payment_processing.infrastructure.db.models import Outbox as OutboxModel
from payment_processing.infrastructure.db.models import Payment as PaymentModel
from payment_processing.infrastructure.db.repositories import SQLAlchemyPaymentRepository

PAYMENTS_URL = f"{settings.app.api_prefix}/payments/"


async def create_payment(async_client: AsyncClient, json: dict, headers: dict | None = None):
    extra_headers = headers or {}
    response = await async_client.post(
        PAYMENTS_URL,
        headers={
            "X-API-Key": settings.api_key,
            "idempotency-key": str(uuid4()),
        }
        | extra_headers,
        json=json,
    )
    return response


async def get_payment(async_client: AsyncClient, payment_id: UUID | str):
    response = await async_client.get(
        f"{PAYMENTS_URL}{payment_id}",
        headers={
            "X-API-Key": settings.api_key,
        },
    )
    return response


def build_payment_payload(**kwargs):
    payload = {
        "amount": "150.25",
        "currency": "RUB",
        "description": "Тестовый платеж через API",
        "metadata": {"source": "автотест"},
        "webhook_url": "http://example.com/webhook",
    }

    for key, value in kwargs.items():
        payload[key] = value

    return payload


@pytest.mark.asyncio(loop_scope="session")
async def test_create_payment(async_client: AsyncClient, async_session: AsyncSession):
    request_json = build_payment_payload()
    response = await create_payment(async_client, request_json)
    assert response.status_code == 202
    data = response.json()
    assert "payment_id" in data

    repository = SQLAlchemyPaymentRepository(async_session)
    payment_id = UUID(data["payment_id"])

    payment = await repository.get_by_id(payment_id)
    assert payment.amount.amount == Decimal(request_json["amount"])
    assert payment.amount.currency == request_json["currency"]
    assert payment.description == request_json["description"]
    assert payment.metadata.data == request_json["metadata"]
    assert payment.status == PaymentStatus.PENDING
    assert payment.webhook_url.url == request_json["webhook_url"]


@pytest.mark.asyncio(loop_scope="session")
async def test_create_payments(async_client: AsyncClient, async_session: AsyncSession):
    for i in range(10):
        request_json = build_payment_payload()
        response = await create_payment(async_client, request_json)
        assert response.status_code == 202

    payments = await async_session.scalars(select(PaymentModel))
    payments = payments.all()
    assert len(payments) == 10


@pytest.mark.asyncio(loop_scope="session")
async def test_incorrect_values(async_client: AsyncClient, async_session: AsyncSession):
    request_jsons = (
        build_payment_payload(amount="invalid_amount"),
        build_payment_payload(amount=-1),
        build_payment_payload(currency="invalid_currency"),
        build_payment_payload(webhook_url="invalid_url"),
        build_payment_payload(metadata=[]),
        build_payment_payload(description=5),
    )

    for request_json in request_jsons:
        response = await create_payment(async_client, request_json)
        assert response.status_code == 422

    payments = await async_session.scalars(select(PaymentModel))
    payments = payments.all()
    assert len(payments) == 0


@pytest.mark.asyncio(loop_scope="session")
async def test_unique_idempotency_key(async_client: AsyncClient, async_session: AsyncSession):
    request_json = build_payment_payload()
    same_idempotency_key = {"idempotency-key": "not_unique_idempotency_key"}
    first_response = await create_payment(async_client, request_json, same_idempotency_key)
    assert first_response.status_code == 202

    second_response = await create_payment(async_client, request_json, same_idempotency_key)
    assert second_response.status_code == 202

    payments = await async_session.scalars(select(PaymentModel))
    payments = payments.all()
    assert len(payments) == 1


@pytest.mark.asyncio(loop_scope="session")
async def test_incorrect_api_key(async_client: AsyncClient):
    request_json = build_payment_payload()
    response = await create_payment(async_client, request_json, {"X-API-Key": "incorrect_api_key"})
    assert response.status_code == 401


@pytest.mark.asyncio(loop_scope="session")
async def test_get_payment(async_client: AsyncClient, async_session: AsyncSession):
    request_json = build_payment_payload()
    response = await create_payment(async_client, request_json)
    assert response.status_code == 202
    data = response.json()
    payment_id = data["payment_id"]

    response = await get_payment(async_client, payment_id)
    assert response.status_code == 200

    data = response.json()
    assert data["payment_id"] == str(payment_id)
    assert data["amount"] == request_json["amount"]
    assert data["currency"] == request_json["currency"]
    assert data["description"] == request_json["description"]
    assert data["metadata"] == request_json["metadata"]
    assert data["status"] == PaymentStatus.PENDING
    assert data["webhook_url"] == request_json["webhook_url"]
    assert datetime.fromisoformat(data["created_at"])
    assert data["processed_at"] is None


@pytest.mark.asyncio(loop_scope="session")
async def test_create_payment_with_outbox(async_client: AsyncClient, async_session: AsyncSession):
    request_json = build_payment_payload()
    response = await create_payment(async_client, request_json)
    assert response.status_code == 202

    outboxes = await async_session.scalars(select(OutboxModel))
    outboxes = outboxes.all()
    assert len(outboxes) == 1

    data = response.json()
    outbox = outboxes[0]
    assert outbox.aggregate_id == UUID(data["payment_id"])
    assert outbox.aggregate_type == AggregateType.PAYMENT
    assert outbox.routing_key == RoutingKey.PAYMENT_NEW
    assert outbox.published_at is None
    assert "payment_id" in outbox.payload


@pytest.mark.asyncio(loop_scope="session")
async def test_unique_idempotency_key_with_outbox(async_client: AsyncClient, async_session: AsyncSession):
    request_json = build_payment_payload()
    same_idempotency_key = {"idempotency-key": "not_unique_idempotency_key"}
    first_response = await create_payment(async_client, request_json, same_idempotency_key)
    assert first_response.status_code == 202

    second_response = await create_payment(async_client, request_json, same_idempotency_key)
    assert second_response.status_code == 202

    outboxes = await async_session.scalars(select(OutboxModel))
    outboxes = outboxes.all()
    assert len(outboxes) == 1


@pytest.mark.asyncio(loop_scope="session")
async def test_get_payments_with_outbox(async_client: AsyncClient, async_session: AsyncSession):
    for i in range(10):
        request_json = build_payment_payload()
        response = await create_payment(async_client, request_json)
        assert response.status_code == 202

    outboxes = await async_session.scalars(select(OutboxModel))
    outboxes = outboxes.all()
    assert len(outboxes) == 10
