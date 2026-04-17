ifneq ($(wildcard .env),)
	include .env
endif

install:
	uv sync --frozen && uv cache prune --ci

lint:
	uv run ruff check payment_processing --fix

PORT ?= 8000
dev:
	uv run uvicorn payment_processing.api:app --reload --port ${PORT}

HOST ?= 127.0.0.1
WORKERS ?= 1
start:
	uv run uvicorn payment_processing.api:app --host ${HOST} --port ${PORT} --workers ${WORKERS}

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

.PHONY: install lint dev start test test-coverage check migrate migrate-up migrate-down