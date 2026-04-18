from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from payment_processing.config import settings
from payment_processing.domain import PaymentStatus
from payment_processing.infrastructure.db.repositories import PaymentRepository

PAYMENTS_URL = f"{settings.app.api_prefix}/payments/"


def build_payment_payload(**kwargs):
    payload = {
        "idempotency_key": str(uuid4()),
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
    response = await async_client.post(
        PAYMENTS_URL,
        json=request_json,
    )
    assert response.status_code == 200
    data = response.json()
    assert "payment_id" in data

    repository = PaymentRepository(async_session)
    payment_id = UUID(data["payment_id"])

    payment = await repository.get_by_id(payment_id)
    assert payment.idempotency_key == request_json["idempotency_key"]
    assert payment.amount == Decimal(request_json["amount"])
    assert payment.currency == request_json["currency"]
    assert payment.description == request_json["description"]
    assert payment.metadata == request_json["metadata"]
    assert payment.status == PaymentStatus.PENDING
    assert payment.webhook_url == request_json["webhook_url"]


@pytest.mark.asyncio(loop_scope="session")
async def test_incorrect_values(async_client: AsyncClient, async_session: AsyncSession):
    request_jsons = (
        build_payment_payload(amount="invalid_amount"),
        build_payment_payload(amount=-1),
        build_payment_payload(currency="invalid_currency"),
        build_payment_payload(idempotency_key=5),
        build_payment_payload(webhook_url="invalid_url"),
        build_payment_payload(metadata=[]),
        build_payment_payload(description=5),
    )

    for request_json in request_jsons:
        response = await async_client.post(
            PAYMENTS_URL,
            json=request_json,
        )
        assert response.status_code == 422


@pytest.mark.asyncio(loop_scope="session")
async def test_unique_idempotency_key(async_client: AsyncClient, async_session: AsyncSession):
    request_json = build_payment_payload(idempotency_key="unique_idempotency_key")
    response = await async_client.post(
        PAYMENTS_URL,
        json=request_json,
    )
    assert response.status_code == 200

    new_response = await async_client.post(
        PAYMENTS_URL,
        json=request_json,
    )
    assert new_response.status_code == 409

    repository = PaymentRepository(async_session)
    payments = await repository.get_all()
    assert len(payments) == 1


@pytest.mark.asyncio(loop_scope="session")
async def test_get_payment(async_client: AsyncClient, async_session: AsyncSession):
    request_json = build_payment_payload()
    response = await async_client.post(
        PAYMENTS_URL,
        json=request_json,
    )
    assert response.status_code == 200
    data = response.json()
    payment_id = UUID(data["payment_id"])

    response = await async_client.get(
        f"{PAYMENTS_URL}{payment_id}",
    )
    assert response.status_code == 200

    data = response.json()
    assert data["payment_id"] == str(payment_id)
    assert data["idempotency_key"] == request_json["idempotency_key"]
    assert data["amount"] == request_json["amount"]
    assert data["currency"] == request_json["currency"]
    assert data["description"] == request_json["description"]
    assert data["metadata"] == request_json["metadata"]
    assert data["status"] == PaymentStatus.PENDING
    assert data["webhook_url"] == request_json["webhook_url"]
    assert datetime.fromisoformat(data["created_at"])
    assert data["processed_at"] is None


@pytest.mark.asyncio(loop_scope="session")
async def test_get_payments(async_client: AsyncClient, async_session: AsyncSession):
    for i in range(10):
        request_json = build_payment_payload()
        response = await async_client.post(
            PAYMENTS_URL,
            json=request_json,
        )
        assert response.status_code == 200

    response = await async_client.get(
        PAYMENTS_URL,
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 10
