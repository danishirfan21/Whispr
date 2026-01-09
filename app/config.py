"""Configuration management - Pure Audio-to-Text Service."""
from pydantic_settings import BaseSettings
from pydantic import validator
import logging

logger = logging.getLogger(__name__)

class Settings(BaseSettings):
    """Application settings - Audio-to-Text only."""
    
    # Required credentials
    openai_api_key: str
    twilio_account_sid: str
    twilio_auth_token: str
    twilio_sender_number: str
    
    # Defaults
    verify_twilio_signature: bool = False
    max_requests_per_hour: int = 20
    downloads_dir: str = "downloads"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    @validator('twilio_sender_number')
    def validate_phone_number(cls, v):
        if not v.startswith('whatsapp:+'):
            raise ValueError('Sender number must start with whatsapp:+')
        return v

    @validator('openai_api_key')
    def validate_api_key(cls, v):
        if not v.startswith('sk-'):
            logger.warning("OpenAI API key format seems incorrect")
        return v

settings = Settings()