"""FastAPI application - Pure Audio-to-Text Service."""
import logging
import asyncio

from fastapi import FastAPI
from app.health import ping_openai, ping_twilio
from app.twilio_webhook import router as twilio_router
from app.middleware import SimpleLoggingMiddleware

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Whispr",
    description="WhatsApp audio transcription using OpenAI Whisper",
    version="1.0.0",
)

app.add_middleware(SimpleLoggingMiddleware)
app.include_router(twilio_router, prefix="/webhook")


@app.get("/", include_in_schema=False)
async def root():
    """Root endpoint - health check."""
    return {"status": "ok", "service": "whispr"}


@app.get("/health", tags=["internal"])
async def health() -> dict:
    """Health check endpoint."""
    openai_status, twilio_status = await asyncio.gather(
        ping_openai(), ping_twilio()
    )
    status = "ok" if openai_status == twilio_status == "ok" else "degraded"
    return {
        "status": status,
        "service": "whispr",
        "checks": {
            "openai": openai_status,
            "twilio": twilio_status
        },
    }