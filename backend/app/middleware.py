"""
Request context middleware for correlation IDs and request tracking.
"""
import uuid
import time
from contextvars import ContextVar
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

# Context variable for request ID (accessible anywhere in async context)
_request_id_ctx: ContextVar[str | None] = ContextVar("request_id", default=None)


def get_request_id() -> str | None:
    """Get current request ID from context."""
    return _request_id_ctx.get()


class RequestContextMiddleware(BaseHTTPMiddleware):
    """
    Middleware that assigns a unique request ID to each request.

    - Generates UUID for each request (or uses incoming X-Request-ID header)
    - Stores in request.state.request_id
    - Sets context variable for access anywhere in async context
    - Adds X-Request-ID response header
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        # Generate or extract request ID (support distributed tracing)
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())

        # Store in request state (for handlers)
        request.state.request_id = request_id

        # Store in context var (for logging anywhere)
        token = _request_id_ctx.set(request_id)

        # Record timing
        request.state.start_time = time.time()

        try:
            response = await call_next(request)

            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id

            return response
        finally:
            # Reset context var
            _request_id_ctx.reset(token)
