"""Unit tests for Pydantic models."""

import pytest
from decimal import Decimal
from pydantic import ValidationError

from payment_service.models.payment import (
    CardData, PaymentRequest, PaymentResponse, RefundRequest,
    PaymentMethod, PaymentStatus, RefundStatus
)


class TestCardData:
    """Test CardData model."""
    
    def test_valid_card_data(self):
        """Test valid card data creation."""
        card = CardData(
            card_number="4111111111111111",
            expiry_month=12,
            expiry_year=2025,
            cvv="123",
            cardholder_name="John Doe",
        )
        assert card.card_number == "4111111111111111"
        assert card.expiry_month == 12
        assert card.expiry_year == 2025
        assert card.cvv == "123"
        assert card.cardholder_name == "John Doe"
    
    def test_card_number_validation(self):
        """Test card number validation."""
        # Valid card number with spaces and dashes
        card = CardData(
            card_number="4111-1111-1111-1111",
            expiry_month=12,
            expiry_year=2025,
            cvv="123",
            cardholder_name="John Doe",
        )
        assert card.card_number == "4111111111111111"
        
        # Invalid card number (too short)
        with pytest.raises(ValidationError):
            CardData(
                card_number="411111",
                expiry_month=12,
                expiry_year=2025,
                cvv="123",
                cardholder_name="John Doe",
            )
    
    def test_expiry_month_validation(self):
        """Test expiry month validation."""
        # Invalid month (too high)
        with pytest.raises(ValidationError):
            CardData(
                card_number="4111111111111111",
                expiry_month=13,
                expiry_year=2025,
                cvv="123",
                cardholder_name="John Doe",
            )
        
        # Invalid month (too low)
        with pytest.raises(ValidationError):
            CardData(
                card_number="4111111111111111",
                expiry_month=0,
                expiry_year=2025,
                cvv="123",
                cardholder_name="John Doe",
            )
    
    def test_expiry_year_validation(self):
        """Test expiry year validation."""
        # Invalid year (too low)
        with pytest.raises(ValidationError):
            CardData(
                card_number="4111111111111111",
                expiry_month=12,
                expiry_year=2020,
                cvv="123",
                cardholder_name="John Doe",
            )


class TestPaymentRequest:
    """Test PaymentRequest model."""
    
    def test_valid_payment_request(self, sample_card_data):
        """Test valid payment request creation."""
        request = PaymentRequest(
            merchant_id="merchant_123",
            amount=Decimal("99.99"),
            currency="USD",
            payment_method=PaymentMethod.CREDIT_CARD,
            card_data=sample_card_data,
            description="Test payment",
            metadata={"test": True},
        )
        assert request.merchant_id == "merchant_123"
        assert request.amount == Decimal("99.99")
        assert request.currency == "USD"
        assert request.payment_method == PaymentMethod.CREDIT_CARD
    
    def test_currency_normalization(self, sample_card_data):
        """Test currency code normalization."""
        request = PaymentRequest(
            merchant_id="merchant_123",
            amount=Decimal("99.99"),
            currency="usd",
            payment_method=PaymentMethod.CREDIT_CARD,
            card_data=sample_card_data,
        )
        assert request.currency == "USD"
    
    def test_amount_validation(self, sample_card_data):
        """Test amount validation."""
        # Negative amount
        with pytest.raises(ValidationError):
            PaymentRequest(
                merchant_id="merchant_123",
                amount=Decimal("-10.00"),
                currency="USD",
                payment_method=PaymentMethod.CREDIT_CARD,
                card_data=sample_card_data,
            )
        
        # Zero amount
        with pytest.raises(ValidationError):
            PaymentRequest(
                merchant_id="merchant_123",
                amount=Decimal("0.00"),
                currency="USD",
                payment_method=PaymentMethod.CREDIT_CARD,
                card_data=sample_card_data,
            )
        
        # Too many decimal places
        with pytest.raises(ValidationError):
            PaymentRequest(
                merchant_id="merchant_123",
                amount=Decimal("10.999"),
                currency="USD",
                payment_method=PaymentMethod.CREDIT_CARD,
                card_data=sample_card_data,
            )
    
    def test_optional_fields(self):
        """Test optional fields."""
        request = PaymentRequest(
            merchant_id="merchant_123",
            amount=Decimal("99.99"),
            payment_method=PaymentMethod.BANK_TRANSFER,
        )
        assert request.currency == "USD"  # Default value
        assert request.card_data is None
        assert request.description is None
        assert request.metadata == {}


class TestRefundRequest:
    """Test RefundRequest model."""
    
    def test_valid_refund_request(self):
        """Test valid refund request creation."""
        request = RefundRequest(
            amount=Decimal("50.00"),
            reason="Customer request",
            metadata={"test": True},
        )
        assert request.amount == Decimal("50.00")
        assert request.reason == "Customer request"
        assert request.metadata == {"test": True}
    
    def test_optional_amount(self):
        """Test optional amount (full refund)."""
        request = RefundRequest(
            reason="Customer request",
        )
        assert request.amount is None
        assert request.reason == "Customer request"
    
    def test_amount_validation(self):
        """Test refund amount validation."""
        # Negative amount
        with pytest.raises(ValidationError):
            RefundRequest(amount=Decimal("-10.00"))
        
        # Zero amount
        with pytest.raises(ValidationError):
            RefundRequest(amount=Decimal("0.00"))
        
        # Too many decimal places
        with pytest.raises(ValidationError):
            RefundRequest(amount=Decimal("10.999"))


class TestPaymentResponse:
    """Test PaymentResponse model."""
    
    def test_payment_response_creation(self):
        """Test payment response creation."""
        from datetime import datetime
        
        response = PaymentResponse(
            transaction_id="txn_123456",
            status=PaymentStatus.CAPTURED,
            amount=Decimal("99.99"),
            currency="USD",
            payment_method=PaymentMethod.CREDIT_CARD,
            card_last_four="1111",
            authorization_id="auth_123456",
            capture_id="cap_123456",
            description="Test payment",
            metadata={"test": True},
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        assert response.transaction_id == "txn_123456"
        assert response.status == PaymentStatus.CAPTURED
        assert response.amount == Decimal("99.99")
        assert response.card_last_four == "1111"


class TestEnums:
    """Test enum classes."""
    
    def test_payment_status_enum(self):
        """Test PaymentStatus enum."""
        assert PaymentStatus.PENDING.value == "pending"
        assert PaymentStatus.AUTHORIZED.value == "authorized"
        assert PaymentStatus.CAPTURED.value == "captured"
        assert PaymentStatus.FAILED.value == "failed"
        assert PaymentStatus.CANCELLED.value == "cancelled"
        assert PaymentStatus.EXPIRED.value == "expired"
    
    def test_payment_method_enum(self):
        """Test PaymentMethod enum."""
        assert PaymentMethod.CREDIT_CARD.value == "credit_card"
        assert PaymentMethod.DEBIT_CARD.value == "debit_card"
        assert PaymentMethod.BANK_TRANSFER.value == "bank_transfer"
        assert PaymentMethod.DIGITAL_WALLET.value == "digital_wallet"
    
    def test_refund_status_enum(self):
        """Test RefundStatus enum."""
        assert RefundStatus.PENDING.value == "pending"
        assert RefundStatus.PROCESSING.value == "processing"
        assert RefundStatus.COMPLETED.value == "completed"
        assert RefundStatus.FAILED.value == "failed"
        assert RefundStatus.CANCELLED.value == "cancelled"