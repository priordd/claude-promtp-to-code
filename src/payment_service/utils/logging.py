"""Structured logging configuration."""

import logging
import sys
from typing import Any, Dict

import structlog
from payment_service.config import settings


def setup_logging() -> None:
    """Configure structured logging with appropriate processors."""

    # Configure stdlib logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.INFO if not settings.debug else logging.DEBUG,
    )

    # Configure structlog
    processors = [
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    if settings.debug:
        processors.append(structlog.dev.ConsoleRenderer())
    else:
        processors.append(structlog.processors.JSONRenderer())

    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def get_correlation_id() -> str:
    """Generate a correlation ID for request tracking."""
    import uuid

    return str(uuid.uuid4())


def add_correlation_context(correlation_id: str) -> Dict[str, Any]:
    """Add correlation ID to logging context."""
    return {"correlation_id": correlation_id}
