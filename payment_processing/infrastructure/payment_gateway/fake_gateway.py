from asyncio import sleep
from random import random

from payment_processing.domain import Payment
from payment_processing.domain.interfaces import PaymentProcessor


class FakePaymentProcessor(PaymentProcessor):
    def __init__(self):
        self.min_delay = 2
        self.max_delay = 5
        self.success_rate = 0.9

    async def process(self, payment: Payment) -> bool:
        delay = self.min_delay + (self.max_delay - self.min_delay) * random()
        await sleep(delay)

        return random() < self.success_rate
