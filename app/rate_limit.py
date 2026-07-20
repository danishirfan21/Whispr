"""Rate limiting using token bucket algorithm - Stateless-friendly."""
import time
import logging
from typing import Dict, Tuple
from app.config import settings
from app.constants import RateLimitConstants

logger = logging.getLogger(__name__)

# In-memory storage: {user_id: (tokens, last_refill_time)}
# NOTE: For Vercel/serverless, this resets on cold starts
# Consider disabling rate limiting or using external Redis (Upstash)
_rate_limits: Dict[str, Tuple[int, float]] = {}


async def check_rate_limit(user_id: str) -> bool:
    """
    Check if user is within rate limits using token bucket.
    
    NOTE: In serverless environments (Vercel), this resets on cold starts.
    Set ENABLE_RATE_LIMITING=false to disable, or use external Redis.
    
    Args:
        user_id: Unique identifier for user (phone number)
        
    Returns:
        True if request is allowed, False if rate limited
    """
    # Check if rate limiting is enabled
    if not getattr(settings, 'enable_rate_limiting', True):
        logger.debug("Rate limiting disabled")
        return True
    
    max_requests = getattr(settings, 'max_requests_per_hour', RateLimitConstants.TOKENS_PER_HOUR)
    current_time: float = time.time()
    
    # Get or initialize bucket for user
    if user_id not in _rate_limits:
        _rate_limits[user_id] = (max_requests - 1, current_time)
        return True
    
    tokens, last_refill = _rate_limits[user_id]
    
    # Refill tokens based on time elapsed
    time_elapsed: float = current_time - last_refill
    tokens_to_add: int = int(time_elapsed / RateLimitConstants.REFILL_INTERVAL_SEC)
    
    if tokens_to_add > 0:
        tokens = min(max_requests, tokens + tokens_to_add)
        last_refill = current_time
    
    # Check if request is allowed
    if tokens > 0:
        _rate_limits[user_id] = (tokens - 1, last_refill)
        return True
    else:
        logger.warning(f"Rate limit exceeded for user {user_id}")
        return False


def cleanup_old_rate_limits(hours_old: int = 48) -> int:
    """Remove old rate limit entries. Returns count of cleaned entries."""
    cutoff_time: float = time.time() - (hours_old * 3600)
    old_entries = [
        user_id for user_id, (_, last_refill) in _rate_limits.items()
        if last_refill < cutoff_time
    ]
    
    for user_id in old_entries:
        _rate_limits.pop(user_id, None)
    
    logger.info(f"Cleaned up {len(old_entries)} old rate limit entries")
    return len(old_entries)


def get_rate_limit_stats() -> dict:
    """Get rate limiting statistics."""
    return {
        "active_users": len(_rate_limits),
        "total_tokens": sum(tokens for tokens, _ in _rate_limits.values())
    }


def reset_rate_limits() -> None:
    """Reset all rate limits (useful for testing)."""
    global _rate_limits
    _rate_limits.clear()