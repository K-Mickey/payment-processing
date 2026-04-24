ifneq ($(wildcard .env),)
	include .env
endif

install:
	uv sync --frozen && uv cache prune --ci

lint:
	uv run ruff check payment_processing --fix

APP_PORT ?= 8000
dev:
	uv run uvicorn payment_processing.api.main:main --factory --reload --port ${APP_PORT}

APP_HOST ?= 127.0.0.1
APP_WORKERS ?= 1
start:
	uv run uvicorn payment_processing.api.main:main \
		--factory --host ${APP_HOST} --port ${APP_PORT} --workers ${APP_WORKERS}

PAYMENT_CONSUMER_WORKERS ?= 1
start-payment-consumer:
	uv run faststream run payment_processing.infrastructure.broker.consumer:main \
		--factory --workers ${PAYMENT_CONSUMER_WORKERS}

OUTBOX_PRODUCER_WORKERS ?= 1
start-outbox-producer:
	uv run faststream run payment_processing.infrastructure.broker.producer:main \
		--factory --workers ${OUTBOX_PRODUCER_WORKERS}

test:
	uv run pytest

test-coverage:
	uv run pytest --cov=payment_processing --cov-report xml

check: test lint

migrate:
	@if [ -z "$(MSG)" ]; then \
		echo "Error: MSG is required. Usage: make migrate MSG=\"...\""; \
		exit 1; \
	fi; \
	uv run alembic revision --autogenerate -m "$(MSG)"

migrate-up:
	uv run alembic upgrade head

migrate-down:
	uv run alembic downgrade -1

.PHONY: install lint dev start start-payment-consumer start-outbox-producer
.PHONY: test test-coverage check migrate migrate-up migrate-down