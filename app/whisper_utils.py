"""Audio processing using OpenAI Whisper - Stateless (Vercel-compatible)."""
import uuid
import aiohttp
import asyncio
import logging
from io import BytesIO
from typing import Optional

from app.config import settings
from app.deps import get_openai_client
from app.constants import AudioConstants

logger = logging.getLogger(__name__)


async def download_audio_to_memory(media_url: str) -> Optional[BytesIO]:
    """Download audio file from Twilio media URL directly to memory (stateless)."""
    # Input validation
    if not media_url or not media_url.startswith('http'):
        logger.error("Invalid media URL")
        return None

    try:
        auth = aiohttp.BasicAuth(
            settings.twilio_account_sid, settings.twilio_auth_token
        )

        timeout = aiohttp.ClientTimeout(total=AudioConstants.TIMEOUT_SEC)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(media_url, auth=auth) as resp:
                if resp.status != 200:
                    logger.error(f"Failed to download audio: HTTP {resp.status}")
                    return None

                response_content_type = (resp.headers.get('content-type') or '').split(';', 1)[0].strip().lower()

                # Check content length (if available)
                content_length = resp.headers.get('content-length')
                max_size_bytes = AudioConstants.MAX_FILE_SIZE_MB * 1024 * 1024
                if content_length and int(content_length) > max_size_bytes:
                    logger.error(f"Audio file too large: {content_length} bytes")
                    return None

                # Download to memory with size enforcement
                audio_buffer = BytesIO()
                bytes_written = 0
                first_chunk = b""

                async for chunk in resp.content.iter_chunked(4096):
                    if not first_chunk:
                        first_chunk = chunk[:16]
                    bytes_written += len(chunk)
                    if bytes_written > max_size_bytes:
                        logger.error(f"Audio file exceeded max size during download: {bytes_written} bytes")
                        return None
                    audio_buffer.write(chunk)

                logger.info(
                    f"Downloaded audio to memory: content_type={response_content_type!r} "
                    f"size={bytes_written} first_bytes={first_chunk!r}"
                )

                if bytes_written == 0:
                    logger.error("Downloaded audio file is empty")
                    return None

                # Twilio media auth failures/errors come back as JSON/HTML
                # instead of audio bytes - catch that before handing a bogus
                # buffer to the transcription API.
                if first_chunk.lstrip()[:1] in (b"<", b"{"):
                    logger.error(
                        f"Downloaded content does not look like audio (content_type={response_content_type!r})"
                    )
                    return None

                # Reset buffer position to beginning for reading
                audio_buffer.seek(0)
                return audio_buffer

    except (aiohttp.ClientError, asyncio.TimeoutError) as exc:
        logger.error(f"Network error downloading audio: {exc}")
        return None
    except Exception as exc:
        logger.error(f"Unexpected error downloading audio: {exc}")
        return None


async def transcribe_audio_from_memory(audio_data: BytesIO, filename: str = "audio.ogg") -> Optional[tuple[str, str]]:
    """Call OpenAI's gpt-transcribe API with in-memory audio data, with retries.

    gpt-transcribe is cheaper and more accurate than whisper-1 for file
    transcription, and still reports detected language(s) in the same call
    (no extra API cost), letting callers skip translation for English audio.
    Returns (transcript, language_code) or None on failure. language_code is
    "" when the model couldn't make a reliable language prediction.
    """
    from openai import BadRequestError

    max_retries = 3
    retry_delay = 1  # seconds

    for attempt in range(max_retries):
        try:
            client = get_openai_client()

            # Reset buffer position before each attempt
            audio_data.seek(0)

            # OpenAI API needs a filename hint for format detection
            audio_data.name = filename

            result = await client.audio.transcriptions.create(
                model="gpt-transcribe",
                file=audio_data,
                response_format="json",
                temperature=0,
            )

            text = (result.text or "").strip()
            if text:
                # gpt-transcribe reports detected languages as e.g. [{"code": "fr"}],
                # not the verbose_json-only "language" field whisper-1 used.
                detected_languages = getattr(result, "languages", None) or []
                language = ""
                for entry in detected_languages:
                    code = entry.get("code") if isinstance(entry, dict) else getattr(entry, "code", None)
                    if code:
                        language = code.strip().lower()
                        break
                return text, language

            logger.warning(f"Transcription attempt {attempt + 1} returned empty result")

        except BadRequestError as exc:
            # A 400 means the file itself was rejected (bad format,
            # corrupted download, etc.) - retrying with the same bytes
            # will never succeed, so fail fast instead of burning the
            # whole retry budget.
            logger.error(f"Permanent transcription error (file rejected by API): {exc}")
            return None

        except Exception as exc:
            logger.error(f"Transcription attempt {attempt + 1} failed: {exc}")

            if attempt < max_retries - 1:
                wait_time = retry_delay * (2 ** attempt)  # Exponential backoff
                logger.info(f"Retrying in {wait_time}s...")
                await asyncio.sleep(wait_time)
            else:
                logger.error(f"All {max_retries} transcription attempts failed")
                return None

    return None


