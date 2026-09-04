"""Constants for audio-to-text service."""

class AudioConstants:
    TIMEOUT_SEC = 30
    MAX_FILE_SIZE_MB = 25
    MIN_DURATION_SEC = 2.0
    WORDS_PER_SEC_LIMIT = 2.5
    BYTES_PER_SEC_EST = 2000
    MIN_FALLBACK_DURATION = 0.5
    DEFAULT_FALLBACK_DURATION = 5.0

    # Map Twilio's MediaContentType0 to the file extension OpenAI's
    # transcription API expects. WhatsApp voice notes are usually
    # "audio/ogg" but other clients can send other formats - assuming
    # .ogg for all of them produces a filename/content mismatch that
    # Whisper rejects as "corrupted or unsupported".
    CONTENT_TYPE_EXTENSIONS = {
        "audio/ogg": ".ogg",
        "application/ogg": ".ogg",
        "audio/opus": ".ogg",
        "audio/mpeg": ".mp3",
        "audio/mp3": ".mp3",
        "audio/mp4": ".m4a",
        "audio/x-m4a": ".m4a",
        "audio/aac": ".aac",
        "audio/webm": ".webm",
        "audio/wav": ".wav",
        "audio/x-wav": ".wav",
        "audio/vnd.wave": ".wav",
        "audio/flac": ".flac",
        "audio/amr": ".amr",
        "audio/3gpp": ".3gp",
    }
    DEFAULT_AUDIO_EXTENSION = ".ogg"


class WhatsAppConstants:
    MAX_MESSAGE_LENGTH = 1600  # WhatsApp message limit via Twilio


class RateLimitConstants:
    TOKENS_PER_HOUR = 20
    REFILL_INTERVAL_SEC = 180


class ErrorResponses:
    TRANSCRIBE_FAILED = "Could not transcribe audio."
    PROCESSING_FAILED = "Audio processing failed."