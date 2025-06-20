"""Core payment processing service with business logic."""

import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, Optional

import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

from payment_service.config import settings
from payment_service.database.connection import database_manager, serialize_json
from payment_service.models.payment import (
    PaymentRequest,
    PaymentResponse,
    PaymentStatusResponse,
    RefundRequest,
    RefundResponse,
    PaymentStatus,
    RefundStatus,
)
from payment_service.services.banking_service import BankingService
from payment_service.services.event_service import EventService
from payment_service.services.encryption_service import EncryptionService
from payment_service.services.cache_service import CacheService
from payment_service.utils.monitoring import create_span, increment_counter


class PaymentService:
    """Core payment processing service."""

    def __init__(self):
        self.logger = structlog.get_logger(__name__)
        self.banking_service = BankingService()
        self.event_service = EventService()
        self.encryption_service = EncryptionService()
        self.cache_service = CacheService()

    async def process_payment(
        self, payment_request: PaymentRequest, correlation_id: str
    ) -> PaymentResponse:
        """Process a payment request with full workflow."""
        with create_span("payment.process", resource="process_payment"):
            transaction_id = f"txn_{uuid.uuid4().hex[:16]}"

            self.logger.info(
                "Processing payment",
                transaction_id=transaction_id,
                merchant_id=payment_request.merchant_id,
                amount=str(payment_request.amount),
                correlation_id=correlation_id,
            )

            try:
                # Validate merchant
                await self._validate_merchant(payment_request.merchant_id)

                # Encrypt card data
                encrypted_card_data = None
                card_last_four = None
                if payment_request.card_data:
                    encrypted_card_data = self.encryption_service.encrypt_card_data(
                        payment_request.card_data
                    )
                    card_last_four = payment_request.card_data.card_number[-4:]

                # Create transaction record
                transaction_record = await self._create_transaction(
                    transaction_id=transaction_id,
                    payment_request=payment_request,
                    encrypted_card_data=encrypted_card_data,
                    card_last_four=card_last_four,
                    correlation_id=correlation_id,
                )

                # Authorize payment
                authorization_result = await self._authorize_payment(
                    transaction_id=transaction_id,
                    payment_request=payment_request,
                    correlation_id=correlation_id,
                )

                # Update transaction with authorization
                await self._update_transaction_authorization(
                    transaction_id=transaction_id,
                    authorization_result=authorization_result,
                    correlation_id=correlation_id,
                )

                # Capture payment if authorized
                if authorization_result.get("status") == "approved":
                    capture_result = await self._capture_payment(
                        transaction_id=transaction_id,
                        authorization_id=authorization_result.get("authorization_id"),
                        correlation_id=correlation_id,
                    )

                    # Update transaction with capture
                    await self._update_transaction_capture(
                        transaction_id=transaction_id,
                        capture_result=capture_result,
                        correlation_id=correlation_id,
                    )

                    final_status = PaymentStatus.CAPTURED
                else:
                    final_status = PaymentStatus.FAILED

                # Update final status
                await self._update_transaction_status(transaction_id, final_status, correlation_id)

                # Publish event
                await self._publish_payment_event(transaction_id, final_status, correlation_id)

                # Create audit log
                await self._create_audit_log(
                    transaction_id=transaction_id,
                    event_type="payment_created",
                    event_data={
                        "merchant_id": payment_request.merchant_id,
                        "amount": str(payment_request.amount),
                        "status": final_status.value,
                    },
                    correlation_id=correlation_id,
                )

                # Build response
                response = PaymentResponse(
                    transaction_id=transaction_id,
                    status=final_status,
                    amount=payment_request.amount,
                    currency=payment_request.currency,
                    payment_method=payment_request.payment_method,
                    card_last_four=card_last_four,
                    authorization_id=authorization_result.get("authorization_id"),
                    capture_id=(
                        capture_result.get("capture_id")
                        if final_status == PaymentStatus.CAPTURED
                        else None
                    ),
                    description=payment_request.description,
                    metadata=payment_request.metadata,
                    created_at=transaction_record["created_at"],
                    updated_at=datetime.utcnow(),
                )

                increment_counter("payment.processed", tags={"status": final_status.value})

                self.logger.info(
                    "Payment processed successfully",
                    transaction_id=transaction_id,
                    status=final_status.value,
                    correlation_id=correlation_id,
                )

                return response

            except Exception as e:
                self.logger.error(
                    "Payment processing failed",
                    transaction_id=transaction_id,
                    error=str(e),
                    correlation_id=correlation_id,
                )

                # Update transaction to failed
                await self._update_transaction_status(
                    transaction_id, PaymentStatus.FAILED, correlation_id
                )

                increment_counter("payment.failed", tags={"error": type(e).__name__})
                raise

    async def get_payment_status(
        self, transaction_id: str, correlation_id: str
    ) -> PaymentStatusResponse:
        """Get payment status by transaction ID."""
        with create_span("payment.status", resource="get_payment_status"):
            # Check cache first
            cached_status = await self.cache_service.get(f"payment_status:{transaction_id}")
            if cached_status:
                return PaymentStatusResponse.parse_obj(cached_status)

            # Query database
            query = """
                SELECT transaction_id, status, amount, currency, payment_method, card_last_four,
                       authorization_id, capture_id, description, metadata, created_at, updated_at, expires_at
                FROM transactions
                WHERE transaction_id = %s
            """

            result = await database_manager.execute_query(query, (transaction_id,), fetch_one=True)

            if not result:
                raise ValueError(f"Transaction {transaction_id} not found")

            response = PaymentStatusResponse(
                transaction_id=result["transaction_id"],
                status=PaymentStatus(result["status"]),
                amount=result["amount"],
                currency=result["currency"],
                payment_method=result["payment_method"],
                card_last_four=result["card_last_four"],
                authorization_id=result["authorization_id"],
                capture_id=result["capture_id"],
                description=result["description"],
                metadata=result["metadata"] or {},
                created_at=result["created_at"],
                updated_at=result["updated_at"],
                expires_at=result["expires_at"],
            )

            # Cache for 5 minutes
            await self.cache_service.set(
                f"payment_status:{transaction_id}", response.dict(), ttl=300
            )

            return response

    async def process_refund(
        self, transaction_id: str, refund_request: RefundRequest, correlation_id: str
    ) -> RefundResponse:
        """Process a refund for a transaction."""
        with create_span("payment.refund", resource="process_refund"):
            refund_id = f"ref_{uuid.uuid4().hex[:16]}"

            self.logger.info(
                "Processing refund",
                transaction_id=transaction_id,
                refund_id=refund_id,
                amount=str(refund_request.amount) if refund_request.amount else "full",
                correlation_id=correlation_id,
            )

            try:
                # Get original transaction
                original_transaction = await self._get_transaction(transaction_id)
                if not original_transaction:
                    raise ValueError(f"Transaction {transaction_id} not found")

                if original_transaction["status"] != PaymentStatus.CAPTURED.value:
                    raise ValueError("Can only refund captured transactions")

                # Determine refund amount
                refund_amount = refund_request.amount or original_transaction["amount"]

                # Validate refund amount
                if refund_amount > original_transaction["amount"]:
                    raise ValueError("Refund amount cannot exceed original transaction amount")

                # Create refund record
                await self._create_refund(
                    refund_id=refund_id,
                    transaction_id=transaction_id,
                    amount=refund_amount,
                    currency=original_transaction["currency"],
                    reason=refund_request.reason,
                    metadata=refund_request.metadata,
                    correlation_id=correlation_id,
                )

                # Process refund with banking service
                refund_result = await self._process_external_refund(
                    refund_id=refund_id,
                    transaction_id=transaction_id,
                    amount=refund_amount,
                    correlation_id=correlation_id,
                )

                # Update refund status
                final_status = (
                    RefundStatus.COMPLETED
                    if refund_result.get("status") == "refunded"
                    else RefundStatus.FAILED
                )
                await self._update_refund_status(
                    refund_id=refund_id,
                    status=final_status,
                    external_refund_id=refund_result.get("refund_id"),
                    correlation_id=correlation_id,
                )

                # Publish event
                await self._publish_refund_event(refund_id, final_status, correlation_id)

                # Create audit log
                await self._create_audit_log(
                    transaction_id=transaction_id,
                    event_type="refund_created",
                    event_data={
                        "refund_id": refund_id,
                        "amount": str(refund_amount),
                        "status": final_status.value,
                    },
                    correlation_id=correlation_id,
                )

                response = RefundResponse(
                    refund_id=refund_id,
                    transaction_id=transaction_id,
                    amount=refund_amount,
                    currency=original_transaction["currency"],
                    status=final_status,
                    reason=refund_request.reason,
                    external_refund_id=refund_result.get("refund_id"),
                    metadata=refund_request.metadata,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                    processed_at=(
                        datetime.utcnow() if final_status == RefundStatus.COMPLETED else None
                    ),
                )

                increment_counter("refund.processed", tags={"status": final_status.value})

                self.logger.info(
                    "Refund processed successfully",
                    refund_id=refund_id,
                    status=final_status.value,
                    correlation_id=correlation_id,
                )

                return response

            except Exception as e:
                self.logger.error(
                    "Refund processing failed",
                    refund_id=refund_id,
                    error=str(e),
                    correlation_id=correlation_id,
                )

                # Update refund to failed
                await self._update_refund_status(
                    refund_id, RefundStatus.FAILED, None, correlation_id
                )

                increment_counter("refund.failed", tags={"error": type(e).__name__})
                raise

    async def _validate_merchant(self, merchant_id: str) -> None:
        """Validate merchant ID."""
        # In a real implementation, this would check against a merchant database
        if len(merchant_id) < 3:
            raise ValueError("Invalid merchant ID")

    async def _create_transaction(
        self,
        transaction_id: str,
        payment_request: PaymentRequest,
        encrypted_card_data: Optional[str],
        card_last_four: Optional[str],
        correlation_id: str,
    ) -> Dict[str, Any]:
        """Create a new transaction record."""
        query = """
            INSERT INTO transactions (
                transaction_id, merchant_id, amount, currency, status, payment_method,
                card_last_four, encrypted_card_data, description, metadata, expires_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING *
        """

        expires_at = datetime.utcnow() + timedelta(hours=24)  # 24-hour expiry

        result = await database_manager.execute_query(
            query,
            (
                transaction_id,
                payment_request.merchant_id,
                payment_request.amount,
                payment_request.currency,
                PaymentStatus.PENDING.value,
                payment_request.payment_method.value,
                card_last_four,
                encrypted_card_data,
                payment_request.description,
                serialize_json(payment_request.metadata),
                expires_at,
            ),
            fetch_one=True,
        )

        return result

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def _authorize_payment(
        self, transaction_id: str, payment_request: PaymentRequest, correlation_id: str
    ) -> Dict[str, Any]:
        """Authorize payment with external banking service."""
        return await self.banking_service.authorize_payment(
            transaction_id=transaction_id,
            amount=payment_request.amount,
            currency=payment_request.currency,
            card_data=payment_request.card_data,
            correlation_id=correlation_id,
        )

    async def _update_transaction_authorization(
        self, transaction_id: str, authorization_result: Dict[str, Any], correlation_id: str
    ) -> None:
        """Update transaction with authorization result."""
        query = """
            UPDATE transactions 
            SET authorization_id = %s, status = %s, updated_at = CURRENT_TIMESTAMP
            WHERE transaction_id = %s
        """

        status = (
            PaymentStatus.AUTHORIZED
            if authorization_result.get("status") == "approved"
            else PaymentStatus.FAILED
        )

        await database_manager.execute_query(
            query, (authorization_result.get("authorization_id"), status.value, transaction_id)
        )

    async def _capture_payment(
        self, transaction_id: str, authorization_id: str, correlation_id: str
    ) -> Dict[str, Any]:
        """Capture authorized payment."""
        return await self.banking_service.capture_payment(
            authorization_id=authorization_id,
            correlation_id=correlation_id,
        )

    async def _update_transaction_capture(
        self, transaction_id: str, capture_result: Dict[str, Any], correlation_id: str
    ) -> None:
        """Update transaction with capture result."""
        query = """
            UPDATE transactions 
            SET capture_id = %s, updated_at = CURRENT_TIMESTAMP
            WHERE transaction_id = %s
        """

        await database_manager.execute_query(
            query, (capture_result.get("capture_id"), transaction_id)
        )

    async def _update_transaction_status(
        self, transaction_id: str, status: PaymentStatus, correlation_id: str
    ) -> None:
        """Update transaction status."""
        query = """
            UPDATE transactions 
            SET status = %s, updated_at = CURRENT_TIMESTAMP
            WHERE transaction_id = %s
        """

        await database_manager.execute_query(query, (status.value, transaction_id))

    async def _get_transaction(self, transaction_id: str) -> Optional[Dict[str, Any]]:
        """Get transaction by ID."""
        query = "SELECT * FROM transactions WHERE transaction_id = %s"
        return await database_manager.execute_query(query, (transaction_id,), fetch_one=True)

    async def _create_refund(
        self,
        refund_id: str,
        transaction_id: str,
        amount: Decimal,
        currency: str,
        reason: Optional[str],
        metadata: Dict[str, Any],
        correlation_id: str,
    ) -> None:
        """Create refund record."""
        # Get transaction UUID
        transaction_uuid_query = "SELECT id FROM transactions WHERE transaction_id = %s"
        transaction_uuid_result = await database_manager.execute_query(
            transaction_uuid_query, (transaction_id,), fetch_one=True
        )

        query = """
            INSERT INTO refunds (
                refund_id, transaction_id, amount, currency, status, reason, metadata
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
        """

        await database_manager.execute_query(
            query,
            (
                refund_id,
                transaction_uuid_result["id"],
                amount,
                currency,
                RefundStatus.PENDING.value,
                reason,
                serialize_json(metadata),
            ),
        )

    async def _process_external_refund(
        self, refund_id: str, transaction_id: str, amount: Decimal, correlation_id: str
    ) -> Dict[str, Any]:
        """Process refund with external banking service."""
        return await self.banking_service.process_refund(
            transaction_id=transaction_id,
            amount=amount,
            correlation_id=correlation_id,
        )

    async def _update_refund_status(
        self,
        refund_id: str,
        status: RefundStatus,
        external_refund_id: Optional[str],
        correlation_id: str,
    ) -> None:
        """Update refund status."""
        query = """
            UPDATE refunds 
            SET status = %s, external_refund_id = %s, updated_at = CURRENT_TIMESTAMP,
                processed_at = CASE WHEN %s = 'completed' THEN CURRENT_TIMESTAMP ELSE processed_at END
            WHERE refund_id = %s
        """

        await database_manager.execute_query(
            query, (status.value, external_refund_id, status.value, refund_id)
        )

    async def _publish_payment_event(
        self, transaction_id: str, status: PaymentStatus, correlation_id: str
    ) -> None:
        """Publish payment event to message queue."""
        event_data = {
            "transaction_id": transaction_id,
            "status": status.value,
            "timestamp": datetime.utcnow().isoformat(),
            "correlation_id": correlation_id,
        }

        await self.event_service.publish_event(
            topic=settings.kafka_payment_topic,
            event_type="payment_status_changed",
            event_data=event_data,
        )

    async def _publish_refund_event(
        self, refund_id: str, status: RefundStatus, correlation_id: str
    ) -> None:
        """Publish refund event to message queue."""
        event_data = {
            "refund_id": refund_id,
            "status": status.value,
            "timestamp": datetime.utcnow().isoformat(),
            "correlation_id": correlation_id,
        }

        await self.event_service.publish_event(
            topic=settings.kafka_payment_topic,
            event_type="refund_status_changed",
            event_data=event_data,
        )

    async def _create_audit_log(
        self, transaction_id: str, event_type: str, event_data: Dict[str, Any], correlation_id: str
    ) -> None:
        """Create audit log entry."""
        # Get transaction UUID
        transaction_uuid_query = "SELECT id FROM transactions WHERE transaction_id = %s"
        transaction_uuid_result = await database_manager.execute_query(
            transaction_uuid_query, (transaction_id,), fetch_one=True
        )

        query = """
            INSERT INTO audit_logs (
                transaction_id, event_type, event_data, correlation_id
            ) VALUES (%s, %s, %s, %s)
        """

        await database_manager.execute_query(
            query,
            (
                transaction_uuid_result["id"] if transaction_uuid_result else None,
                event_type,
                serialize_json(event_data),
                correlation_id,
            ),
        )
