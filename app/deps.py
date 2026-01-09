"""Dependency injection for external clients."""
from functools import lru_cache
from openai import AsyncOpenAI
from twilio.rest import Client as TwilioClient

from app.config import settings


@lru_cache()
def get_openai_client() -> AsyncOpenAI:
    """Get AsyncOpenAI client instance."""
    return AsyncOpenAI(api_key=settings.openai_api_key)


@lru_cache()
def get_twilio_client() -> TwilioClient:
    """Get Twilio client instance."""
    return TwilioClient(settings.twilio_account_sid, settings.twilio_auth_token)