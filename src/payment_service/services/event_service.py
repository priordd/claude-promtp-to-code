"""Event logging service for payment events tracking."""

import json
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import structlog

from payment_service.config import settings


class EventService:
    """Service for logging and tracking payment events."""

    def __init__(self):
        self.logger = structlog.get_logger(__name__)

    async def publish_event(
        self,
        topic: str,
        event_type: str,
        event_data: Dict[str, Any],
        key: Optional[str] = None,
    ) -> None:
        """Log event with structured logging."""
        if not settings.event_logging_enabled:
            return

        # Create structured event message
        event_message = {
            "event_type": event_type,
            "topic": topic,
            "event_data": event_data,
            "timestamp": event_data.get("timestamp", datetime.now(timezone.utc).isoformat()),
            "correlation_id": event_data.get("correlation_id"),
            "key": key or event_data.get("transaction_id", event_data.get("refund_id")),
        }

        # Log the event with appropriate level based on event type
        if "error" in event_type.lower() or "failed" in event_type.lower():
            self.logger.error(
                "Payment event logged",
                event_message=event_message,
                **{k: v for k, v in event_data.items() if k != 'event'}
            )
        elif "warning" in event_type.lower() or "declined" in event_type.lower():
            self.logger.warning(
                "Payment event logged",
                event_message=event_message,
                **{k: v for k, v in event_data.items() if k != 'event'}
            )
        else:
            self.logger.info(
                "Payment event logged",
                event_message=event_message,
                **{k: v for k, v in event_data.items() if k != 'event'}
            )

    def close(self) -> None:
        """Close event service (no-op for logging-based implementation)."""
        self.logger.info("Event service closed")

    async def health_check(self) -> bool:
        """Check event service health."""
        # Logging-based service is always healthy if configured
        return settings.event_logging_enabled

    # Convenience methods for common payment events
    async def log_payment_processed(self, transaction_id: str, amount: float, 
                                  currency: str, merchant_id: str, 
                                  correlation_id: str) -> None:
        """Log successful payment processing event."""
        await self.publish_event(
            topic="payment-events",
            event_type="payment_processed",
            event_data={
                "transaction_id": transaction_id,
                "amount": amount,
                "currency": currency,
                "merchant_id": merchant_id,
                "correlation_id": correlation_id,
                "status": "success"
            }
        )

    async def log_payment_failed(self, transaction_id: str, reason: str, 
                               merchant_id: str, correlation_id: str) -> None:
        """Log failed payment processing event."""
        await self.publish_event(
            topic="payment-events",
            event_type="payment_failed",
            event_data={
                "transaction_id": transaction_id,
                "reason": reason,
                "merchant_id": merchant_id,
                "correlation_id": correlation_id,
                "status": "failed"
            }
        )

    async def log_refund_processed(self, refund_id: str, transaction_id: str, 
                                 amount: float, currency: str, 
                                 correlation_id: str) -> None:
        """Log successful refund processing event."""
        await self.publish_event(
            topic="refund-events",
            event_type="refund_processed",
            event_data={
                "refund_id": refund_id,
                "transaction_id": transaction_id,
                "amount": amount,
                "currency": currency,
                "correlation_id": correlation_id,
                "status": "success"
            }
        )

    async def log_refund_failed(self, refund_id: str, transaction_id: str, 
                              reason: str, correlation_id: str) -> None:
        """Log failed refund processing event."""
        await self.publish_event(
            topic="refund-events",
            event_type="refund_failed",
            event_data={
                "refund_id": refund_id,
                "transaction_id": transaction_id,
                "reason": reason,
                "correlation_id": correlation_id,
                "status": "failed"
            }
        )