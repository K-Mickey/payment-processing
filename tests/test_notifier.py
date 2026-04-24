from unittest.mock import AsyncMock, Mock, patch
from uuid import UUID

import pytest
from aiohttp import ClientResponseError

from payment_processing.domain import PaymentStatus
from payment_processing.infrastructure.webhook import AiohttpWebhookNotifier


@pytest.fixture
def notifier():
    return AiohttpWebhookNotifier(timeout=5.0)


@pytest.mark.asyncio(loop_scope="session")
async def test_notify_success(notifier):
    payment_id = UUID("123e4567-e89b-12d3-a456-426614174000")
    webhook_url = "https://example.com/webhook"
    status = PaymentStatus.SUCCESS

    with patch("payment_processing.infrastructure.webhook.notifier.ClientSession") as MockSession:
        mock_session = Mock()
        mock_post_cm = AsyncMock()
        mock_response = Mock()
        mock_response.status = 200
        mock_response.raise_for_status = Mock()

        mock_post_cm.__aenter__.return_value = mock_response
        mock_post_cm.__aexit__.return_value = None
        mock_session.post.return_value = mock_post_cm
        MockSession.return_value.__aenter__.return_value = mock_session

        result = await notifier.notify(payment_id, status, webhook_url)

        assert result is True
        mock_session.post.assert_called_once_with(webhook_url, json={"payment_id": str(payment_id), "status": status})


@pytest.mark.asyncio
async def test_notify_http_error(notifier):
    payment_id = UUID("456e4567-e89b-12d3-a456-426614174111")
    webhook_url = "https://example.com/webhook"
    status = PaymentStatus.FAILED

    with patch("payment_processing.infrastructure.webhook.notifier.ClientSession") as MockSession:
        mock_session = Mock()
        mock_post = AsyncMock()
        mock_response = Mock()
        mock_response.raise_for_status = Mock(
            side_effect=ClientResponseError(
                request_info=Mock(),
                history=(),
                status=404,
                message="Not Found",
            )
        )
        mock_post.__aenter__.return_value = mock_response
        mock_post.__aexit__.return_value = None
        mock_session.post.return_value = mock_post
        MockSession.return_value.__aenter__.return_value = mock_session

        result = await notifier.notify(payment_id, status, webhook_url)

        assert result is False
        mock_session.post.assert_called_once()
