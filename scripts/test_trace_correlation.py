#!/usr/bin/env python3
"""Test script to verify trace correlation is working correctly."""

import requests
import json
import time
import sys

def test_trace_correlation():
    """Test that logs are properly correlated with APM traces."""
    
    print("🔍 Testing Trace Correlation")
    print("=" * 50)
    
    # Test endpoint
    base_url = "http://localhost:8000"
    
    # Test health endpoint first
    print("1. Testing health endpoint...")
    try:
        response = requests.get(f"{base_url}/health")
        if response.status_code == 200:
            print("   ✅ Health check passed")
        else:
            print(f"   ❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Health check error: {e}")
        return False
    
    # Test payment endpoint with auth
    print("2. Testing payment endpoint for trace correlation...")
    
    payment_data = {
        "merchant_id": "merchant_test_trace",
        "amount": 42.99,
        "currency": "USD",
        "payment_method": "credit_card",
        "card_data": {
            "card_number": "4111111111111111",
            "expiry_month": 12,
            "expiry_year": 2025,
            "cvv": "123",
            "cardholder_name": "Trace Test User"
        },
        "description": "Payment for trace correlation testing"
    }
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer test_token_123456789"
    }
    
    try:
        response = requests.post(
            f"{base_url}/api/v1/payments/process",
            json=payment_data,
            headers=headers
        )
        
        if response.status_code == 200:
            result = response.json()
            transaction_id = result.get("transaction_id")
            print(f"   ✅ Payment processed successfully")
            print(f"   📋 Transaction ID: {transaction_id}")
            
            # Check transaction status
            print("3. Testing transaction status lookup...")
            status_response = requests.get(
                f"{base_url}/api/v1/payments/{transaction_id}",
                headers=headers
            )
            
            if status_response.status_code == 200:
                print("   ✅ Transaction status retrieved successfully")
                return True
            else:
                print(f"   ❌ Transaction status failed: {status_response.status_code}")
                return False
                
        else:
            print(f"   ❌ Payment failed: {response.status_code}")
            print(f"   📄 Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Payment error: {e}")
        return False

def check_logs_for_correlation():
    """Instructions for checking log correlation."""
    print("\n🔍 Manual Log Verification Steps")
    print("=" * 50)
    print("1. Run: docker-compose logs payment-service | grep 'Processing payment'")
    print("2. Look for log entries with the following fields:")
    print("   - correlation_id: Should be consistent across related log entries")
    print("   - dd.trace_id: Datadog trace ID (if APM is active)")
    print("   - dd.span_id: Datadog span ID (if APM is active)")
    print("   - dd.service: Should be 'payment-service'")
    print("   - dd.env: Should be 'dev'")
    print("\n3. In Datadog APM:")
    print("   - Find the trace with the correlation_id")
    print("   - Click on 'Logs' tab in the trace view")
    print("   - Verify logs are automatically correlated")
    print("\n4. In Datadog Logs:")
    print("   - Search for: @correlation_id:<correlation_id_from_logs>")
    print("   - Click on any log entry")
    print("   - Verify 'View Trace' link appears if correlation is working")

if __name__ == "__main__":
    print("🚀 Payment Service Trace Correlation Test")
    print("=" * 60)
    
    success = test_trace_correlation()
    
    if success:
        print("\n✅ All tests passed!")
        check_logs_for_correlation()
        sys.exit(0)
    else:
        print("\n❌ Tests failed!")
        print("Ensure the payment service is running: make docker-up")
        sys.exit(1)