install:
	uv sync --frozen && uv cache prune --ci

lint:
	uv run ruff check payment-processing --fix

dev:
	uv run

PORT ?= 8000
start:
	uv run

test:
	uv run pytest

test-coverage:
	uv run pytest --cov=payment-processing --cov-report xml

check: test lint

.PHONY: install lint dev start test test-coverage check