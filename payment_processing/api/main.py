from fastapi import FastAPI

from payment_processing.api.config import settings

app = FastAPI(
    title=settings.app.title,
    description=settings.app.description,
    version=settings.app.version,
    docs_url=settings.develop and settings.app.docs_url or None,
    redoc_url=settings.develop and settings.app.redoc_url or None,
)


@app.get("/")
async def index():
    return {"message": "Hello World"}


@app.get("/health")
async def health():
    return {"status": "ok"}
