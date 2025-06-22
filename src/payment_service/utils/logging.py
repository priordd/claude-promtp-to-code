"""Structured logging configuration."""

import logging
import sys
from typing import Any, Dict

import structlog
from payment_service.config import settings

try:
    from ddtrace import tracer

    DDTRACE_AVAILABLE = True
except ImportError:
    DDTRACE_AVAILABLE = False


def add_trace_correlation(logger, method_name, event_dict):
    """Add Datadog trace correlation to log entries."""
    if DDTRACE_AVAILABLE:
        # Get current span
        span = tracer.current_span()
        if span:
            # Add trace and span IDs for correlation
            event_dict["dd.trace_id"] = str(span.trace_id)
            event_dict["dd.span_id"] = str(span.span_id)

            # Also add service and version for better correlation
            event_dict["dd.service"] = settings.dd_service
            event_dict["dd.version"] = settings.dd_version
            event_dict["dd.env"] = settings.dd_env

    return event_dict


@tracer.wrap()
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
        structlog.contextvars.merge_contextvars,  # Add contextvars support
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        add_trace_correlation,  # Add trace correlation
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

    # Enable contextvars for request-scoped context
    structlog.contextvars.clear_contextvars()


def get_correlation_id() -> str:
    """Generate a correlation ID for request tracking."""
    import uuid

    # If we have an active Datadog span, use its trace ID as correlation ID
    if DDTRACE_AVAILABLE:
        span = tracer.current_span()
        if span:
            return str(span.trace_id)

    # Otherwise generate a new UUID
    return str(uuid.uuid4())


def add_correlation_context(correlation_id: str) -> Dict[str, Any]:
    """Add correlation ID to logging context."""
    return {"correlation_id": correlation_id}
