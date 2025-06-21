"""Realistic test data generators for payment scenarios."""

import random
from datetime import datetime, timedelta
from typing import Dict, Any, List
from faker import Faker
from decimal import Decimal

from config import config, VALID_CARDS, DECLINED_CARDS, CURRENCIES, MERCHANT_CATEGORIES

fake = Faker()

class PaymentDataGenerator:
    """Generates realistic payment test data."""
    
    def __init__(self):
        self.merchant_ids = [f"merchant_{i:03d}" for i in range(1, config.merchant_count + 1)]
        self.customers = self._generate_customers()
        self.transaction_counter = 0
    
    def _generate_customers(self) -> List[Dict[str, Any]]:
        """Generate a pool of customers for realistic testing."""
        customers = []
        for i in range(config.customer_count):
            customers.append({
                "customer_id": f"cust_{i:05d}",
                "name": fake.name(),
                "email": fake.email(),
                "phone": fake.phone_number(),
                "address": {
                    "street": fake.street_address(),
                    "city": fake.city(),
                    "state": fake.state_abbr(),
                    "zip_code": fake.zipcode(),
                    "country": "US"
                }
            })
        return customers
    
    def generate_payment_request(self, force_failure: bool = False) -> Dict[str, Any]:
        """Generate a realistic payment request."""
        self.transaction_counter += 1
        customer = random.choice(self.customers)
        
        # Choose card based on failure simulation
        if force_failure or (config.simulate_failures and random.random() < config.card_decline_rate):
            card_number = random.choice(DECLINED_CARDS)
        else:
            card_number = random.choice(VALID_CARDS)
        
        # Generate amount (convert to dollars for API)
        amount_cents = random.randint(config.min_payment_amount, config.max_payment_amount)
        amount = Decimal(amount_cents) / 100
        
        # Generate expiry date (1-3 years in future)
        future_date = datetime.now() + timedelta(days=random.randint(365, 1095))
        
        return {
            "merchant_id": random.choice(self.merchant_ids),
            "amount": float(amount),
            "currency": random.choice(CURRENCIES),
            "payment_method": "credit_card",
            "card_data": {
                "card_number": card_number,
                "expiry_month": future_date.month,
                "expiry_year": future_date.year,
                "cvv": fake.credit_card_security_code(),
                "cardholder_name": customer["name"]
            },
            "billing_address": customer["address"],
            "customer": {
                "id": customer["customer_id"],
                "email": customer["email"],
                "phone": customer["phone"]
            },
            "description": self._generate_description(),
            "metadata": {
                "order_id": f"order_{self.transaction_counter:08d}",
                "category": random.choice(MERCHANT_CATEGORIES),
                "channel": random.choice(["web", "mobile", "pos", "api"]),
                "user_agent": fake.user_agent(),
                "ip_address": fake.ipv4(),
                "session_id": fake.uuid4(),
                "test_transaction": True
            }
        }
    
    def generate_refund_request(self, original_amount: float) -> Dict[str, Any]:
        """Generate a refund request for a successful payment."""
        # Determine if partial or full refund
        if random.random() < config.partial_refund_probability:
            # Partial refund (20-80% of original amount)
            refund_amount = original_amount * random.uniform(0.2, 0.8)
        else:
            # Full refund
            refund_amount = original_amount
        
        return {
            "amount": round(refund_amount, 2),
            "reason": random.choice([
                "Customer request",
                "Duplicate charge",
                "Product return",
                "Service cancellation",
                "Billing error",
                "Fraudulent transaction",
                "Quality issue",
                "Wrong item shipped"
            ]),
            "metadata": {
                "refund_type": "partial" if refund_amount < original_amount else "full",
                "initiated_by": random.choice(["customer", "merchant", "admin"]),
                "refund_id": f"rfnd_{fake.uuid4()[:8]}",
                "notes": fake.sentence()
            }
        }
    
    def _generate_description(self) -> str:
        """Generate realistic transaction descriptions."""
        category = random.choice(MERCHANT_CATEGORIES)
        
        descriptions = {
            "retail": lambda: f"Purchase at {fake.company()} - {fake.word().title()} Store",
            "restaurant": lambda: f"Dining at {fake.company()} Restaurant",
            "gas_station": lambda: f"Fuel purchase - {fake.company()} Station #{random.randint(1, 999)}",
            "grocery": lambda: f"Grocery shopping - {fake.company()} Market",
            "online": lambda: f"Online purchase - {fake.domain_name()}",
            "subscription": lambda: f"Monthly subscription - {fake.company()} Service",
            "marketplace": lambda: f"Marketplace purchase - Order #{fake.uuid4()[:8]}",
            "hotel": lambda: f"Hotel stay - {fake.company()} Hotel",
            "airline": lambda: f"Flight booking - {fake.company()} Airlines",
            "pharmacy": lambda: f"Pharmacy purchase - {fake.company()} Pharmacy"
        }
        
        return descriptions[category]()