async def translate_audio_to_english(audio_data: BytesIO, filename: str = "audio.ogg") -> Optional[str]:
    """Call OpenAI's Whisper translation endpoint to get an English translation, with retries."""
    from openai import BadRequestError

    max_retries = 3
    retry_delay = 1  # seconds

    for attempt in range(max_retries):
        try:
            client = get_openai_client()

            # Reset buffer position before each attempt
            audio_data.seek(0)

            # OpenAI API needs a filename hint for format detection
            audio_data.name = filename

            result = await client.audio.translations.create(
                model="whisper-1",
                file=audio_data,
                response_format="text",
                temperature=0,
            )

            if result and result.strip():
                return result.strip()

            logger.warning(f"Translation attempt {attempt + 1} returned empty result")

        except BadRequestError as exc:
            # A 400 means the file itself was rejected - retrying with the
            # same bytes will never succeed.
            logger.error(f"Permanent translation error (file rejected by API): {exc}")
            return None

        except Exception as exc:
            logger.error(f"Translation attempt {attempt + 1} failed: {exc}")

            if attempt < max_retries - 1:
                wait_time = retry_delay * (2 ** attempt)  # Exponential backoff
                logger.info(f"Retrying in {wait_time}s...")
                await asyncio.sleep(wait_time)
            else:
                logger.error(f"All {max_retries} translation attempts failed")
                return None

    return None


async def process_voice_message(media_url: str, content_type: Optional[str] = None) -> Optional[str]:
    """Process voice message from media URL to text (stateless, no disk I/O).

    Transcribes with gpt-transcribe (cheaper and more accurate than
    whisper-1). Non-English audio is then translated to English via
    whisper-1's translations endpoint, since gpt-transcribe has no
    translation support, and both the original transcript and the
    translation are returned together. Only audio confidently detected as
    English skips the translation call and returns the transcript alone,
    since translating it would just echo the transcript back, wasting an
    API call.
    """
    normalized_content_type = (content_type or "").split(";", 1)[0].strip().lower()
    extension = AudioConstants.CONTENT_TYPE_EXTENSIONS.get(
        normalized_content_type, AudioConstants.DEFAULT_AUDIO_EXTENSION
    )
    if normalized_content_type and normalized_content_type not in AudioConstants.CONTENT_TYPE_EXTENSIONS:
        logger.warning(
            f"Unrecognized audio content type {normalized_content_type!r}, "
            f"defaulting to {extension} extension"
        )
    filename = f"voice_{uuid.uuid4().hex[:8]}{extension}"

    # Download audio to memory
    audio_data = await download_audio_to_memory(media_url)
    if not audio_data:
        return None

    # Transcribe from memory
    transcription = await transcribe_audio_from_memory(audio_data, filename)

    # Only reject if completely empty
    if not transcription:
        return None

    transcript, language = transcription
    logger.info(f"Transcribed ({language or 'unknown'}): {transcript[:100]}...")

    if language == "en":
        return transcript

    translation = await translate_audio_to_english(audio_data, filename)
    if not translation:
        return transcript

    return f"{transcript}\n\n{translation}"