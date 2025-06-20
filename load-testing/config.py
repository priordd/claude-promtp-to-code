"""Configuration for load testing."""

import os
from typing import Dict, Any
try:
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic import BaseSettings

class LoadTestConfig(BaseSettings):
    """Load testing configuration."""
    
    # Service URLs
    payment_service_url: str = "http://localhost:8000"
    banking_api_url: str = "http://localhost:1080"
    
    # Authentication
    auth_token: str = "Bearer test_token_UKSZyHH7EkwD7skZOi2IGBBpjT9a046Q"
    
    # Test behavior configuration
    min_wait_time: int = 1000  # milliseconds
    max_wait_time: int = 5000  # milliseconds
    
    # Payment amounts (in cents to avoid floating point issues)
    min_payment_amount: int = 100    # $1.00
    max_payment_amount: int = 100000 # $1000.00
    
    # Refund configuration
    refund_probability: float = 0.1  # 10% chance of refund
    partial_refund_probability: float = 0.6  # 60% of refunds are partial
    
    # Failure simulation
    simulate_failures: bool = True
    card_decline_rate: float = 0.05  # 5% of cards will be declined
    network_error_rate: float = 0.02  # 2% network errors
    
    # Test data variety
    merchant_count: int = 10
    customer_count: int = 1000
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# Global configuration instance
config = LoadTestConfig()

# Test credit cards (for different scenarios)
VALID_CARDS = [
    "4111111111111111",  # Visa
    "5555555555554444",  # Mastercard
    "378282246310005",   # American Express
    "6011111111111117",  # Discover
]

DECLINED_CARDS = [
    "4000000000000002",  # Declined card
    "4000000000000127",  # Incorrect CVC
    "4000000000000069",  # Expired card
]

# Currency codes for international testing
CURRENCIES = ["USD", "EUR", "GBP", "CAD", "AUD"]

# Merchant categories for realistic scenarios
MERCHANT_CATEGORIES = [
    "retail",
    "restaurant", 
    "gas_station",
    "grocery",
    "online",
    "subscription",
    "marketplace",
    "hotel",
    "airline",
    "pharmacy"
]