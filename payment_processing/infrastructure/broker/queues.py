from faststream.rabbit import ExchangeType, RabbitExchange, RabbitQueue

DeadLetterExchange = RabbitExchange(
    "payment.dlx",
    type=ExchangeType.DIRECT,
    durable=True,
)
DeadLetterQueue = RabbitQueue(
    "payment.dlq",
    durable=True,
)

NewPaymentQueue = RabbitQueue(
    "payment.new",
    durable=True,
    arguments={
        "x-dead-letter-exchange": DeadLetterExchange.name,
        "x-dead-letter-routing-key": DeadLetterQueue.name,
    },
)
PaymentExchange = RabbitExchange(
    "payment.exchange",
    type=ExchangeType.DIRECT,
    durable=True,
)
