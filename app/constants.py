"""Constants for audio-to-text service."""

class AudioConstants:
    TIMEOUT_SEC = 30
    MAX_FILE_SIZE_MB = 25
    MIN_DURATION_SEC = 2.0
    WORDS_PER_SEC_LIMIT = 2.5
    BYTES_PER_SEC_EST = 2000
    MIN_FALLBACK_DURATION = 0.5
    DEFAULT_FALLBACK_DURATION = 5.0


class RateLimitConstants:
    TOKENS_PER_HOUR = 20
    REFILL_INTERVAL_SEC = 180


class ErrorResponses:
    RATE_LIMIT = "⚠️ Rate limit exceeded. Please try again later."
    AUDIO_TIMEOUT = "⏱️ Audio processing timeout. Try a shorter recording."
    AUDIO_UNCLEAR = "❌ Could not transcribe audio clearly. Please try again."
    UNSUPPORTED_MEDIA = "⚠️ Only audio files are supported."
    PROCESSING_ERROR = "❌ Processing error occurred. Please try again."