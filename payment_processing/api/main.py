from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI
from starlette.responses import RedirectResponse

from payment_processing.config import settings
from payment_processing.infrastructure.db import dispose_db, init_db

from .routers import health_router, payments_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db(settings.db)
    yield
    await dispose_db()


def get_router():
    router = APIRouter(prefix=settings.app.api_prefix)
    router.include_router(health_router)
    router.include_router(payments_router)
    return router


app = FastAPI(
    title=settings.app.title,
    description=settings.app.description,
    version=settings.app.version,
    docs_url=settings.develop and settings.app.docs_url or None,
    redoc_url=settings.develop and settings.app.redoc_url or None,
    lifespan=lifespan,
)

app.include_router(get_router())


@app.get("/")
async def develop_handler():
    if settings.develop:
        return RedirectResponse(url=settings.app.docs_url)
    return None
