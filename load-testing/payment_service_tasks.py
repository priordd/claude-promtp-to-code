"""Locust tasks for PaymentService load testing."""

import json
import random
from typing import Dict, Any, Optional
from locust import task, HttpUser, between
from locust.exception import RescheduleTask

from config import config
from data_generators import payment_generator

class PaymentServiceUser(HttpUser):
    """Locust user for PaymentService load testing."""
    
    wait_time = between(config.min_wait_time / 1000, config.max_wait_time / 1000)
    host = config.payment_service_url
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.auth_headers = {"Authorization": config.auth_token}
        self.successful_transactions = []
        self.session_stats = {
            "payments_attempted": 0,
            "payments_successful": 0,
            "refunds_attempted": 0,
            "refunds_successful": 0,
            "failures": 0
        }
    
    def on_start(self):
        """Called when user starts - check service health."""
        self.check_service_health()
    
    def on_stop(self):
        """Called when user stops - log session statistics."""
        success_rate = (
            self.session_stats["payments_successful"] / 
            max(self.session_stats["payments_attempted"], 1) * 100
        )
        print(f"User session completed: {success_rate:.1f}% payment success rate")
    
    @task(weight=70)
    def process_payment(self):
        """Process a payment transaction (70% of all tasks)."""
        payment_data = payment_generator.generate_payment_request()
        self.session_stats["payments_attempted"] += 1
        
        with self.client.post(
            "/api/v1/payments/process",
            json=payment_data,
            headers=self.auth_headers,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                try:
                    result = response.json()
                    if result.get("status") == "captured":
                        self.session_stats["payments_successful"] += 1
                        # Store successful transaction for potential refund
                        self.successful_transactions.append({
                            "transaction_id": result.get("transaction_id"),
                            "amount": payment_data["amount"]
                        })
                        response.success()
                    elif result.get("status") == "failed":
                        # Expected failure (declined card, etc.)
                        response.success()
                    else:
                        response.failure(f"Unexpected payment status: {result.get('status')}")
                except (ValueError, KeyError) as e:
                    response.failure(f"Invalid response format: {e}")
                    self.session_stats["failures"] += 1
            elif response.status_code == 400:
                # Bad request - could be validation error
                try:
                    error_detail = response.json().get("detail", "Bad request")
                    if "validation" in error_detail.lower():
                        response.success()  # Expected validation error
                    else:
                        response.failure(f"Payment validation error: {error_detail}")
                except ValueError:
                    response.failure("Bad request with invalid JSON response")
                self.session_stats["failures"] += 1
            elif response.status_code == 401:
                response.failure("Authentication failed")
                self.session_stats["failures"] += 1
            elif response.status_code >= 500:
                response.failure(f"Server error: {response.status_code}")
                self.session_stats["failures"] += 1
            else:
                response.failure(f"Unexpected status code: {response.status_code}")
                self.session_stats["failures"] += 1
    
    @task(weight=10)
    def process_refund(self):
        """Process a refund (10% of all tasks)."""
        if not self.successful_transactions:
            # No successful transactions to refund, skip this iteration
            raise RescheduleTask()
        
        # Select a random successful transaction for refund
        transaction = random.choice(self.successful_transactions)
        refund_data = payment_generator.generate_refund_request(transaction["amount"])
        self.session_stats["refunds_attempted"] += 1
        
        with self.client.post(
            f"/api/v1/payments/{transaction['transaction_id']}/refund",
            json=refund_data,
            headers=self.auth_headers,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                try:
                    result = response.json()
                    if result.get("status") in ["completed", "processing"]:
                        self.session_stats["refunds_successful"] += 1
                        response.success()
                        # Remove transaction from successful list to avoid double refunds
                        self.successful_transactions.remove(transaction)
                    else:
                        response.failure(f"Unexpected refund status: {result.get('status')}")
                except (ValueError, KeyError) as e:
                    response.failure(f"Invalid refund response format: {e}")
            elif response.status_code == 404:
                response.failure("Transaction not found for refund")
                # Remove invalid transaction from list
                if transaction in self.successful_transactions:
                    self.successful_transactions.remove(transaction)
            elif response.status_code == 400:
                try:
                    error_detail = response.json().get("detail", "Bad request")
                    response.failure(f"Refund validation error: {error_detail}")
                except ValueError:
                    response.failure("Bad refund request")
            else:
                response.failure(f"Refund failed with status: {response.status_code}")
    
    @task(weight=15)
    def get_transaction_status(self):
        """Check transaction status (15% of all tasks)."""
        if not self.successful_transactions:
            # No transactions to check, skip
            raise RescheduleTask()
        
        transaction = random.choice(self.successful_transactions)
        
        with self.client.get(
            f"/api/v1/payments/{transaction['transaction_id']}",
            headers=self.auth_headers,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                try:
                    result = response.json()
                    if "transaction_id" in result and "status" in result:
                        response.success()
                    else:
                        response.failure("Invalid transaction response format")
                except ValueError:
                    response.failure("Invalid JSON in transaction response")
            elif response.status_code == 404:
                response.failure("Transaction not found")
                # Remove invalid transaction
                if transaction in self.successful_transactions:
                    self.successful_transactions.remove(transaction)
            else:
                response.failure(f"Transaction lookup failed: {response.status_code}")
    
    @task(weight=3)
    def get_merchant_transactions(self):
        """Get merchant transaction list (3% of all tasks)."""
        merchant_id = random.choice(payment_generator.merchant_ids)
        
        with self.client.get(
            f"/api/v1/merchants/{merchant_id}/transactions",
            headers=self.auth_headers,
            params={"limit": 50, "offset": 0},
            catch_response=True
        ) as response:
            if response.status_code == 200:
                try:
                    result = response.json()
                    if isinstance(result, dict) and "transactions" in result:
                        response.success()
                    else:
                        response.failure("Invalid merchant transactions response format")
                except ValueError:
                    response.failure("Invalid JSON in merchant transactions response")
            elif response.status_code == 404:
                response.success()  # Merchant not found is acceptable
            else:
                response.failure(f"Merchant transactions lookup failed: {response.status_code}")
    
    @task(weight=2)
    def check_service_health(self):
        """Check service health (2% of all tasks)."""
        with self.client.get("/health", catch_response=True) as response:
            if response.status_code == 200:
                try:
                    result = response.json()
                    if "status" in result and "services" in result:
                        response.success()
                    else:
                        response.failure("Invalid health check response format")
                except ValueError:
                    response.failure("Invalid JSON in health response")
            else:
                response.failure(f"Health check failed: {response.status_code}")

class HighVolumePaymentUser(PaymentServiceUser):
    """High-volume payment user for stress testing."""
    
    wait_time = between(0.1, 0.5)  # Much faster execution
    
    @task(weight=90)
    def rapid_payments(self):
        """Rapid payment processing for volume testing."""
        self.process_payment()
    
    @task(weight=10)
    def rapid_status_checks(self):
        """Rapid status checking."""
        self.get_transaction_status()

class FailureSimulationUser(PaymentServiceUser):
    """User that simulates various failure scenarios."""
    
    wait_time = between(2, 8)
    
    @task(weight=40)
    def invalid_payment_requests(self):
        """Send invalid payment requests to test error handling."""
        invalid_scenarios = [
            # Missing required fields
            {"merchant_id": "test"},
            # Invalid amount
            {"merchant_id": "test", "amount": -100, "currency": "USD"},
            # Invalid currency
            {"merchant_id": "test", "amount": 100, "currency": "INVALID"},
            # Invalid card data
            {"merchant_id": "test", "amount": 100, "currency": "USD", "card_data": {"card_number": "123"}},
        ]
        
        invalid_data = random.choice(invalid_scenarios)
        
        with self.client.post(
            "/api/v1/payments/process",
            json=invalid_data,
            headers=self.auth_headers,
            catch_response=True
        ) as response:
            if response.status_code == 400:
                response.success()  # Expected validation error
            else:
                response.failure(f"Expected 400 for invalid request, got {response.status_code}")
    
    @task(weight=30)
    def force_declined_payments(self):
        """Force payment declines using test cards."""
        payment_data = payment_generator.generate_payment_request(force_failure=True)
        
        with self.client.post(
            "/api/v1/payments/process",
            json=payment_data,
            headers=self.auth_headers,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                try:
                    result = response.json()
                    if result.get("status") == "failed":
                        response.success()  # Expected decline
                    else:
                        response.failure(f"Expected declined payment, got status: {result.get('status')}")
                except ValueError:
                    response.failure("Invalid JSON response for declined payment")
            else:
                response.failure(f"Declined payment request failed: {response.status_code}")
    
    @task(weight=20)
    def unauthorized_requests(self):
        """Test requests without proper authorization."""
        payment_data = payment_generator.generate_payment_request()
        
        with self.client.post(
            "/api/v1/payments/process",
            json=payment_data,
            headers={},  # No auth headers
            catch_response=True
        ) as response:
            if response.status_code == 401:
                response.success()  # Expected unauthorized
            else:
                response.failure(f"Expected 401 for unauthorized request, got {response.status_code}")
    
    @task(weight=10)
    def nonexistent_endpoints(self):
        """Test nonexistent endpoints."""
        with self.client.get("/api/v1/nonexistent", catch_response=True) as response:
            if response.status_code == 404:
                response.success()  # Expected not found
            else:
                response.failure(f"Expected 404 for nonexistent endpoint, got {response.status_code}")