from asyncio import sleep
from random import random


class PaymentProcessor:
    def __init__(self):
        self.min_delay = 2
        self.max_delay = 5
        self.success_rate = 0.9

    async def process_payment(self) -> bool:
        delay = self.min_delay + (self.max_delay - self.min_delay) * random()
        await sleep(delay)

        return random() < self.success_rate
