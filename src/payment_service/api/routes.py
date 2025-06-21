"""API routes for the payment service."""

from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Depends, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import structlog

from payment_service.config import settings
from payment_service.models.payment import (
    PaymentRequest,
    PaymentResponse,
    PaymentStatusResponse,
    RefundRequest,
    RefundResponse,
    HealthCheckResponse,
)
from payment_service.services.payment_service import PaymentService
from payment_service.services.banking_service import BankingService
from payment_service.services.event_service import EventService
from payment_service.database.connection import database_manager
from payment_service.utils.logging import get_correlation_id
from payment_service.utils.monitoring import create_span, increment_counter


# Initialize router
router = APIRouter()

# Security
security = HTTPBearer(auto_error=True)

# Services
payment_service = PaymentService()
banking_service = BankingService()
event_service = EventService()

# Logger
logger = structlog.get_logger(__name__)


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Validate authentication token."""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Validate token format and content
    if not credentials.credentials or len(credentials.credentials) < 10:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # For demo purposes, accept specific valid tokens
    valid_tokens = ["test_token_123456789", "valid_demo_token_12345", "merchant_api_token_567"]

    if credentials.credentials not in valid_tokens:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return {"user_id": "demo_user", "token": credentials.credentials}


@router.post("/api/v1/payments/process", response_model=PaymentResponse)
async def process_payment(
    payment_request: PaymentRequest,
    request: Request,
    current_user: dict = Depends(get_current_user),
) -> PaymentResponse:
    """Process a new payment."""
    correlation_id = get_correlation_id()

    with create_span("api.process_payment", resource="POST /api/v1/payments/process"):
        logger.info(
            "Processing payment request",
            merchant_id=payment_request.merchant_id,
            amount=str(payment_request.amount),
            currency=payment_request.currency,
            correlation_id=correlation_id,
        )

        try:
            result = await payment_service.process_payment(payment_request, correlation_id)
            increment_counter("api.payment.success")
            return result

        except ValueError as e:
            logger.warning(
                "Payment validation error",
                error=str(e),
                correlation_id=correlation_id,
            )
            increment_counter("api.payment.validation_error")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            )
        except Exception as e:
            logger.error(
                "Payment processing error",
                error=str(e),
                correlation_id=correlation_id,
            )
            increment_counter("api.payment.error")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Payment processing failed",
            )


@router.get("/api/v1/payments/{transaction_id}", response_model=PaymentStatusResponse)
async def get_payment_status(
    transaction_id: str,
    current_user: dict = Depends(get_current_user),
) -> PaymentStatusResponse:
    """Get payment status by transaction ID."""
    correlation_id = get_correlation_id()

    with create_span("api.get_payment_status", resource="GET /api/v1/payments/{transaction_id}"):
        logger.info(
            "Getting payment status",
            transaction_id=transaction_id,
            correlation_id=correlation_id,
        )

        try:
            result = await payment_service.get_payment_status(transaction_id, correlation_id)
            increment_counter("api.payment_status.success")
            return result

        except ValueError as e:
            logger.warning(
                "Payment not found",
                transaction_id=transaction_id,
                error=str(e),
                correlation_id=correlation_id,
            )
            increment_counter("api.payment_status.not_found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Payment {transaction_id} not found",
            )
        except Exception as e:
            logger.error(
                "Payment status lookup error",
                transaction_id=transaction_id,
                error=str(e),
                correlation_id=correlation_id,
            )
            increment_counter("api.payment_status.error")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve payment status",
            )


@router.post("/api/v1/payments/{transaction_id}/refund", response_model=RefundResponse)
async def process_refund(
    transaction_id: str,
    refund_request: RefundRequest,
    current_user: dict = Depends(get_current_user),
) -> RefundResponse:
    """Process a refund for a transaction."""
    correlation_id = get_correlation_id()

    with create_span(
        "api.process_refund", resource="POST /api/v1/payments/{transaction_id}/refund"
    ):
        logger.info(
            "Processing refund request",
            transaction_id=transaction_id,
            amount=str(refund_request.amount) if refund_request.amount else "full",
            correlation_id=correlation_id,
        )

        try:
            result = await payment_service.process_refund(
                transaction_id, refund_request, correlation_id
            )
            increment_counter("api.refund.success")
            return result

        except ValueError as e:
            logger.warning(
                "Refund validation error",
                transaction_id=transaction_id,
                error=str(e),
                correlation_id=correlation_id,
            )
            increment_counter("api.refund.validation_error")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            )
        except Exception as e:
            logger.error(
                "Refund processing error",
                transaction_id=transaction_id,
                error=str(e),
                correlation_id=correlation_id,
            )
            increment_counter("api.refund.error")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Refund processing failed",
            )


@router.get("/health", response_model=HealthCheckResponse)
async def health_check() -> HealthCheckResponse:
    """Health check endpoint."""
    with create_span("api.health_check", resource="GET /health"):
        logger.info("Health check requested")

        services = {}

        # Check database
        try:
            db_healthy = await database_manager.health_check()
            services["database"] = db_healthy
        except Exception as e:
            logger.warning("Database health check failed", error=str(e))
            services["database"] = False

        # Check banking service
        try:
            banking_healthy = await banking_service.health_check()
            services["banking_service"] = banking_healthy
        except Exception as e:
            logger.warning("Banking service health check failed", error=str(e))
            services["banking_service"] = False

        # Check event service
        try:
            event_healthy = await event_service.health_check()
            services["event_service"] = event_healthy
        except Exception as e:
            logger.warning("Event service health check failed", error=str(e))
            services["event_service"] = False

        # Overall health
        overall_healthy = all(services.values())
        status_text = "healthy" if overall_healthy else "unhealthy"

        response = HealthCheckResponse(
            status=status_text,
            timestamp=datetime.now(timezone.utc),
            version=settings.dd_version,
            services=services,
        )

        logger.info("Health check completed", status=status_text, services=services)
        increment_counter("api.health_check", tags={"status": status_text})

        return response


@router.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "Payment Processing Service",
        "version": settings.dd_version,
        "status": "running",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# Error handlers moved to main.py
