# Payment Processing Service

[![Quality gate](https://sonarcloud.io/api/project_badges/quality_gate?project=K-Mickey_payment-processing)](https://sonarcloud.io/summary/new_code?id=K-Mickey_payment-processing)
[![Python CI](https://github.com/K-Mickey/payment-processing/actions/workflows/pyci.yml/badge.svg)](https://github.com/K-Mickey/payment-processing/actions/workflows/pyci.yml)

## Description

This microservice accepts payment requests, 
asynchronously processes them through an external payment gateway (emulation), and notifies the client via webhook.

### Key Features:

- Create a payment (`POST /api/v1/payments`) with an idempotency key.
- Get payment information (`GET /api/v1/payments/{payment_id}`).
- Guaranteed delivery of events through the `outbox` pattern.
- Idempotency protection for duplicate requests.
- Emulation of an external payment gateway: 2-5 seconds, 90% success, 10% error.
- Sending notifications to `webhook_url` with repeated attempts.
- Working in a Docker environment: PostgreSQL, RabbitMQ, API, outbox consumer, payment consumer.

## Architecture

- **`api`** HTTP interface on FastAPI: accepts requests, validates data, returns `202 Accepted` and payment ID.
- **`domain`** core business logic: entities, value objects, domain events, invariants and errors.
- **`application`** use cases: payment creation and update scenarios, without binding to DB or RabbitMQ.
- **`infra`** infrastructure:  
    - ORM models (`Payment`, `Outbox`);  
    - repositories (`PaymentRepository`, `OutboxRepository`);  
    - `OutboxPublisher` (consumer, publishing events to RabbitMQ);  
    - webhook sending logic.
- **`outbox_consumer`** separate consumer, reading `outbox` table and publishing events to RabbitMQ.
- **`payment_consumer`** consumer, handling payments, updating status and sending webhooks.

## Description of the domain

The domain of the project is focused on the concept of a payment and its lifecycle.

### Main concepts of the domain

- **`Payment`**  
  Entity with a unique identifier, amount, currency, description, status, webhook URL and `idempotency_key`.  
  - Statuses: `pending`, `succeeded`, `failed`.  
  - Payment can be created only in status `pending`.  
  - Payment can be transitioned to `succeeded` or `failed` only from `pending`

- **`Currency` / `CurrencyCode`**  
  Value object representing a currency (`RUB`, `USD`, `EUR`), separated from a string and used in `Money`.

- **`Money`**  
  Value object that combines `amount` and `currency`, representing a payment amount.

- **`WebhookURL`**  
  Value object representing a webhook URL with base validation and schema.

- **`IdempotencyKey`**  
  String key used for duplicate request protection.

### Domain events

- **`PaymentCreated`**  
  Event generated when a new payment is created. Contains `payment_id` and other minimal information.

- **`PaymentStatusChanged`**  
  Event generated when the status of a payment changes.

### Domain errors

- **`InvalidPaymentStatusTransitionError`**  
  Invariant that ensures that a payment can only be transitioned to `succeeded` or `failed` from `pending`.

- **`IdempotencyKeyConflictError`**  
  Invariant that ensures that a payment can only be created with a unique `idempotency_key`.

## How it works

- `Payment` entity located in `domain/entities/payment.py` and contains methods `succeed()` and `fail()`.  
- `Money`, `CurrencyCode`, `WebhookURL` located in `domain/value_objects.py`.  
- `PaymentCreated` and `PaymentStatusChanged` located in `domain/events.py`.  
- Domain errors located in `domain/errors.py`.
- Any operations with the database, RabbitMQ, HTTP or logging are outside the domain, in `application` and `infra`.

## Variables

- `HOST` - host of the API.
- `PORT` - port of the API.
- `WORKERS` - number of threads for the API.
- see others in `config.py`