class BankingDataGenerator:
    """Generates realistic banking API simulation data."""
    
    def __init__(self):
        self.authorization_counter = 0
    
    def generate_authorization_response(self, amount: float, card_number: str) -> Dict[str, Any]:
        """Generate banking API authorization response."""
        self.authorization_counter += 1
        
        # Simulate different response scenarios
        if card_number in DECLINED_CARDS:
            status = "declined"
            response_code = random.choice(["51", "05", "14", "54", "61"])
            message = self._get_decline_message(response_code)
            auth_id = None
        else:
            # Simulate occasional random declines even for valid cards
            if random.random() < 0.02:  # 2% random decline rate
                status = "declined"
                response_code = "05"
                message = "Do not honor"
                auth_id = None
            else:
                status = "approved"
                response_code = "00"
                message = "Approved"
                auth_id = f"auth_{self.authorization_counter:010d}"
        
        return {
            "status": status,
            "authorization_id": auth_id,
            "response_code": response_code,
            "message": message,
            "amount": amount,
            "currency": "USD",
            "timestamp": datetime.utcnow().isoformat(),
            "processing_time_ms": random.randint(50, 500),
            "network": self._detect_card_network(card_number),
            "risk_score": random.randint(1, 100),
            "metadata": {
                "processor_id": f"proc_{random.randint(1000, 9999)}",
                "batch_id": f"batch_{random.randint(100000, 999999)}",
                "terminal_id": f"term_{random.randint(10000, 99999)}",
                "acquirer": random.choice(["First Data", "Chase Paymentech", "Worldpay", "Elavon"])
            }
        }
    
    def generate_capture_response(self, auth_id: str, amount: float) -> Dict[str, Any]:
        """Generate banking API capture response."""
        return {
            "status": "captured",
            "capture_id": f"cap_{fake.uuid4()[:12]}",
            "authorization_id": auth_id,
            "amount": amount,
            "settlement_date": (datetime.now() + timedelta(days=1)).date().isoformat(),
            "processing_fee": round(amount * 0.029 + 0.30, 2),  # Typical processing fee
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def generate_refund_response(self, amount: float) -> Dict[str, Any]:
        """Generate banking API refund response."""
        return {
            "status": "refunded",
            "refund_id": f"rfnd_{fake.uuid4()[:12]}",
            "amount": amount,
            "processing_time": random.randint(1, 5),  # days
            "timestamp": datetime.utcnow().isoformat(),
            "expected_completion": (datetime.now() + timedelta(days=random.randint(3, 7))).date().isoformat()
        }
    
    def _detect_card_network(self, card_number: str) -> str:
        """Detect card network from card number."""
        if card_number.startswith('4'):
            return "Visa"
        elif card_number.startswith('5'):
            return "Mastercard"
        elif card_number.startswith('3'):
            return "American Express"
        elif card_number.startswith('6'):
            return "Discover"
        else:
            return "Unknown"
    
    def _get_decline_message(self, response_code: str) -> str:
        """Get human-readable decline message."""
        decline_messages = {
            "51": "Insufficient funds",
            "05": "Do not honor",
            "14": "Invalid card number",
            "54": "Expired card",
            "61": "Exceeds withdrawal limit"
        }
        return decline_messages.get(response_code, "Transaction declined")

# Global generator instances
payment_generator = PaymentDataGenerator()
banking_generator = BankingDataGenerator()