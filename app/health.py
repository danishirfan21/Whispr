"""Health check utilities for audio-to-text service."""
import asyncio
import logging
import httpx
from twilio.rest import Client as TwilioClient
from openai import AsyncOpenAI, APITimeoutError

from app.config import settings
from app.deps import get_openai_client

logger = logging.getLogger(__name__)

OPENAI_TIMEOUT = 3
TWILIO_TIMEOUT = 3


async def ping_openai() -> str:
    """Check OpenAI API availability."""
    client: AsyncOpenAI = get_openai_client()
    try:
        await asyncio.wait_for(client.models.list(), timeout=OPENAI_TIMEOUT)
        return "ok"
    except (APITimeoutError, httpx.HTTPError, asyncio.TimeoutError) as exc:
        logger.warning(f"OpenAI health check failed: {exc}")
        return str(exc) or "error"


async def ping_twilio() -> str:
    """Check Twilio API availability."""
    try:
        twilio = TwilioClient(settings.twilio_account_sid, settings.twilio_auth_token)
        await asyncio.get_event_loop().run_in_executor(
            None, lambda: twilio.api.accounts(settings.twilio_account_sid).fetch()
        )
        return "ok"
    except Exception as exc:
        logger.warning(f"Twilio health check failed: {exc}")
        return str(exc) or "error"