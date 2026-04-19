import logging
from asyncio import sleep

from faststream.rabbit import RabbitBroker, RabbitQueue

from payment_processing.infrastructure.messaging import Outbox

logger = logging.getLogger(__name__)


class Broker:
    def __init__(self, url: str):
        self.broker = RabbitBroker(url=url)
        self._declare_queues: set[str] = set()

    async def start(self, attempts: int = 3, delay: float = 5.0) -> None:
        for attempt in range(attempts):
            try:
                await self.broker.start()
                logger.debug("Broker started")
                return
            except Exception as e:
                logger.exception(e)

            logger.debug("Retrying start broker in %s seconds, attempt %s/%s", delay, attempt + 1, attempts)
            await sleep(delay)

        raise RuntimeError("Failed to start broker")

    async def stop(self) -> None:
        await self.broker.stop()
        logger.debug("Broker stopped")

    async def publish(self, outbox: Outbox) -> None:
        await self._declare_queue(outbox.topic)
        await self.broker.publish(
            message=outbox.payload,
            queue=outbox.topic,
            headers=outbox.headers,
            message_id=str(outbox.id),
            persist=True,
        )
        logger.debug("Published outbox %s to queue %s", outbox.id, outbox.topic)

    async def _declare_queue(self, queue_name: str) -> None:
        if queue_name not in self._declare_queues:
            queue = RabbitQueue(name=queue_name, durable=True)
            await self.broker.declare_queue(queue)
            self._declare_queues.add(queue_name)
            logger.debug("Declared queue %s", queue_name)
