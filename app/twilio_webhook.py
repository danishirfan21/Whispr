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
from app.validators import validate_phone_number, validate_message_size

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
        await _send_twilio_message(
            twilio_client,
            ErrorResponses.RATE_LIMIT,
            From
        )
        logger.info(f"[{request_id}] Rate limited user {user_id}")
        return PlainTextResponse("")
    
    # Process audio file
    try:
        logger.info(f"[{request_id}] Processing audio from {user_id}")
        
        # Transcribe audio with timeout
        try:
            with fail_after(AudioConstants.TIMEOUT_SEC):
                transcript = await process_voice_message(MediaUrl0)
        except TimeoutError:
            logger.warning(f"[{request_id}] Audio processing timeout")
            await _send_twilio_message(
                twilio_client,
                ErrorResponses.AUDIO_TIMEOUT,
                From
            )
            return PlainTextResponse("")
        
        # Handle transcription failure
        if transcript is None:
            logger.warning(f"[{request_id}] Audio transcription failed")
            await _send_twilio_message(
                twilio_client,
                ErrorResponses.AUDIO_UNCLEAR,
                From
            )
            return PlainTextResponse("")
        
        # Send transcript back
        message_text = f"📝 *Transcript:*\n\n{transcript}"
        message = await _send_twilio_message(twilio_client, message_text, From)
        
        processing_time = time.time() - start_time
        logger.info(f"[{request_id}] Sent transcript {message.sid} to {From} in {processing_time:.2f}s")
        
    except Exception as e:
        logger.error(f"[{request_id}] Error processing audio: {e}")
        await _send_twilio_message(
            twilio_client,
            ErrorResponses.PROCESSING_ERROR,
            From
        )
    
    return PlainTextResponse("")