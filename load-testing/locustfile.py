"""Main Locust file for coordinated load testing of Payment Service ecosystem."""

from locust import HttpUser, task, between
from locust.runners import MasterRunner
import random

try:
    from .payment_service_tasks import (
        PaymentServiceUser,
        HighVolumePaymentUser,
        FailureSimulationUser
    )
    from .banking_api_tasks import (
        BankingAPIUser,
        HighThroughputBankingUser,
        BankingFailureUser
    )
    from .config import config
except ImportError:
    # Fallback for direct execution
    from payment_service_tasks import (
        PaymentServiceUser,
        HighVolumePaymentUser,
        FailureSimulationUser
    )
    from banking_api_tasks import (
        BankingAPIUser,
        HighThroughputBankingUser,
        BankingFailureUser
    )
    from config import config

class MixedWorkloadUser(HttpUser):
    """User that switches between PaymentService and BankingAPI testing."""
    
    wait_time = between(1, 3)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Randomly assign this user to focus on either payments or banking
        self.focus = random.choice(["payment", "banking"])
        
        if self.focus == "payment":
            self.host = config.payment_service_url
            self.payment_user = PaymentServiceUser(self.environment)
            self.payment_user.client = self.client
        else:
            self.host = config.banking_api_url
            self.banking_user = BankingAPIUser(self.environment)
            self.banking_user.client = self.client
    
    @task
    def execute_focused_task(self):
        """Execute task based on user focus."""
        if self.focus == "payment":
            # Randomly select a payment service task
            tasks = [
                self.payment_user.process_payment,
                self.payment_user.process_refund,
                self.payment_user.get_transaction_status,
                self.payment_user.check_service_health
            ]
            random.choice(tasks)()
        else:
            # Randomly select a banking API task
            tasks = [
                self.banking_user.authorize_payment,
                self.banking_user.capture_payment,
                self.banking_user.process_refund,
                self.banking_user.check_transaction_status
            ]
            random.choice(tasks)()

class RealisticTrafficUser(HttpUser):
    """User that simulates realistic traffic patterns."""
    
    wait_time = between(5, 30)  # More realistic user behavior
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.host = config.payment_service_url
        self.auth_headers = {"Authorization": config.auth_token}
        self.user_session = {
            "transactions": [],
            "behavior_type": random.choice(["casual", "power", "business"])
        }
    
    def on_start(self):
        """Initialize user session."""
        # Check service health before starting
        self.client.get("/health")
    
    @task(weight=70)
    def typical_payment_flow(self):
        """Simulate typical payment flow with realistic delays."""
        try:
            from .data_generators import payment_generator
        except ImportError:
            from data_generators import payment_generator
        
        # Generate payment
        payment_data = payment_generator.generate_payment_request()
        
        # Simulate user thinking time before payment
        self.wait()
        
        response = self.client.post(
            "/api/v1/payments/process",
            json=payment_data,
            headers=self.auth_headers
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get("status") == "captured":
                self.user_session["transactions"].append({
                    "id": result.get("transaction_id"),
                    "amount": payment_data["amount"]
                })
                
                # Simulate checking transaction status after payment
                if random.random() < 0.3:  # 30% check status
                    self.wait()
                    self.client.get(
                        f"/api/v1/payments/{result.get('transaction_id')}",
                        headers=self.auth_headers
                    )
    
    @task(weight=10)
    def refund_scenario(self):
        """Simulate refund scenario."""
        if not self.user_session["transactions"]:
            return
        
        transaction = random.choice(self.user_session["transactions"])
        
        try:
            from .data_generators import payment_generator
        except ImportError:
            from data_generators import payment_generator
        refund_data = payment_generator.generate_refund_request(transaction["amount"])
        
        self.client.post(
            f"/api/v1/payments/{transaction['id']}/refund",
            json=refund_data,
            headers=self.auth_headers
        )
    
    @task(weight=15)
    def browse_transactions(self):
        """Simulate browsing transaction history."""
        if self.user_session["behavior_type"] == "business":
            # Business users check transaction lists more often
            merchant_id = f"merchant_{random.randint(1, 10):03d}"
            self.client.get(
                f"/api/v1/merchants/{merchant_id}/transactions",
                headers=self.auth_headers,
                params={"limit": 20, "offset": 0}
            )
    
    @task(weight=5)
    def health_monitoring(self):
        """Simulate monitoring/health checks."""
        if self.user_session["behavior_type"] == "business":
            self.client.get("/health")

# Event hooks for coordinated testing
def on_test_start(environment, **kwargs):
    """Called when the test starts."""
    if isinstance(environment.runner, MasterRunner):
        print("Starting coordinated load test...")
        print(f"Payment Service URL: {config.payment_service_url}")
        print(f"Banking API URL: {config.banking_api_url}")
        print("Test configuration:")
        print(f"  - Simulate failures: {config.simulate_failures}")
        print(f"  - Card decline rate: {config.card_decline_rate*100}%")
        print(f"  - Refund probability: {config.refund_probability*100}%")

def on_test_stop(environment, **kwargs):
    """Called when the test stops."""
    if isinstance(environment.runner, MasterRunner):
        print("Load test completed.")
        print("Check Datadog dashboard for metrics!")

# Import all user classes for Locust to discover
__all__ = [
    'PaymentServiceUser',
    'HighVolumePaymentUser', 
    'FailureSimulationUser',
    'BankingAPIUser',
    'HighThroughputBankingUser',
    'BankingFailureUser',
    'MixedWorkloadUser',
    'RealisticTrafficUser'
]