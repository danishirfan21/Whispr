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
                
                # Check content length (if available)
                content_length = resp.headers.get('content-length')
                max_size_bytes = AudioConstants.MAX_FILE_SIZE_MB * 1024 * 1024
                if content_length and int(content_length) > max_size_bytes:
                    logger.error(f"Audio file too large: {content_length} bytes")
                    return None
                
                # Download to memory with size enforcement
                audio_buffer = BytesIO()
                bytes_written = 0
                
                async for chunk in resp.content.iter_chunked(4096):
                    bytes_written += len(chunk)
                    if bytes_written > max_size_bytes:
                        logger.error(f"Audio file exceeded max size during download: {bytes_written} bytes")
                        return None
                    audio_buffer.write(chunk)
                
                # Reset buffer position to beginning for reading
                audio_buffer.seek(0)
                logger.info(f"Downloaded audio to memory: {bytes_written} bytes")
                return audio_buffer

    except (aiohttp.ClientError, asyncio.TimeoutError) as exc:
        logger.error(f"Network error downloading audio: {exc}")
        return None
    except Exception as exc:
        logger.error(f"Unexpected error downloading audio: {exc}")
        return None


async def transcribe_audio_from_memory(audio_data: BytesIO, filename: str = "audio.ogg") -> Optional[str]:
    """Call OpenAI Whisper API with in-memory audio data."""
    try:
        client = get_openai_client()
        
        # OpenAI API needs a filename hint for format detection
        audio_data.name = filename
        
        result = await client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_data,
            response_format="text",
            temperature=0,
        )
        return result.strip() if result else None

    except Exception as exc:
        logger.error(f"Error transcribing audio: {exc}")
        return None


async def process_voice_message(media_url: str) -> Optional[str]:
    """Process voice message from media URL to transcript (stateless, no disk I/O)."""
    filename = f"voice_{uuid.uuid4().hex[:8]}.ogg"

    # Download audio to memory
    audio_data = await download_audio_to_memory(media_url)
    if not audio_data:
        return None

    # Transcribe from memory
    transcript = await transcribe_audio_from_memory(audio_data, filename)
    
    # Only reject if completely empty
    if not transcript or not transcript.strip():
        return None

    logger.info(f"Transcribed: {transcript[:100]}...")
    return transcript