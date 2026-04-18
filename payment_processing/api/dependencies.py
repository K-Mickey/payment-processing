from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from payment_processing.infrastructure.db import get_session
from payment_processing.infrastructure.db.repositories import PaymentRepository
from payment_processing.services import PaymentService


async def get_payment_repository(session: AsyncSession = Depends(get_session)):
    return PaymentRepository(session)


async def get_payment_service(payment_repository: PaymentRepository = Depends(get_payment_repository)):
    return PaymentService(payment_repository)
