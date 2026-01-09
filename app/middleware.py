"""Simple request logging middleware."""
import time
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

logger = logging.getLogger(__name__)


class SimpleLoggingMiddleware(BaseHTTPMiddleware):
    """Basic request logging."""
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        logger.info(f"{request.method} {request.url.path} - {process_time:.2f}s - {response.status_code}")
        return response