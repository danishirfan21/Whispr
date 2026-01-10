"""FastAPI application - Pure Audio-to-Text Service."""
import logging
import asyncio

from fastapi import FastAPI
from app.health import ping_openai, ping_twilio
from app.twilio_webhook import router as twilio_router
from app.rate_limit import cleanup_old_rate_limits, get_rate_limit_stats
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


@app.get("/admin/stats", tags=["admin"])
async def get_stats():
    """Get system statistics."""
    return {
        "service": "audio-to-text",
        "rate_limit_stats": get_rate_limit_stats()
    }


@app.post("/admin/cleanup", tags=["admin"])
async def cleanup_data():
    """Clean up old rate limits."""
    rate_limits_cleaned = cleanup_old_rate_limits(48)
    return {
        "rate_limits_cleaned": rate_limits_cleaned,
        "status": "completed"
    }