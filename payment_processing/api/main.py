import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from payment_processing.api.routers import health_router, payments_router
from payment_processing.config import settings
from payment_processing.infrastructure.db import dispose_db, init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db(settings.db)
    try:
        yield

    finally:
        await dispose_db()


def create_app():
    app = FastAPI(
        title=settings.app.title,
        description=settings.app.description,
        version=settings.app.version,
        docs_url=settings.develop and settings.app.docs_url or None,
        redoc_url=settings.develop and settings.app.redoc_url or None,
        lifespan=lifespan,
    )

    prefix = settings.app.api_prefix
    app.include_router(health_router, prefix=prefix)
    app.include_router(payments_router, prefix=prefix)

    return app


def main():
    logging.basicConfig(
        level=settings.log_level,
        format=settings.log_format,
    )
    return create_app()
