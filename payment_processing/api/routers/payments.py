from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, status

from payment_processing.api.dependencies import get_create_payment_handler, get_get_payment_handler, verify_api_key
from payment_processing.api.schemas import CreatePaymentRequest, CreatePaymentResponse, PaymentResponse
from payment_processing.application import (
    CreatePaymentCommand,
    CreatePaymentHandler,
    GetPaymentHandler,
)

router = APIRouter(prefix="/payments", tags=["payments"], dependencies=[Depends(verify_api_key)])


@router.get("/{payment_id}", summary="Get information about payment")
async def get_payment(
    payment_id: UUID,
    handler: Annotated[GetPaymentHandler, Depends(get_get_payment_handler)],
) -> PaymentResponse:
    dto = await handler.execute(payment_id)
    if dto is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return PaymentResponse.model_validate(dto)


@router.post("/", summary="Create payment", status_code=status.HTTP_202_ACCEPTED)
async def create_payment(
    params: CreatePaymentRequest,
    handler: Annotated[CreatePaymentHandler, Depends(get_create_payment_handler)],
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
) -> CreatePaymentResponse:
    command = CreatePaymentCommand(
        amount=params.amount,
        currency=params.currency,
        description=params.description,
        metadata=params.metadata,
        idempotency_key=idempotency_key,
        webhook_url=str(params.webhook_url),
    )
    dto = await handler.execute(command)
    return CreatePaymentResponse.model_validate(dto)
