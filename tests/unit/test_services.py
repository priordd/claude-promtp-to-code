"""Unit tests for service classes."""

import pytest
from decimal import Decimal
from unittest.mock import Mock, patch

from payment_service.services.payment_service import PaymentService
from payment_service.services.banking_service import BankingService
from payment_service.services.encryption_service import EncryptionService
from payment_service.services.cache_service import CacheService


class TestPaymentService:
    """Test PaymentService class."""

    @pytest.fixture
    def payment_service(
        self, mock_banking_service, mock_event_service, mock_encryption_service, mock_cache_service
    ):
        """Create payment service with mocked dependencies."""
        service = PaymentService()
        service.banking_service = mock_banking_service
        service.event_service = mock_event_service
        service.encryption_service = mock_encryption_service
        service.cache_service = mock_cache_service
        return service

    @pytest.mark.asyncio
    async def test_validate_merchant_valid(self, payment_service):
        """Test merchant validation with valid ID."""
        # Should not raise exception
        await payment_service._validate_merchant("merchant_123")

    @pytest.mark.asyncio
    async def test_validate_merchant_invalid(self, payment_service):
        """Test merchant validation with invalid ID."""
        with pytest.raises(ValueError, match="Invalid merchant ID"):
            await payment_service._validate_merchant("ab")

    @pytest.mark.asyncio
    @patch("payment_service.services.payment_service.database_manager")
    async def test_create_transaction(
        self, mock_db, payment_service, sample_payment_request, correlation_id
    ):
        """Test transaction creation."""
        from unittest.mock import AsyncMock

        mock_db.execute_query = AsyncMock(
            return_value={
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "transaction_id": "txn_test123456",
                "created_at": "2024-01-01T00:00:00Z",
            }
        )

        result = await payment_service._create_transaction(
            transaction_id="txn_test123456",
            payment_request=sample_payment_request,
            encrypted_card_data="encrypted_data",
            card_last_four="1111",
            correlation_id=correlation_id,
        )

        assert result["transaction_id"] == "txn_test123456"
        mock_db.execute_query.assert_called_once()


class TestBankingService:
    """Test BankingService class."""

    @pytest.fixture
    def banking_service(self):
        """Create banking service instance."""
        return BankingService()

    @pytest.mark.asyncio
    @patch("payment_service.services.banking_service.httpx.AsyncClient")
    async def test_authorize_payment_success(
        self, mock_client, banking_service, sample_card_data, correlation_id
    ):
        """Test successful payment authorization."""
        # Mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "approved",
            "authorization_id": "auth_123456",
            "message": "Payment authorized",
        }

        mock_client.return_value.__aenter__.return_value.post.return_value = mock_response

        result = await banking_service.authorize_payment(
            transaction_id="txn_123456",
            amount=Decimal("99.99"),
            currency="USD",
            card_data=sample_card_data,
            correlation_id=correlation_id,
        )

        assert result["status"] == "approved"
        assert result["authorization_id"] == "auth_123456"

    @pytest.mark.asyncio
    @patch("payment_service.services.banking_service.httpx.AsyncClient")
    async def test_authorize_payment_declined(
        self, mock_client, banking_service, sample_card_data, correlation_id
    ):
        """Test declined payment authorization."""
        # Mock declined response
        mock_response = Mock()
        mock_response.status_code = 402
        mock_response.json.return_value = {
            "error": "card_declined",
            "message": "Your card was declined",
            "decline_code": "generic_decline",
        }

        mock_client.return_value.__aenter__.return_value.post.return_value = mock_response

        result = await banking_service.authorize_payment(
            transaction_id="txn_123456",
            amount=Decimal("99.99"),
            currency="USD",
            card_data=sample_card_data,
            correlation_id=correlation_id,
        )

        assert result["status"] == "declined"
        assert "declined" in result["message"]

    @pytest.mark.asyncio
    @patch("payment_service.services.banking_service.httpx.AsyncClient")
    async def test_capture_payment_success(self, mock_client, banking_service, correlation_id):
        """Test successful payment capture."""
        # Mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "captured",
            "capture_id": "cap_123456",
            "message": "Payment captured",
        }
        mock_response.raise_for_status.return_value = None

        mock_client.return_value.__aenter__.return_value.post.return_value = mock_response

        result = await banking_service.capture_payment(
            authorization_id="auth_123456",
            correlation_id=correlation_id,
        )

        assert result["status"] == "captured"
        assert result["capture_id"] == "cap_123456"

    @pytest.mark.asyncio
    async def test_health_check_success(self, banking_service):
        """Test successful health check."""
        with patch("payment_service.services.banking_service.httpx.AsyncClient") as mock_client:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response

            result = await banking_service.health_check()
            assert result is True

    @pytest.mark.asyncio
    async def test_health_check_failure(self, banking_service):
        """Test failed health check."""
        with patch("payment_service.services.banking_service.httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get.side_effect = Exception(
                "Connection error"
            )

            result = await banking_service.health_check()
            assert result is False


