import logging
from uuid import UUID

from aiohttp import ClientSession, ClientTimeout

from payment_processing.domain.interfaces import WebhookNotifier

logger = logging.getLogger(__name__)


class AiohttpWebhookNotifier(WebhookNotifier):
    def __init__(self, timeout: float = 10.0):
        self._timeout = ClientTimeout(total=timeout)

    async def notify(self, payment_id: UUID, status: str, webhook_url: str) -> bool:
        payload = {
            "payment_id": str(payment_id),
            "status": status,
        }

        try:
            async with ClientSession(timeout=self._timeout) as session:
                async with session.post(webhook_url, json=payload) as response:
                    response.raise_for_status()
                    logger.info(f"Webhook for payment {payment_id} sent successfully")
                    return True

        except Exception as e:
            logger.warning(f"Webhook for payment {payment_id} exception: {e}")

        return False
