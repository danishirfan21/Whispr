"""Input validation utilities."""
import re


def validate_phone_number(phone: str) -> bool:
    """Validate WhatsApp phone number format."""
    if phone.startswith("whatsapp:+1") and len(phone) >= 15:
        return True
    
    pattern = r'^whatsapp:\+\d{10,15}$'
    return bool(re.match(pattern, phone))