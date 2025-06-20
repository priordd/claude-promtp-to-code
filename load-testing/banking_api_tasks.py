"""Locust tasks for BankingAPI (MockServer) load testing."""

import json
import random
import time
from typing import Dict, Any
from locust import task, HttpUser, between
from locust.exception import RescheduleTask

try:
    from .config import config
    from .data_generators import banking_generator, payment_generator
except ImportError:
    from config import config
    from data_generators import banking_generator, payment_generator

class BankingAPIUser(HttpUser):
    """Locust user for BankingAPI load testing via MockServer."""
    
    wait_time = between(config.min_wait_time / 1000, config.max_wait_time / 1000)
    host = config.banking_api_url
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pending_authorizations = []
        self.completed_captures = []
        self.session_stats = {
            "authorizations": 0,
            "captures": 0,
            "refunds": 0,
            "settlements": 0,
            "health_checks": 0
        }
    
    @task(weight=40)
    def authorize_payment(self):
        """Authorize a payment transaction (40% of all tasks)."""
        payment_data = payment_generator.generate_payment_request()
        
        # Create authorization request
        auth_request = {
            "amount": payment_data["amount"],
            "currency": payment_data["currency"],
            "card": {
                "number": payment_data["card_data"]["card_number"],
                "expiry_month": payment_data["card_data"]["expiry_month"],
                "expiry_year": payment_data["card_data"]["expiry_year"],
                "cvv": payment_data["card_data"]["cvv"],
                "holder_name": payment_data["card_data"]["cardholder_name"]
            },
            "merchant_id": payment_data["merchant_id"],
            "transaction_id": f"txn_{int(time.time())}_{random.randint(1000, 9999)}",
            "description": payment_data["description"]
        }
        
        with self.client.post(
            "/api/v1/authorize",
            json=auth_request,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                try:
                    result = response.json()
                    self.session_stats["authorizations"] += 1
                    
                    if result.get("status") == "approved":
                        # Store authorization for potential capture
                        self.pending_authorizations.append({
                            "auth_id": result.get("authorization_id"),
                            "amount": auth_request["amount"],
                            "merchant_id": auth_request["merchant_id"]
                        })
                        response.success()
                    elif result.get("status") == "declined":
                        # Expected decline
                        response.success()
                    else:
                        response.failure(f"Unexpected authorization status: {result.get('status')}")
                except (ValueError, KeyError) as e:
                    response.failure(f"Invalid authorization response: {e}")
            else:
                response.failure(f"Authorization failed: {response.status_code}")
    
    @task(weight=25)
    def capture_payment(self):
        """Capture an authorized payment (25% of all tasks)."""
        if not self.pending_authorizations:
            # No pending authorizations to capture
            raise RescheduleTask()
        
        auth = random.choice(self.pending_authorizations)
        
        capture_request = {
            "authorization_id": auth["auth_id"],
            "amount": auth["amount"],  # Full capture
            "merchant_id": auth["merchant_id"]
        }
        
        with self.client.post(
            "/api/v1/capture",
            json=capture_request,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                try:
                    result = response.json()
                    self.session_stats["captures"] += 1
                    
                    if result.get("status") == "captured":
                        # Move to completed captures
                        self.completed_captures.append({
                            "capture_id": result.get("capture_id"),
                            "amount": auth["amount"],
                            "merchant_id": auth["merchant_id"]
                        })
                        self.pending_authorizations.remove(auth)
                        response.success()
                    else:
                        response.failure(f"Unexpected capture status: {result.get('status')}")
                except (ValueError, KeyError) as e:
                    response.failure(f"Invalid capture response: {e}")
            elif response.status_code == 404:
                response.failure("Authorization not found for capture")
                # Remove invalid authorization
                if auth in self.pending_authorizations:
                    self.pending_authorizations.remove(auth)
            else:
                response.failure(f"Capture failed: {response.status_code}")
    
    @task(weight=15)
    def process_refund(self):
        """Process a refund for captured payment (15% of all tasks)."""
        if not self.completed_captures:
            # No completed captures to refund
            raise RescheduleTask()
        
        capture = random.choice(self.completed_captures)
        refund_amount = capture["amount"] * random.uniform(0.1, 1.0)  # Partial or full refund
        
        refund_request = {
            "capture_id": capture["capture_id"],
            "amount": round(refund_amount, 2),
            "reason": random.choice([
                "Customer request",
                "Merchant error",
                "Fraudulent transaction",
                "Product return"
            ]),
            "merchant_id": capture["merchant_id"]
        }
        
        with self.client.post(
            "/api/v1/refund",
            json=refund_request,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                try:
                    result = response.json()
                    self.session_stats["refunds"] += 1
                    
                    if result.get("status") == "refunded":
                        response.success()
                        # Remove from completed captures if full refund
                        if refund_amount >= capture["amount"]:
                            self.completed_captures.remove(capture)
                    else:
                        response.failure(f"Unexpected refund status: {result.get('status')}")
                except (ValueError, KeyError) as e:
                    response.failure(f"Invalid refund response: {e}")
            elif response.status_code == 404:
                response.failure("Capture not found for refund")
                # Remove invalid capture
                if capture in self.completed_captures:
                    self.completed_captures.remove(capture)
            else:
                response.failure(f"Refund failed: {response.status_code}")
    
    @task(weight=10)
    def check_transaction_status(self):
        """Check transaction status (10% of all tasks)."""
        all_transactions = self.pending_authorizations + self.completed_captures
        
        if not all_transactions:
            raise RescheduleTask()
        
        transaction = random.choice(all_transactions)
        transaction_id = transaction.get("auth_id") or transaction.get("capture_id")
        
        with self.client.get(
            f"/api/v1/transactions/{transaction_id}",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                try:
                    result = response.json()
                    if "status" in result and "transaction_id" in result:
                        response.success()
                    else:
                        response.failure("Invalid transaction status response")
                except ValueError:
                    response.failure("Invalid JSON in transaction status response")
            elif response.status_code == 404:
                response.failure("Transaction not found")
            else:
                response.failure(f"Transaction status check failed: {response.status_code}")
    
    @task(weight=5)
    def get_settlement_report(self):
        """Get settlement report (5% of all tasks)."""
        # Generate random date range for settlement report
        import datetime
        end_date = datetime.date.today()
        start_date = end_date - datetime.timedelta(days=random.randint(1, 30))
        
        params = {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "merchant_id": random.choice(payment_generator.merchant_ids)
        }
        
        with self.client.get(
            "/api/v1/settlements",
            params=params,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                try:
                    result = response.json()
                    self.session_stats["settlements"] += 1
                    if isinstance(result, dict) and "settlements" in result:
                        response.success()
                    else:
                        response.failure("Invalid settlement report format")
                except ValueError:
                    response.failure("Invalid JSON in settlement response")
            elif response.status_code == 404:
                response.success()  # No settlements for period is acceptable
            else:
                response.failure(f"Settlement report failed: {response.status_code}")
    
    @task(weight=3)
    def check_banking_health(self):
        """Check banking API health (3% of all tasks)."""
        with self.client.get("/banking/health", catch_response=True) as response:
            if response.status_code == 200:
                try:
                    result = response.json()
                    self.session_stats["health_checks"] += 1
                    if "status" in result:
                        response.success()
                    else:
                        response.failure("Invalid health response format")
                except ValueError:
                    response.failure("Invalid JSON in health response")
            else:
                response.failure(f"Banking health check failed: {response.status_code}")
    
    @task(weight=2)
    def batch_authorization(self):
        """Process batch authorizations (2% of all tasks)."""
        batch_size = random.randint(5, 20)
        batch_requests = []
        
        for _ in range(batch_size):
            payment_data = payment_generator.generate_payment_request()
            batch_requests.append({
                "amount": payment_data["amount"],
                "currency": payment_data["currency"],
                "card_number": payment_data["card_data"]["card_number"],
                "merchant_id": payment_data["merchant_id"],
                "transaction_id": f"batch_txn_{int(time.time())}_{random.randint(1000, 9999)}"
            })
        
        batch_request = {
            "batch_id": f"batch_{int(time.time())}",
            "transactions": batch_requests
        }
        
        with self.client.post(
            "/api/v1/batch/authorize",
            json=batch_request,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                try:
                    result = response.json()
                    if "batch_id" in result and "results" in result:
                        # Count successful authorizations in batch
                        approved_count = sum(1 for r in result["results"] if r.get("status") == "approved")
                        self.session_stats["authorizations"] += approved_count
                        response.success()
                    else:
                        response.failure("Invalid batch authorization response")
                except ValueError:
                    response.failure("Invalid JSON in batch response")
            else:
                response.failure(f"Batch authorization failed: {response.status_code}")

class HighThroughputBankingUser(BankingAPIUser):
    """High-throughput banking user for performance testing."""
    
    wait_time = between(0.05, 0.2)  # Very fast execution
    
    @task(weight=60)
    def rapid_authorizations(self):
        """Rapid authorization processing."""
        self.authorize_payment()
    
    @task(weight=30)
    def rapid_captures(self):
        """Rapid capture processing."""
        self.capture_payment()
    
    @task(weight=10)
    def rapid_status_checks(self):
        """Rapid status checking."""
        self.check_transaction_status()

class BankingFailureUser(BankingAPIUser):
    """Banking user that simulates failure scenarios."""
    
    wait_time = between(1, 4)
    
    @task(weight=50)
    def invalid_authorization_requests(self):
        """Send invalid authorization requests."""
        invalid_scenarios = [
            # Missing required fields
            {"amount": 100},
            # Invalid amount
            {"amount": -100, "currency": "USD", "card": {"number": "4111111111111111"}},
            # Invalid card number
            {"amount": 100, "currency": "USD", "card": {"number": "123"}},
            # Missing currency
            {"amount": 100, "card": {"number": "4111111111111111"}},
        ]
        
        invalid_request = random.choice(invalid_scenarios)
        
        with self.client.post(
            "/api/v1/authorize",
            json=invalid_request,
            catch_response=True
        ) as response:
            if response.status_code == 400:
                response.success()  # Expected validation error
            else:
                response.failure(f"Expected 400 for invalid auth request, got {response.status_code}")
    
    @task(weight=30)
    def capture_nonexistent_auth(self):
        """Try to capture non-existent authorization."""
        fake_auth_id = f"fake_auth_{random.randint(100000, 999999)}"
        
        capture_request = {
            "authorization_id": fake_auth_id,
            "amount": 100.0,
            "merchant_id": "fake_merchant"
        }
        
        with self.client.post(
            "/api/v1/capture",
            json=capture_request,
            catch_response=True
        ) as response:
            if response.status_code == 404:
                response.success()  # Expected not found
            else:
                response.failure(f"Expected 404 for fake auth capture, got {response.status_code}")
    
    @task(weight=20)
    def refund_nonexistent_capture(self):
        """Try to refund non-existent capture."""
        fake_capture_id = f"fake_cap_{random.randint(100000, 999999)}"
        
        refund_request = {
            "capture_id": fake_capture_id,
            "amount": 50.0,
            "reason": "Test refund",
            "merchant_id": "fake_merchant"
        }
        
        with self.client.post(
            "/api/v1/refund",
            json=refund_request,
            catch_response=True
        ) as response:
            if response.status_code == 404:
                response.success()  # Expected not found
            else:
                response.failure(f"Expected 404 for fake capture refund, got {response.status_code}")