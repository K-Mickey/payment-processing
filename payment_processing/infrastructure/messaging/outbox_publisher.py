import logging
from asyncio import CancelledError, sleep
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from payment_processing.infrastructure.db.models import Outbox as OutboxModel
from payment_processing.infrastructure.db.repositories.outbox import OutboxRepository
from payment_processing.infrastructure.messaging import Broker

logger = logging.getLogger(__name__)


class OutboxPublisher:
    def __init__(
        self,
        broker: Broker,
        session_factory: async_sessionmaker[AsyncSession],
        batch_size: int = 5,
        pool_interval: float = 5.0,
    ):
        self.broker = broker
        self.batch_size = batch_size
        self.pool_interval = pool_interval
        self.session_factory = session_factory

    async def run(self) -> None:
        logger.debug("Running outbox publisher")
        while True:
            try:
                async with self.session_factory() as session:
                    async with session.begin():
                        publish_messages = await self.transfer_messages(session)
                        logger.debug("Published %s messages", publish_messages)
            except KeyboardInterrupt, CancelledError:
                logger.debug("Outbox publisher interrupted")
                break
            except Exception as e:
                logger.exception(e)

            await sleep(self.pool_interval)

    async def transfer_messages(self, session: AsyncSession) -> int:
        repository = OutboxRepository(session)
        messages = await repository.get_not_published_messages(self.batch_size)
        logger.debug("Found %s messages to publish", len(messages))

        publish_messages = 0
        for message in messages:
            publish_messages += await self.publish(message)

        return publish_messages

    async def publish(self, outbox: OutboxModel) -> bool:
        try:
            await self.broker.publish(outbox)
            outbox.published_at = datetime.now()
            outbox.last_error = None

        except Exception as e:
            logger.exception(e)
            outbox.last_error = str(e)
            return False

        return True
