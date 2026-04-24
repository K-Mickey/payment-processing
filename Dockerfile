FROM python:3.14-alpine as base

ENV PYTHONUNBUFFERED=1 \
  PYTHONDONTWRITEBYTECODE=1

RUN apk add --no-cache libpq-dev curl
RUN pip install --no-cache-dir uv

WORKDIR /app

COPY pyproject.toml uv.lock ./

RUN uv sync --frozen --no-dev --no-editable

COPY payment_processing/ ./payment_processing/
COPY alembic.ini ./
COPY alembic/ ./alembic/

CMD ["uv", "run", "uvicorn", "payment_processing.api.main:main", "--factory", "--host", "0.0.0.0", "--port", "8000"]