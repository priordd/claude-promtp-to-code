"""Payment-related Pydantic models for request/response validation."""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field, validator


class PaymentStatus(str, Enum):
    """Payment status enumeration."""

    PENDING = "pending"
    AUTHORIZED = "authorized"
    CAPTURED = "captured"
    FAILED = "failed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class PaymentMethod(str, Enum):
    """Payment method enumeration."""

    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    BANK_TRANSFER = "bank_transfer"
    DIGITAL_WALLET = "digital_wallet"


class RefundStatus(str, Enum):
    """Refund status enumeration."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class CardData(BaseModel):
    """Credit card information model."""

    card_number: str = Field(..., min_length=13, max_length=19)
    expiry_month: int = Field(..., ge=1, le=12)
    expiry_year: int = Field(..., ge=2024, le=2050)
    cvv: str = Field(..., min_length=3, max_length=4)
    cardholder_name: str = Field(..., min_length=1, max_length=100)

    @validator("card_number")
    def validate_card_number(cls, v):
        """Validate card number format."""
        # Remove spaces and dashes
        card_num = "".join(c for c in v if c.isdigit())
        if len(card_num) < 13 or len(card_num) > 19:
            raise ValueError("Invalid card number length")
        return card_num


class PaymentRequest(BaseModel):
    """Payment processing request model."""

    merchant_id: str = Field(..., min_length=1, max_length=100)
    amount: Decimal = Field(..., gt=0, decimal_places=2)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    payment_method: PaymentMethod
    card_data: Optional[CardData] = None
    description: Optional[str] = Field(None, max_length=500)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)

    @validator("currency")
    def validate_currency(cls, v):
        """Validate currency code."""
        return v.upper()

    @validator("amount")
    def validate_amount(cls, v):
        """Validate amount precision."""
        if v.as_tuple().exponent < -2:
            raise ValueError("Amount cannot have more than 2 decimal places")
        return v


class PaymentResponse(BaseModel):
    """Payment processing response model."""

    transaction_id: str
    status: PaymentStatus
    amount: Decimal
    currency: str
    payment_method: PaymentMethod
    card_last_four: Optional[str] = None
    authorization_id: Optional[str] = None
    capture_id: Optional[str] = None
    description: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime
    expires_at: Optional[datetime] = None


class PaymentStatusResponse(BaseModel):
    """Payment status lookup response model."""

    transaction_id: str
    status: PaymentStatus
    amount: Decimal
    currency: str
    payment_method: PaymentMethod
    card_last_four: Optional[str] = None
    authorization_id: Optional[str] = None
    capture_id: Optional[str] = None
    description: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime
    expires_at: Optional[datetime] = None


class RefundRequest(BaseModel):
    """Refund processing request model."""

    amount: Optional[Decimal] = Field(None, gt=0, decimal_places=2)
    reason: Optional[str] = Field(None, max_length=100)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)

    @validator("amount")
    def validate_amount(cls, v):
        """Validate refund amount precision."""
        if v and v.as_tuple().exponent < -2:
            raise ValueError("Amount cannot have more than 2 decimal places")
        return v


class RefundResponse(BaseModel):
    """Refund processing response model."""

    refund_id: str
    transaction_id: str
    amount: Decimal
    currency: str
    status: RefundStatus
    reason: Optional[str] = None
    external_refund_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime
    processed_at: Optional[datetime] = None


class HealthCheckResponse(BaseModel):
    """Health check response model."""

    status: str = "healthy"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    version: str
    services: Dict[str, bool] = Field(default_factory=dict)


class ErrorResponse(BaseModel):
    """Error response model."""

    error: str
    message: str
    correlation_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    details: Optional[Dict[str, Any]] = None
