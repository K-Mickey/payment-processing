from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from payment_processing.application import CreatePaymentHandler, GetPaymentHandler
from payment_processing.config import settings
from payment_processing.infrastructure.db import get_session, get_session_factory
from payment_processing.infrastructure.db.repositories import (
    SQLAlchemyPaymentRepository,
    SqlAlchemyUnitOfWork,
)


async def verify_api_key(x_api_key: str = Header(..., alias="X-API-Key")):
    if x_api_key != settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing X-API-Key header",
        )
    return x_api_key


async def get_payment_repo(session: AsyncSession = Depends(get_session)) -> SQLAlchemyPaymentRepository:
    return SQLAlchemyPaymentRepository(session)


async def get_uow() -> SqlAlchemyUnitOfWork:
    session_factory = await get_session_factory()
    return SqlAlchemyUnitOfWork(session_factory)


async def get_create_payment_handler(
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
) -> CreatePaymentHandler:
    return CreatePaymentHandler(uow)


async def get_get_payment_handler(
    payment_repo: SQLAlchemyPaymentRepository = Depends(get_payment_repo),
) -> GetPaymentHandler:
    return GetPaymentHandler(payment_repo)
