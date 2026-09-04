"""Constants for audio-to-text service."""

class AudioConstants:
    TIMEOUT_SEC = 30
    MAX_FILE_SIZE_MB = 25
    MIN_DURATION_SEC = 2.0
    WORDS_PER_SEC_LIMIT = 2.5
    BYTES_PER_SEC_EST = 2000
    MIN_FALLBACK_DURATION = 0.5
    DEFAULT_FALLBACK_DURATION = 5.0


class WhatsAppConstants:
    MAX_MESSAGE_LENGTH = 1600  # WhatsApp message limit via Twilio


class RateLimitConstants:
    TOKENS_PER_HOUR = 20
    REFILL_INTERVAL_SEC = 180


class ErrorResponses:
    TRANSCRIBE_FAILED = "Could not transcribe audio."
    PROCESSING_FAILED = "Audio processing failed."