"""
Rate limiting configuration using slowapi.
"""
from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.requests import Request

from src.config import get_settings


def get_api_key_from_request(request: Request) -> str:
    """
    Extract API key from request for rate limiting.
    Falls back to IP address if no API key (for unauthenticated endpoints).
    """
    api_key = request.headers.get("X-API-Key")
    if api_key:
        return api_key
    return get_remote_address(request)


settings = get_settings()

# Create limiter with API key as the rate limit key
# Note: headers_enabled must be False when using FastAPI response models (not Response objects)
# We add Retry-After header manually in the exception handler
limiter = Limiter(
    key_func=get_api_key_from_request,
    default_limits=[f"{settings.rate_limit_per_minute}/minute"],
    headers_enabled=False
)
