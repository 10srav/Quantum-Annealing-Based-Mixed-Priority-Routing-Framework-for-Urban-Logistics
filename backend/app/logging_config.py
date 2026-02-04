"""
Structured logging configuration using structlog.

Provides JSON-formatted logs for production observability.
All log entries include timestamp, log level, and are machine-parseable.
"""

import logging
import os
import sys
from typing import Any

import structlog
from structlog.typing import Processor


# Environment-based log level (default INFO for production)
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()

# Numeric log level for comparisons
_configured_level: int = logging.INFO


def is_debug_enabled() -> bool:
    """Check if DEBUG level logging is enabled."""
    return _configured_level <= logging.DEBUG


def configure_logging(log_level: str | None = None) -> None:
    """
    Configure structlog with JSON renderer for production logging.

    Sets up:
    - JSON output format (machine-parseable)
    - ISO timestamp on all entries
    - Log level included in output
    - Integration with standard library logging

    Args:
        log_level: Override log level (default: from LOG_LEVEL env var)
    """
    global _configured_level
    level = log_level or LOG_LEVEL
    numeric_level = getattr(logging, level, logging.INFO)
    _configured_level = numeric_level

    # Shared processors for both structlog and stdlib integration
    shared_processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.dev.set_exc_info,
        structlog.processors.TimeStamper(fmt="iso"),
    ]

    # Configure structlog
    structlog.configure(
        processors=shared_processors + [
            structlog.processors.JSONRenderer()
        ],
        wrapper_class=structlog.make_filtering_bound_logger(numeric_level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Configure stdlib logging to use structlog formatting
    # This ensures any stdlib loggers also output JSON
    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=shared_processors,
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            structlog.processors.JSONRenderer(),
        ],
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(numeric_level)

    # Suppress noisy third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.WARNING)


def get_logger(name: str | None = None, **initial_context: Any) -> structlog.BoundLogger:
    """
    Get a bound structlog logger.

    Args:
        name: Logger name (typically __name__ from calling module)
        **initial_context: Additional context to bind to all log entries

    Returns:
        Bound structlog logger with optional initial context

    Example:
        logger = get_logger(__name__, service="api")
        logger.info("Request received", endpoint="/health")
        # Output: {"timestamp": "...", "level": "info", "service": "api", "event": "Request received", "endpoint": "/health"}
    """
    logger = structlog.get_logger(name)
    if initial_context:
        logger = logger.bind(**initial_context)
    return logger
