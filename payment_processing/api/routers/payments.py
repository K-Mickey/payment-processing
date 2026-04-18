from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends

from payment_processing.api.dependencies import get_payment_service
from payment_processing.api.schemas import CreatePaymentRequest, CreatePaymentResponse, PaymentResponse
from payment_processing.services import PaymentService

router = APIRouter(
    prefix="/payments",
    tags=["payments"],
)


@router.get("/")
async def get_payments(
    service: Annotated[PaymentService, Depends(get_payment_service)],
) -> list[PaymentResponse]:
    return await service.get_payments()


@router.get("/{payment_id}")
async def get_payment(
    payment_id: UUID,
    service: Annotated[PaymentService, Depends(get_payment_service)],
) -> PaymentResponse:
    return await service.get_payment(payment_id)


@router.post("/")
async def create_payment(
    params: CreatePaymentRequest,
    service: Annotated[PaymentService, Depends(get_payment_service)],
) -> CreatePaymentResponse:
    return await service.create_payment(params)
