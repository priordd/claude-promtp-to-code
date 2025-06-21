"""Enhanced Datadog integration for comprehensive monitoring."""

from typing import Dict, Any, Optional
import structlog

from payment_service.config import settings


class DatadogIntegration:
    """Enhanced Datadog integration for monitoring."""

    def __init__(self):
        self.logger = structlog.get_logger(__name__)
        self.enabled = settings.dd_trace_enabled and settings.dd_api_key

        if self.enabled:
            self._setup_datadog()

    def _setup_datadog(self) -> None:
        """Setup Datadog tracing and monitoring."""
        try:
            import ddtrace

            # Use modern ddtrace.auto instead of deprecated patch_all
            import ddtrace.auto  # This replaces patch_all()

            # Configure Datadog
            ddtrace.config.service = settings.dd_service
            ddtrace.config.env = settings.dd_env
            ddtrace.config.version = settings.dd_version

            # Configure specific integrations
            ddtrace.config.fastapi["service_name"] = settings.dd_service

            # Enable profiling
            self._setup_profiling()

            self.logger.info("Datadog integration configured successfully")

        except ImportError:
            self.logger.warning("Datadog library not available")
            self.enabled = False
        except Exception as e:
            self.logger.error("Failed to configure Datadog", error=str(e))
            self.enabled = False

    def _setup_profiling(self) -> None:
        """Setup Datadog continuous profiling."""
        if not settings.dd_profiling_enabled:
            self.logger.info("Datadog profiling disabled by configuration")
            return
            
        try:
            import ddtrace.profiling.auto
            
            self.logger.info(
                "Datadog profiling enabled",
                service=settings.dd_service,
                env=settings.dd_env,
                version=settings.dd_version
            )
            
        except ImportError:
            self.logger.warning("Datadog profiling not available - install ddtrace with profiling support")
        except Exception as e:
            self.logger.warning("Failed to enable Datadog profiling", error=str(e))

    def create_span(
        self, operation_name: str, service: Optional[str] = None, resource: Optional[str] = None
    ):
        """Create a Datadog span."""
        if not self.enabled:
            from contextlib import nullcontext

            return nullcontext()

        try:
            import ddtrace

            return ddtrace.tracer.trace(
                name=operation_name,
                service=service or settings.dd_service,
                resource=resource,
            )
        except ImportError:
            from contextlib import nullcontext

            return nullcontext()

    def set_span_tag(self, key: str, value: Any) -> None:
        """Set tag on current span."""
        if not self.enabled:
            return

        try:
            import ddtrace

            span = ddtrace.tracer.current_span()
            if span:
                span.set_tag(key, value)
        except ImportError:
            pass

    def set_span_error(self, error: Exception) -> None:
        """Set error on current span."""
        if not self.enabled:
            return

        try:
            import ddtrace

            span = ddtrace.tracer.current_span()
            if span:
                span.set_error(error)
        except ImportError:
            pass

    def increment_counter(
        self, metric_name: str, value: int = 1, tags: Optional[Dict[str, str]] = None
    ) -> None:
        """Increment a counter metric."""
        if not self.enabled:
            return

        try:
            from datadog import statsd

            tags_list = [f"{k}:{v}" for k, v in (tags or {}).items()]
            statsd.increment(metric_name, value=value, tags=tags_list)
        except ImportError:
            self.logger.debug("Datadog statsd not available for metrics")

    def histogram(
        self, metric_name: str, value: float, tags: Optional[Dict[str, str]] = None
    ) -> None:
        """Record histogram metric."""
        if not self.enabled:
            return

        try:
            from datadog import statsd

            tags_list = [f"{k}:{v}" for k, v in (tags or {}).items()]
            statsd.histogram(metric_name, value=value, tags=tags_list)
        except ImportError:
            self.logger.debug("Datadog statsd not available for metrics")

    def gauge(self, metric_name: str, value: float, tags: Optional[Dict[str, str]] = None) -> None:
        """Record gauge metric."""
        if not self.enabled:
            return

        try:
            from datadog import statsd

            tags_list = [f"{k}:{v}" for k, v in (tags or {}).items()]
            statsd.gauge(metric_name, value=value, tags=tags_list)
        except ImportError:
            self.logger.debug("Datadog statsd not available for metrics")

    def timing(self, metric_name: str, value: float, tags: Optional[Dict[str, str]] = None) -> None:
        """Record timing metric."""
        if not self.enabled:
            return

        try:
            from datadog import statsd

            tags_list = [f"{k}:{v}" for k, v in (tags or {}).items()]
            statsd.timing(metric_name, value=value, tags=tags_list)
        except ImportError:
            self.logger.debug("Datadog statsd not available for metrics")

    def log_event(
        self, title: str, text: str, alert_type: str = "info", tags: Optional[Dict[str, str]] = None
    ) -> None:
        """Log an event to Datadog."""
        if not self.enabled:
            return

        try:
            from datadog import api

            tags_list = [f"{k}:{v}" for k, v in (tags or {}).items()]
            api.Event.create(
                title=title,
                text=text,
                alert_type=alert_type,
                tags=tags_list,
            )
        except ImportError:
            self.logger.debug("Datadog API not available for events")

    def create_custom_metrics(self) -> None:
        """Create custom business metrics."""
        if not self.enabled:
            return

        # Payment processing metrics
        self.increment_counter("payment.service.started", tags={"service": settings.dd_service})

        # Database connection metrics
        self.gauge(
            "payment.database.pool.size",
            settings.database_pool_size,
            tags={"service": settings.dd_service},
        )

        # Cache metrics
        self.gauge(
            "payment.cache.max_size", settings.cache_max_size, tags={"service": settings.dd_service}
        )

    def record_payment_metrics(
        self, status: str, amount: float, currency: str, merchant_id: str
    ) -> None:
        """Record payment-specific metrics."""
        if not self.enabled:
            return

        tags = {
            "status": status,
            "currency": currency,
            "merchant_id": merchant_id,
            "service": settings.dd_service,
        }

        self.increment_counter("payment.processed", tags=tags)
        self.histogram("payment.amount", amount, tags=tags)

    def record_refund_metrics(self, status: str, amount: float, currency: str) -> None:
        """Record refund-specific metrics."""
        if not self.enabled:
            return

        tags = {
            "status": status,
            "currency": currency,
            "service": settings.dd_service,
        }

        self.increment_counter("refund.processed", tags=tags)
        self.histogram("refund.amount", amount, tags=tags)

    def record_api_metrics(
        self, endpoint: str, method: str, status_code: int, duration: float
    ) -> None:
        """Record API endpoint metrics."""
        if not self.enabled:
            return

        tags = {
            "endpoint": endpoint,
            "method": method,
            "status_code": str(status_code),
            "service": settings.dd_service,
        }

        self.increment_counter("api.requests", tags=tags)
        self.timing("api.duration", duration, tags=tags)

    def record_database_metrics(
        self, operation: str, table: str, duration: float, success: bool
    ) -> None:
        """Record database operation metrics."""
        if not self.enabled:
            return

        tags = {
            "operation": operation,
            "table": table,
            "success": str(success),
            "service": settings.dd_service,
        }

        self.increment_counter("database.operations", tags=tags)
        self.timing("database.duration", duration, tags=tags)


# Global Datadog integration instance
datadog_integration = DatadogIntegration()
