"""Monitoring and observability setup."""

from typing import Optional
import structlog

from payment_service.config import settings
from payment_service.utils.datadog_integration import datadog_integration


def setup_monitoring() -> None:
    """Initialize monitoring and observability tools."""
    logger = structlog.get_logger(__name__)

    # Initialize Datadog integration
    datadog_integration.create_custom_metrics()

    logger.info(
        "Monitoring setup complete",
        service=settings.dd_service,
        env=settings.dd_env,
        version=settings.dd_version,
        datadog_enabled=datadog_integration.enabled,
    )


def create_span(name: str, service: Optional[str] = None, resource: Optional[str] = None):
    """Create a monitoring span for distributed tracing."""
    return datadog_integration.create_span(name, service, resource)


def increment_counter(metric_name: str, value: int = 1, tags: Optional[dict] = None) -> None:
    """Increment a counter metric."""
    if not settings.metrics_enabled:
        return

    # Use Datadog integration
    datadog_integration.increment_counter(metric_name, value, tags)

    # Also log for debugging
    logger = structlog.get_logger(__name__)
    logger.debug(
        "Counter increment",
        metric=metric_name,
        value=value,
        tags=tags or {},
    )
