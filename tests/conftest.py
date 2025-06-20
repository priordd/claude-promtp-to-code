"""Pytest configuration and fixtures."""

import asyncio
import pytest
from decimal import Decimal
from typing import Generator
from unittest.mock import AsyncMock, Mock

from fastapi.testclient import TestClient
from faker import Faker

from payment_service.main import app
from payment_service.models.payment import PaymentRequest, RefundRequest, CardData, PaymentMethod


fake = Faker()


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def client() -> TestClient:
    """Create a test client."""
    return TestClient(app)


@pytest.fixture
def mock_database_manager():
    """Mock database manager for testing."""
    mock_db = AsyncMock()
    mock_db.execute_query.return_value = None
    mock_db.health_check.return_value = True
    return mock_db


@pytest.fixture
def sample_card_data() -> CardData:
    """Create sample card data for testing."""
    return CardData(
        card_number="4111111111111111",
        expiry_month=12,
        expiry_year=2025,
        cvv="123",
        cardholder_name="John Doe",
    )


@pytest.fixture
def sample_payment_request(sample_card_data: CardData) -> PaymentRequest:
    """Create sample payment request for testing."""
    return PaymentRequest(
        merchant_id="merchant_123",
        amount=Decimal("99.99"),
        currency="USD",
        payment_method=PaymentMethod.CREDIT_CARD,
        card_data=sample_card_data,
        description="Test payment",
        metadata={"test": True},
    )


@pytest.fixture
def sample_refund_request() -> RefundRequest:
    """Create sample refund request for testing."""
    return RefundRequest(
        amount=Decimal("50.00"),
        reason="Customer request",
        metadata={"test_refund": True},
    )


@pytest.fixture
def valid_auth_token() -> str:
    """Create a valid authentication token for testing."""
    return "Bearer test_token_123456789"


@pytest.fixture
def invalid_auth_token() -> str:
    """Create an invalid authentication token for testing."""
    return "Bearer invalid"


@pytest.fixture
def mock_banking_service():
    """Mock banking service for testing."""
    mock_service = AsyncMock()

    # Default successful responses
    mock_service.authorize_payment.return_value = {
        "status": "approved",
        "authorization_id": "auth_123456",
        "message": "Payment authorized",
    }

    mock_service.capture_payment.return_value = {
        "status": "captured",
        "capture_id": "cap_123456",
        "message": "Payment captured",
    }

    mock_service.process_refund.return_value = {
        "status": "refunded",
        "refund_id": "ref_123456",
        "message": "Refund processed",
    }

    mock_service.health_check.return_value = True

    return mock_service


@pytest.fixture
def mock_event_service():
    """Mock event service for testing."""
    mock_service = AsyncMock()
    mock_service.publish_event.return_value = None
    mock_service.health_check.return_value = True
    return mock_service


@pytest.fixture
def mock_encryption_service():
    """Mock encryption service for testing."""
    mock_service = Mock()
    mock_service.encrypt_card_data.return_value = "encrypted_card_data_123"
    mock_service.decrypt_card_data.return_value = {
        "card_number": "4111111111111111",
        "expiry_month": 12,
        "expiry_year": 2025,
        "cvv": "123",
        "cardholder_name": "John Doe",
    }
    mock_service.get_card_last_four.return_value = "1111"
    mock_service.mask_card_number.return_value = "****1111"
    return mock_service


@pytest.fixture
def mock_cache_service():
    """Mock cache service for testing."""
    mock_service = AsyncMock()
    mock_service.get.return_value = None
    mock_service.set.return_value = None
    mock_service.delete.return_value = True
    mock_service.exists.return_value = False
    mock_service.clear.return_value = None
    mock_service.size.return_value = 0
    mock_service.stats.return_value = {
        "size": 0,
        "max_size": 1000,
        "expired_entries": 0,
        "default_ttl": 300,
    }
    return mock_service


@pytest.fixture
def sample_transaction_record() -> dict:
    """Create sample transaction record for testing."""
    return {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "transaction_id": "txn_test123456",
        "merchant_id": "merchant_123",
        "amount": Decimal("99.99"),
        "currency": "USD",
        "status": "captured",
        "payment_method": "credit_card",
        "card_last_four": "1111",
        "authorization_id": "auth_123456",
        "capture_id": "cap_123456",
        "description": "Test payment",
        "metadata": {"test": True},
        "created_at": fake.date_time(),
        "updated_at": fake.date_time(),
        "expires_at": fake.date_time(),
    }


@pytest.fixture
def sample_refund_record() -> dict:
    """Create sample refund record for testing."""
    return {
        "id": "550e8400-e29b-41d4-a716-446655440001",
        "refund_id": "ref_test123456",
        "transaction_id": "550e8400-e29b-41d4-a716-446655440000",
        "amount": Decimal("50.00"),
        "currency": "USD",
        "status": "completed",
        "reason": "Customer request",
        "external_refund_id": "ext_ref_123456",
        "metadata": {"test_refund": True},
        "created_at": fake.date_time(),
        "updated_at": fake.date_time(),
        "processed_at": fake.date_time(),
    }


@pytest.fixture(autouse=True)
def setup_test_environment(monkeypatch):
    """Setup test environment variables."""
    monkeypatch.setenv("DEBUG", "true")
    monkeypatch.setenv("DATABASE_URL", "postgresql://test:test@localhost:5432/test_db")
    monkeypatch.setenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    monkeypatch.setenv("DD_TRACE_ENABLED", "false")
    monkeypatch.setenv("METRICS_ENABLED", "false")
    # Disable OpenTelemetry configuration that conflicts with Datadog
    monkeypatch.delenv("OTEL_EXPORTER_OTLP_METRICS_TEMPORALITY_PREFERENCE", raising=False)


@pytest.fixture
def correlation_id() -> str:
    """Generate a correlation ID for testing."""
    return f"test_corr_{fake.uuid4()}"
