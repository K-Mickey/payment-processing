# Payment Processing Service

[![SonarQube Cloud](https://sonarcloud.io/images/project_badges/sonarcloud-light.svg)](https://sonarcloud.io/summary/new_code?id=K-Mickey_payment-processing)

[![Python CI](https://github.com/K-Mickey/payment-processing/actions/workflows/pyci.yml/badge.svg)](https://github.com/K-Mickey/payment-processing/actions/workflows/pyci.yml)
[![Coverage](https://sonarcloud.io/api/project_badges/measure?project=K-Mickey_payment-processing&metric=coverage)](https://sonarcloud.io/summary/new_code?id=K-Mickey_payment-processing)

## Description

This service accepts payment requests, asynchronously processes them through an external payment gateway, 
and notifies the client via webhook.

### Key Features

- Guaranteed delivery of events through the `outbox` pattern.
- Idempotency protection for duplicate requests.
- Emulation of an external payment gateway: 2-5 seconds, 90% success, 10% error.
- Dead Letter Queue for failed payments.
- Sending notifications to `webhook_url` with repeated attempts.
- Working in a Docker environment: PostgreSQL, RabbitMQ, API, outbox consumer, payment consumer.

### API

- [Create a payment](#create-a-payment)
- [Get payment information](#get-payment-information)
- [Health check](#health-check)

### Architecture

- **`api`** HTTP interface on FastAPI
- **`domain`** core business logic
- **`application`** use cases: payment creation and update scenarios, without binding to DB or RabbitMQ.
- **`infrastructure`**:  
    - **`db`** ORM models and repositories;
    - **`broker`** RabbitMQ producer and consumer;
    - **`webhooks`** HTTP client for webhook sending;
    - **`payment_gateway`** HTTP client for external payment gateway;
  
## Installation

### Running with Docker

After downloading the repository, run [Docker Compose](https://docs.docker.com/compose) of the root directory:

```bash
docker-compose up -d --build
```

You can create `.env` file in the root directory and override the environment variables.

### Running manually

If you want to run the service manually, you need to prepare:
- [PostgreSQL](https://www.postgresql.org/download/) 
- [RabbitMQ](https://www.rabbitmq.com/) 
- [UV](https://docs.astral.sh/uv/)
- Set required environment variables for `RabbitMQ` and `PostgreSQL` in the `.env` file.

After use the commands:
```bash
# Install dependencies
make install

# Run the App
make start  
# Run Outbox producer
make start-outbox-producer
# Run Payment consumer
make start-payment-consumer
```

Also, you can use commands for manage migrations:
```bash
# Make migrations
make migrate
# Run migrations
make migrate-up
# Drop migrations
make migrate-down
```

You can find other commands in the [Makefile](https://github.com/K-Mickey/payment-processing/blob/master/Makefile).

## Environment

Full list of environment variables you can find in 
[config.py](https://github.com/K-Mickey/payment-processing/blob/master/payment_processing/config.py).

### The most important ones

**App**
- `API_KEY` secret key for authentication, default `secret`;
- `DEVELOP` flag for development environment(Docs are only available if `True`), default `False`;
- `LOG_LEVEL` logging level, default `INFO`;

- `APP_HOST` host for the App, default `localhost`;
- `APP_PORT` port for the App, default `8000`;
- `APP_WORKERS` number of workers for the App, default `1`;

- `OUTBOX_PRODUCER_WORKERS` number of workers for the Outbox producer, default `1`;
- `PAYMENT_CONSUMER_WORKERS` number of workers for the Payment consumer, default `1`;

**Broker**
- `BROKER_USER` username for RabbitMQ, default `admin`;
- `BROKER_PASSWORD` password for RabbitMQ, default `admin`;
- `BROKER_HOST` host for RabbitMQ, default `localhost`;
- `BROKER_PORT` port for RabbitMQ, default `5672`;

**Database**
- `DB_USER` username for PostgreSQL, default `postgres`;
- `DB_PASSWORD` password for PostgreSQL, default `postgres`;
- `DB_HOST` host for PostgreSQL, default `localhost`;
- `DB_PORT` port for PostgreSQL, default `5432`;
- `DB_NAME` name for PostgreSQL, default `payment_db`;

## Using

After running the App you can open [Swagger](http://localhost:8000/docs) or [Redoc](http://localhost:8000/redoc) docs.
If they can't open, check `DEVELOP` flag in `.env`, it must be `True`. Also don't forget about `API_KEY`.

You can find your running `RabbitMQ` [here](http://localhost:15672/), default credentials `admin:admin`.

Default DSN for `PostgreSQL`: `postgresql+asyncpg://postgres:postgres@localhost:5432/payment_db`

### Create a payment

`POST /api/v1/payments` 

**Headers:**
- `X-API-Key` secret key for authentication;
- `Idempotency-Key` unique key for idempotency protection;

**Body:**
- `amount` Decimal, example: 150.00;
- `currency` string("RUB", "USD", "EUR"), example: "USD";
- `description` string, example: "Test payment";
- `metadata` dict, example: {"source": "curl"};
- `webhook_url` string, valid URL, example: "https://example.com/webhook";

**Response:**
- `payment_id` UUID;
- `status` string("Processing", "Success", "Failure");
- `created_at` datetime;

#### Examples

_Request:_
```shell
curl -X POST "http://127.0.0.1:8000/api/v1/payments" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: secret" \
  -H "Idempotency-Key: key-01" \
  -d '{
    "amount": 150.00,
    "currency": "USD",
    "description": "Test payment",
    "metadata": {
      "source": "curl"
    },
    "webhook_url": "https://example.com/webhook"
  }'
```

_Response (202)_
```json
{
  "payment_id": "0f4e5a6b-7a2c-4b0a-a3b4-c5d6e7f8a9b0",
  "status": "pending",
  "created_at": "2026-04-25T21:00:00Z"
}
```

### Get payment information

`GET /api/v1/payments/{payment_id}`

**Headers:**
- `X-API-Key` secret key for authentication;

**Response:**
- `payment_id` UUID;
- `amount` Decimal;
- `currency` string("RUB", "USD", "EUR");
- `status` string("Processing", "Success", "Failure");
- `description` string;
- `metadata` dict;
- `idempotency_key` string;
- `webhook_url` string;
- `created_at` datetime;
- `processed_at` datetime;

#### Examples

_Request:_
```shell
curl -X GET "http://127.0.0.1:8000/api/v1/payments/0f4e5a6b-7a2c-4b0a-a3b4-c5d6e7f8a9b0" \
  -H "X-API-Key: secret"
```

_Response (200)_
```json
{
  "payment_id": "0f4e5a6b-7a2c-4b0a-a3b4-c5d6e7f8a9b0",
  "amount": 150.0,
  "currency": "USD",
  "status": "pending",
  "description": "Test payment",
  "metadata": {
    "source": "curl"
  },
  "idempotency_key": "key-01",
  "webhook_url": "https://example.com/webhook",
  "created_at": "2026-04-25T21:00:00Z",
  "processed_at": "2026-04-25T21:00:00Z"
}
```

### Health check

`GET /api/v1/health`

#### Examples

_Request:_
```shell
curl -X GET "http://127.0.0.1:8000/api/v1/health"
```

_Response (200)_
```json
{
  "status": "ok"
}
```

## License

This project is licensed under the MIT License - see the 
[LICENSE](https://github.com/K-Mickey/payment-processing/blob/master/LICENSE) file for details.