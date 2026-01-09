"""Utility functions for audio-to-text service."""


def sanitize_phone_number(phone: str) -> str:
    """Extract clean phone number for rate limiting."""
    return phone.replace("whatsapp:", "").strip()