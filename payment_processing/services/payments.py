from http import HTTPStatus
from uuid import UUID

from fastapi import HTTPException

from payment_processing.api.schemas import CreatePaymentRequest, CreatePaymentResponse, PaymentResponse
from payment_processing.domain import Payment
from payment_processing.domain.errors import PaymentNotFoundError
from payment_processing.infrastructure.db.repositories import PaymentRepository
from payment_processing.infrastructure.messaging import AggregateType, Outbox, TopicType


class PaymentService:
    def __init__(self, payment_repository: PaymentRepository):
        self.payment_repository = payment_repository

    async def get_payment(self, payment_id: UUID) -> PaymentResponse:
        try:
            payment = await self.payment_repository.get_by_id(payment_id)
        except PaymentNotFoundError:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND,
                detail=f"Payment {payment_id} not found",
            )
        except Exception as e:
            raise HTTPException(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                detail=f"Error getting payment {payment_id}: {e}",
            )

        return PaymentResponse.model_validate(payment)

    async def get_payments(self) -> list[PaymentResponse]:
        try:
            payments = await self.payment_repository.get_all()
        except Exception as e:
            raise HTTPException(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                detail=f"Error getting payments: {e}",
            )

        return [PaymentResponse.model_validate(payment) for payment in payments]

    async def create_payment(self, params: CreatePaymentRequest) -> CreatePaymentResponse:
        if await self.payment_repository.exists_by_idempotency_key(params.idempotency_key):
            raise HTTPException(
                status_code=HTTPStatus.CONFLICT,
                detail=f"Payment with idempotency key {params.idempotency_key} already exists",
            )

        payment = Payment.create(**params.model_dump())
        outbox = Outbox.create(
            aggregate_type=AggregateType.PAYMENT,
            aggregate_id=payment.payment_id,
            topic=TopicType.PAYMENT_NEW,
            payload={},
            headers={},
        )

        try:
            payment = await self.payment_repository.create_with_outbox(payment, outbox)
        except Exception as e:
            raise HTTPException(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                detail=f"Error creating payment: {e}",
            )

        return CreatePaymentResponse.model_validate(payment, extra="allow")
