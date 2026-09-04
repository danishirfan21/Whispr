"""Twilio webhook handler - Pure Audio-to-Text Service."""
import logging
import uuid
import time
import anyio
from anyio import fail_after
from typing import Any

from fastapi import APIRouter, Request, HTTPException, Depends, Form
from fastapi.responses import PlainTextResponse
from twilio.request_validator import RequestValidator
from twilio.rest import Client as TwilioClient

from app.config import settings
from app.deps import get_twilio_client
from app.whisper_utils import process_voice_message
from app.rate_limit import check_rate_limit
from app.utils import sanitize_phone_number
from app.constants import ErrorResponses, AudioConstants
from app.validators import validate_phone_number

logger = logging.getLogger(__name__)
router = APIRouter()


async def verify_twilio_signature(request: Request) -> bool:
    """Verify Twilio webhook signature using full form data."""
    try:
        validator = RequestValidator(settings.twilio_auth_token)
        signature = request.headers.get("X-Twilio-Signature", "")
        url = str(request.url)
        
        # Get all form fields for proper signature validation
        form = await request.form()
        form_data = {key: value for key, value in form.items()}
        
        return validator.validate(url, form_data, signature)
    except Exception as e:
        logger.error(f"Signature verification failed: {e}")
        return False


async def _send_twilio_message(client: TwilioClient, body: str, to: str) -> Any:
    """Helper to send Twilio message in thread."""
    def _send() -> Any:
        return client.messages.create(
            body=body,
            from_=settings.twilio_sender_number,
            to=to
        )
    return await anyio.to_thread.run_sync(_send)


def split_message(text: str, max_length: int = 1600) -> list[str]:
    """Split long text into chunks under max_length, preserving word boundaries."""
    if len(text) <= max_length:
        return [text]
    
    chunks = []
    while text:
        if len(text) <= max_length:
            chunks.append(text)
            break
        
        # Find last space before max_length
        split_pos = text.rfind(' ', 0, max_length)
        if split_pos == -1:  # No space found, force split
            split_pos = max_length
        
        chunks.append(text[:split_pos].strip())
        text = text[split_pos:].strip()
    
    return chunks


async def send_transcript_messages(client: TwilioClient, transcript: str, to: str, request_id: str) -> None:
    """Send transcript, splitting into multiple messages if needed."""
    from app.constants import WhatsAppConstants
    
    max_length = WhatsAppConstants.MAX_MESSAGE_LENGTH
    
    # Reserve space for prefix like "(99/99) " = 9 chars max
    prefix_reserve = 10
    chunk_max_length = max_length - prefix_reserve
    
    chunks = split_message(transcript, chunk_max_length)
    
    if len(chunks) > 1:
        logger.info(f"[{request_id}] Splitting transcript into {len(chunks)} messages")
    
    for i, chunk in enumerate(chunks, 1):
        prefix = f"({i}/{len(chunks)}) " if len(chunks) > 1 else ""
        message_body = prefix + chunk
        
        # Safety check - ensure we're under limit
        if len(message_body) > max_length:
            logger.warning(f"[{request_id}] Message part {i} still too long ({len(message_body)} chars), truncating")
            message_body = message_body[:max_length]
        
        try:
            await _send_twilio_message(client, message_body, to)
            logger.info(f"[{request_id}] Sent message part {i}/{len(chunks)} ({len(message_body)} chars)")
        except Exception as e:
            logger.error(f"[{request_id}] Failed to send message part {i}/{len(chunks)}: {e}")
            raise





@router.post("/whatsapp")
async def whatsapp_webhook(
    request: Request,
    Body: str = Form(""),
    From: str = Form(...),
    MediaUrl0: str = Form(None),
    MediaContentType0: str = Form(None),
    NumMedia: int = Form(0),
    twilio_client: TwilioClient = Depends(get_twilio_client)
) -> PlainTextResponse:
    """
    Handle incoming WhatsApp messages - Audio-to-Text Only.
    
    - Only processes audio files
    - Ignores all text messages
    - Ignores all non-audio media
    - Returns transcription via WhatsApp
    """
    
    request_id = str(uuid.uuid4())[:8]
    start_time = time.time()
    logger.info(f"[{request_id}] Webhook received from {From}")
    
    # Validate phone number
    user_id = sanitize_phone_number(From)
    if not validate_phone_number(From):
        logger.warning(f"[{request_id}] Invalid phone number: {From}")
        raise HTTPException(status_code=400, detail="Invalid phone number")
    
    # Ignore text messages
    if NumMedia == 0:
        logger.info(f"[{request_id}] Ignored text message from {user_id}")
        return PlainTextResponse("")
    
    # If multiple media files, log but only process first
    if NumMedia > 1:
        logger.info(f"[{request_id}] Multiple media files ({NumMedia}), processing only first")
    
    # Ignore non-audio media
    if not MediaContentType0 or not MediaContentType0.startswith("audio/"):
        logger.info(f"[{request_id}] Ignored non-audio media: {MediaContentType0}")
        return PlainTextResponse("")
    
    # Signature verification
    if settings.verify_twilio_signature:
        if not await verify_twilio_signature(request):
            logger.warning(f"[{request_id}] Invalid Twilio signature")
            raise HTTPException(status_code=403, detail="Invalid signature")
    
    # Check rate limits (only for audio messages)
    if not await check_rate_limit(user_id):
        logger.warning(f"[{request_id}] Rate limit exceeded for user {user_id}")
        await _send_twilio_message(
            twilio_client,
            ErrorResponses.PROCESSING_FAILED,
            From
        )
        return PlainTextResponse("")
    
    # Process audio file
    try:
        logger.info(f"[{request_id}] Processing audio from {user_id}")
        
        # Transcribe audio with timeout
        try:
            with fail_after(AudioConstants.TIMEOUT_SEC):
                transcript = await process_voice_message(MediaUrl0, MediaContentType0)
        except TimeoutError:
            logger.error(f"[{request_id}] Audio processing timeout (>{AudioConstants.TIMEOUT_SEC}s)")
            await _send_twilio_message(
                twilio_client,
                ErrorResponses.PROCESSING_FAILED,
                From
            )
            return PlainTextResponse("")

        # Handle transcription failure
        if transcript is None:
            logger.error(f"[{request_id}] Transcription failed or returned empty (content_type={MediaContentType0})")
            await _send_twilio_message(
                twilio_client,
                ErrorResponses.TRANSCRIBE_FAILED,
                From
            )
            return PlainTextResponse("")
        
        # Send transcript back (split into multiple messages if needed)
        await send_transcript_messages(twilio_client, transcript, From, request_id)
        
        processing_time = time.time() - start_time
        logger.info(f"[{request_id}] Sent transcript to {From} in {processing_time:.2f}s")
        
    except Exception as e:
        logger.error(f"[{request_id}] Unexpected error processing audio from {user_id}: {type(e).__name__}: {e}", exc_info=True)
        await _send_twilio_message(
            twilio_client,
            ErrorResponses.PROCESSING_FAILED,
            From
        )
    
    return PlainTextResponse("")