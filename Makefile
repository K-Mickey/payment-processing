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

.PHONY: install lint dev start test test-coverage check