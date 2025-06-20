"""Event publishing service for Kafka integration."""

import asyncio
import json
from typing import Any, Dict, Optional

import structlog
from kafka import KafkaProducer
from kafka.errors import KafkaError
from tenacity import retry, stop_after_attempt, wait_exponential

from payment_service.config import settings


class EventService:
    """Service for publishing events to Kafka."""

    def __init__(self):
        self.logger = structlog.get_logger(__name__)
        self.producer: Optional[KafkaProducer] = None

    def _get_producer(self) -> KafkaProducer:
        """Get or create Kafka producer."""
        if not self.producer:
            try:
                self.producer = KafkaProducer(
                    bootstrap_servers=settings.kafka_bootstrap_servers.split(","),
                    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                    key_serializer=lambda v: v.encode("utf-8") if v else None,
                    acks="all",
                    retries=settings.kafka_retry_attempts,
                    max_in_flight_requests_per_connection=1,
                    enable_idempotence=True,
                )
                self.logger.info("Kafka producer initialized")
            except Exception as e:
                self.logger.error("Failed to initialize Kafka producer", error=str(e))
                raise

        return self.producer

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def publish_event(
        self,
        topic: str,
        event_type: str,
        event_data: Dict[str, Any],
        key: Optional[str] = None,
    ) -> None:
        """Publish event to Kafka topic."""
        message = {
            "event_type": event_type,
            "event_data": event_data,
            "timestamp": event_data.get("timestamp"),
            "correlation_id": event_data.get("correlation_id"),
        }

        try:
            producer = self._get_producer()

            # Send message asynchronously
            future = producer.send(
                topic=topic,
                value=message,
                key=key or event_data.get("transaction_id", event_data.get("refund_id")),
            )

            # Wait for send to complete
            await asyncio.get_event_loop().run_in_executor(None, lambda: future.get(timeout=10))

            self.logger.info(
                "Event published successfully",
                topic=topic,
                event_type=event_type,
                correlation_id=event_data.get("correlation_id"),
            )

        except KafkaError as e:
            self.logger.error(
                "Failed to publish event to Kafka",
                topic=topic,
                event_type=event_type,
                error=str(e),
                correlation_id=event_data.get("correlation_id"),
            )
            raise
        except Exception as e:
            self.logger.error(
                "Unexpected error publishing event",
                topic=topic,
                event_type=event_type,
                error=str(e),
                correlation_id=event_data.get("correlation_id"),
            )
            raise

    def close(self) -> None:
        """Close Kafka producer."""
        if self.producer:
            try:
                self.producer.close()
                self.logger.info("Kafka producer closed")
            except Exception as e:
                self.logger.error("Error closing Kafka producer", error=str(e))

    async def health_check(self) -> bool:
        """Check Kafka connectivity."""
        try:
            producer = self._get_producer()
            # Check if we can get metadata (simple connectivity test)
            metadata = producer.list_consumer_group_offsets()
            return True
        except Exception as e:
            self.logger.warning("Kafka health check failed", error=str(e))
            return False
