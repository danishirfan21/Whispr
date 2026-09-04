"""Audio processing using OpenAI Whisper."""
import os
import uuid
import aiohttp
import asyncio
import logging
from pathlib import Path
from typing import Optional

from app.config import settings
from app.deps import get_openai_client
from app.constants import AudioConstants

logger = logging.getLogger(__name__)


async def download_audio(media_url: str, filename: str) -> Optional[str]:
    """Download audio file from Twilio media URL and return local path."""
    # Input validation
    if not media_url or not media_url.startswith('http'):
        logger.error("Invalid media URL")
        return None

    if not filename or '..' in filename:
        logger.error("Invalid filename for security")
        return None

    try:
        downloads_dir = Path(settings.downloads_dir)
        downloads_dir.mkdir(exist_ok=True)

        file_path = downloads_dir / filename
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

                # Enforce max size while streaming
                bytes_written = 0
                first_chunk = b""
                with open(file_path, "wb") as f:
                    async for chunk in resp.content.iter_chunked(4096):
                        if not first_chunk:
                            first_chunk = chunk[:16]
                        bytes_written += len(chunk)
                        if bytes_written > max_size_bytes:
                            logger.error(f"Audio file exceeded max size during download: {bytes_written} bytes")
                            # Clean up partial file
                            try:
                                file_path.unlink(missing_ok=True)
                            except Exception:
                                pass
                            return None
                        f.write(chunk)

                logger.info(
                    f"Downloaded audio: content_type={response_content_type!r} "
                    f"size={bytes_written} first_bytes={first_chunk!r}"
                )

                if bytes_written == 0:
                    logger.error("Downloaded audio file is empty")
                    file_path.unlink(missing_ok=True)
                    return None

                # Twilio media auth failures/errors come back as JSON/HTML
                # instead of audio bytes - catch that before handing a bogus
                # file to the transcription API.
                if first_chunk.lstrip()[:1] in (b"<", b"{"):
                    logger.error(
                        f"Downloaded content does not look like audio (content_type={response_content_type!r})"
                    )
                    file_path.unlink(missing_ok=True)
                    return None

        return str(file_path)

    except (aiohttp.ClientError, asyncio.TimeoutError) as exc:
        logger.error(f"Network error downloading audio: {exc}")
        return None
    except OSError as exc:
        logger.error(f"File system error: {exc}")
        return None
    except Exception as exc:
        logger.error(f"Unexpected error downloading audio: {exc}")
        return None


def estimate_duration(file_path: str) -> float:
    """Rough duration estimate from file size."""
    try:
        size = os.path.getsize(file_path)
        estimated = size / AudioConstants.BYTES_PER_SEC_EST
        return max(estimated, AudioConstants.MIN_FALLBACK_DURATION)
    except OSError:
        return AudioConstants.DEFAULT_FALLBACK_DURATION


async def transcribe_audio(file_path: str) -> Optional[str]:
    """Call OpenAI Whisper and return transcript.

    A 400 from the API means the file itself was rejected (bad format,
    corrupted download, etc.) - retrying with the same bytes will never
    succeed, so we fail fast instead of burning time/rate-limit budget.
    """
    from openai import BadRequestError

    try:
        client = get_openai_client()
        with open(file_path, "rb") as audio_file:
            result = await client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="text",
                temperature=0,
            )
        return result.strip() if result else None

    except BadRequestError as exc:
        logger.error(f"Permanent transcription error (file rejected by API): {exc}")
        return None
    except Exception as exc:
        logger.error(f"Error transcribing audio: {exc}")
        return None
    finally:
        # Always remove temp file
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except OSError as exc:
            logger.warning(f"Could not remove temp file {file_path}: {exc}")


async def process_voice_message(media_url: str, content_type: Optional[str] = None) -> Optional[str]:
    """Process voice message from media URL to transcript."""
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

    # Download audio
    file_path = await download_audio(media_url, filename)
    if not file_path:
        return None

    # Transcribe (will delete file in finally block)
    transcript = await transcribe_audio(file_path)
    
    # Only reject if completely empty
    if not transcript or not transcript.strip():
        return None

    logger.info(f"Transcribed: {transcript[:100]}...")
    return transcript