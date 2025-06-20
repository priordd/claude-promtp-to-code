"""Integration tests for API endpoints."""

import pytest
from decimal import Decimal
from unittest.mock import patch

from fastapi.testclient import TestClient
from payment_service.main import app


class TestPaymentAPI:
    """Test payment API endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    @patch('payment_service.database.connection.database_manager')
    @patch('payment_service.services.payment_service.PaymentService.process_payment')
    def test_process_payment_success(self, mock_process_payment, mock_db, client, 
                                   sample_payment_request, valid_auth_token):
        """Test successful payment processing."""
        from datetime import datetime
        from payment_service.models.payment import PaymentResponse, PaymentStatus, PaymentMethod
        
        # Mock successful response
        mock_process_payment.return_value = PaymentResponse(
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
        
        response = client.post(
            "/api/v1/payments/process",
            json=sample_payment_request.dict(),
            headers={"Authorization": valid_auth_token}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["transaction_id"] == "txn_123456"
        assert data["status"] == "captured"
        assert data["amount"] == "99.99"
    
    def test_process_payment_unauthorized(self, client, sample_payment_request, invalid_auth_token):
        """Test payment processing without valid authentication."""
        response = client.post(
            "/api/v1/payments/process",
            json=sample_payment_request.dict(),
            headers={"Authorization": invalid_auth_token}
        )
        
        assert response.status_code == 401
    
    def test_process_payment_no_auth(self, client, sample_payment_request):
        """Test payment processing without authentication."""
        response = client.post(
            "/api/v1/payments/process",
            json=sample_payment_request.dict()
        )
        
        assert response.status_code == 401
    
    def test_process_payment_invalid_data(self, client, valid_auth_token):
        """Test payment processing with invalid data."""
        invalid_request = {
            "merchant_id": "",  # Invalid - empty merchant ID
            "amount": -10.00,   # Invalid - negative amount
            "currency": "INVALID",  # Invalid - not 3 chars
            "payment_method": "invalid_method",
        }
        
        response = client.post(
            "/api/v1/payments/process",
            json=invalid_request,
            headers={"Authorization": valid_auth_token}
        )
        
        assert response.status_code == 422  # Validation error
    
    @patch('payment_service.services.payment_service.PaymentService.get_payment_status')
    def test_get_payment_status_success(self, mock_get_status, client, valid_auth_token):
        """Test successful payment status retrieval."""
        from datetime import datetime
        from payment_service.models.payment import PaymentStatusResponse, PaymentStatus, PaymentMethod
        
        mock_get_status.return_value = PaymentStatusResponse(
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
        
        response = client.get(
            "/api/v1/payments/txn_123456",
            headers={"Authorization": valid_auth_token}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["transaction_id"] == "txn_123456"
        assert data["status"] == "captured"
    
    @patch('payment_service.services.payment_service.PaymentService.get_payment_status')
    def test_get_payment_status_not_found(self, mock_get_status, client, valid_auth_token):
        """Test payment status retrieval for non-existent transaction."""
        mock_get_status.side_effect = ValueError("Transaction not found")
        
        response = client.get(
            "/api/v1/payments/nonexistent_txn",
            headers={"Authorization": valid_auth_token}
        )
        
        assert response.status_code == 404
    
    @patch('payment_service.services.payment_service.PaymentService.process_refund')
    def test_process_refund_success(self, mock_process_refund, client, 
                                  sample_refund_request, valid_auth_token):
        """Test successful refund processing."""
        from datetime import datetime
        from payment_service.models.payment import RefundResponse, RefundStatus
        
        mock_process_refund.return_value = RefundResponse(
            refund_id="ref_123456",
            transaction_id="txn_123456",
            amount=Decimal("50.00"),
            currency="USD",
            status=RefundStatus.COMPLETED,
            reason="Customer request",
            external_refund_id="ext_ref_123456",
            metadata={"test_refund": True},
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            processed_at=datetime.utcnow(),
        )
        
        response = client.post(
            "/api/v1/payments/txn_123456/refund",
            json=sample_refund_request.dict(),
            headers={"Authorization": valid_auth_token}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["refund_id"] == "ref_123456"
        assert data["status"] == "completed"
        assert data["amount"] == "50.00"
    
    @patch('payment_service.services.payment_service.PaymentService.process_refund')
    def test_process_refund_invalid_transaction(self, mock_process_refund, client, 
                                              sample_refund_request, valid_auth_token):
        """Test refund processing for invalid transaction."""
        mock_process_refund.side_effect = ValueError("Transaction not found")
        
        response = client.post(
            "/api/v1/payments/invalid_txn/refund",
            json=sample_refund_request.dict(),
            headers={"Authorization": valid_auth_token}
        )
        
        assert response.status_code == 400


class TestHealthAPI:
    """Test health check API."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    @patch('payment_service.database.connection.database_manager.health_check')
    @patch('payment_service.services.banking_service.BankingService.health_check')
    @patch('payment_service.services.event_service.EventService.health_check')
    def test_health_check_all_healthy(self, mock_event_health, mock_banking_health, 
                                    mock_db_health, client):
        """Test health check when all services are healthy."""
        mock_db_health.return_value = True
        mock_banking_health.return_value = True
        mock_event_health.return_value = True
        
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["services"]["database"] is True
        assert data["services"]["banking_service"] is True
        assert data["services"]["event_service"] is True
    
    @patch('payment_service.database.connection.database_manager.health_check')
    @patch('payment_service.services.banking_service.BankingService.health_check')
    @patch('payment_service.services.event_service.EventService.health_check')
    def test_health_check_some_unhealthy(self, mock_event_health, mock_banking_health, 
                                       mock_db_health, client):
        """Test health check when some services are unhealthy."""
        mock_db_health.return_value = True
        mock_banking_health.return_value = False  # Banking service down
        mock_event_health.return_value = True
        
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "unhealthy"
        assert data["services"]["database"] is True
        assert data["services"]["banking_service"] is False
        assert data["services"]["event_service"] is True


class TestRootAPI:
    """Test root API endpoint."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    def test_root_endpoint(self, client):
        """Test root endpoint."""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "Payment Processing Service"
        assert "version" in data
        assert data["status"] == "running"
        assert "timestamp" in data