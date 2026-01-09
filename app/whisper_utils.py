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
                
                # Check content length
                content_length = resp.headers.get('content-length')
                max_size_bytes = AudioConstants.MAX_FILE_SIZE_MB * 1024 * 1024
                if content_length and int(content_length) > max_size_bytes:
                    logger.error(f"Audio file too large: {content_length} bytes")
                    return None
                
                with open(file_path, "wb") as f:
                    async for chunk in resp.content.iter_chunked(4096):
                        f.write(chunk)
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
    """Call OpenAI Whisper and return transcript."""
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


async def process_voice_message(media_url: str) -> Optional[str]:
    """Process voice message from media URL to transcript."""
    filename = f"voice_{uuid.uuid4().hex[:8]}.ogg"

    # Download audio
    file_path = await download_audio(media_url, filename)
    if not file_path:
        return None

    # Estimate duration before transcription
    duration: float = estimate_duration(file_path)

    # Transcribe (will delete file in finally block)
    transcript = await transcribe_audio(file_path)
    if not transcript:
        return None

    # Quality checks
    word_count: int = len(transcript.split())
    words_per_sec: float = word_count / duration if duration > 0 else 0

    if duration < AudioConstants.MIN_DURATION_SEC or words_per_sec > AudioConstants.WORDS_PER_SEC_LIMIT:
        logger.info(f"Rejected transcript (duration: {duration:.1f}s, wps: {words_per_sec:.1f})")
        return None

    logger.info(f"Accepted transcript ({duration:.1f}s, {word_count} words): {transcript}")
    return transcript