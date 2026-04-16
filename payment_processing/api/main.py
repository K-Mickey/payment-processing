from contextlib import asynccontextmanager

from fastapi import FastAPI

from payment_processing.config import settings
from payment_processing.infrastructure import dispose_db, init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db(settings.db)
    yield
    dispose_db()


app = FastAPI(
    title=settings.app.title,
    description=settings.app.description,
    version=settings.app.version,
    docs_url=settings.develop and settings.app.docs_url or None,
    redoc_url=settings.develop and settings.app.redoc_url or None,
    lifespan=lifespan,
)


@app.get("/")
async def index():
    return {"message": "Hello World"}


@app.get("/health")
async def health():
    return {"status": "ok"}