class TestEncryptionService:
    """Test EncryptionService class."""

    @pytest.fixture
    def encryption_service(self):
        """Create encryption service instance."""
        return EncryptionService()

    def test_encrypt_decrypt_card_data(self, encryption_service, sample_card_data):
        """Test card data encryption and decryption."""
        # Encrypt card data
        encrypted = encryption_service.encrypt_card_data(sample_card_data)
        assert isinstance(encrypted, str)
        assert len(encrypted) > 0

        # Decrypt card data
        decrypted = encryption_service.decrypt_card_data(encrypted)
        assert decrypted["card_number"] == sample_card_data.card_number
        assert decrypted["expiry_month"] == sample_card_data.expiry_month
        assert decrypted["expiry_year"] == sample_card_data.expiry_year
        assert decrypted["cvv"] == sample_card_data.cvv
        assert decrypted["cardholder_name"] == sample_card_data.cardholder_name

    def test_encrypt_decrypt_sensitive_data(self, encryption_service):
        """Test generic sensitive data encryption."""
        original_data = "sensitive_information_123"

        # Encrypt
        encrypted = encryption_service.encrypt_sensitive_data(original_data)
        assert isinstance(encrypted, str)
        assert encrypted != original_data

        # Decrypt
        decrypted = encryption_service.decrypt_sensitive_data(encrypted)
        assert decrypted == original_data

    def test_get_card_last_four(self, encryption_service):
        """Test extracting last four digits."""
        card_number = "4111111111111111"
        last_four = encryption_service.get_card_last_four(card_number)
        assert last_four == "1111"

        # Test with short card number
        short_card = "123"
        last_four = encryption_service.get_card_last_four(short_card)
        assert last_four == "123"

    def test_mask_card_number(self, encryption_service):
        """Test card number masking."""
        card_number = "4111111111111111"
        masked = encryption_service.mask_card_number(card_number)
        assert masked == "************1111"

        # Test with short card number
        short_card = "123"
        masked = encryption_service.mask_card_number(short_card)
        assert masked == "***"


class TestCacheService:
    """Test CacheService class."""

    @pytest.fixture
    def cache_service(self):
        """Create cache service instance."""
        return CacheService()

    @pytest.mark.asyncio
    async def test_set_and_get(self, cache_service):
        """Test setting and getting cache values."""
        key = "test_key"
        value = {"test": "data"}

        # Set value
        await cache_service.set(key, value, ttl=60)

        # Get value
        retrieved = await cache_service.get(key)
        assert retrieved == value

    @pytest.mark.asyncio
    async def test_get_nonexistent_key(self, cache_service):
        """Test getting non-existent key."""
        result = await cache_service.get("nonexistent_key")
        assert result is None

    @pytest.mark.asyncio
    async def test_delete(self, cache_service):
        """Test deleting cache entries."""
        key = "test_key"
        value = {"test": "data"}

        # Set and verify
        await cache_service.set(key, value)
        assert await cache_service.get(key) == value

        # Delete and verify
        deleted = await cache_service.delete(key)
        assert deleted is True
        assert await cache_service.get(key) is None

        # Delete non-existent key
        deleted = await cache_service.delete("nonexistent")
        assert deleted is False

    @pytest.mark.asyncio
    async def test_exists(self, cache_service):
        """Test checking key existence."""
        key = "test_key"
        value = {"test": "data"}

        # Key doesn't exist
        assert await cache_service.exists(key) is False

        # Set key and check existence
        await cache_service.set(key, value)
        assert await cache_service.exists(key) is True

    @pytest.mark.asyncio
    async def test_clear(self, cache_service):
        """Test clearing all cache entries."""
        # Set multiple keys
        await cache_service.set("key1", "value1")
        await cache_service.set("key2", "value2")

        # Verify size
        size = await cache_service.size()
        assert size == 2

        # Clear cache
        await cache_service.clear()

        # Verify empty
        size = await cache_service.size()
        assert size == 0
        assert await cache_service.get("key1") is None
        assert await cache_service.get("key2") is None

    @pytest.mark.asyncio
    async def test_stats(self, cache_service):
        """Test cache statistics."""
        # Set some entries
        await cache_service.set("key1", "value1")
        await cache_service.set("key2", "value2")

        # Get stats
        stats = await cache_service.stats()
        assert stats["size"] == 2
        assert stats["max_size"] == 1000  # Default from config
        assert "expired_entries" in stats
        assert "default_ttl" in stats
