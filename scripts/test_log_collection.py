#!/usr/bin/env python3
"""Test script to verify logs from all services are being collected by Datadog."""

import subprocess
import json
import sys
import time

def run_command(command):
    """Run a shell command and return the output."""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        return result.stdout, result.stderr, result.returncode
    except Exception as e:
        return "", str(e), 1

def check_datadog_agent_status():
    """Check Datadog agent log collection status."""
    print("🔍 Checking Datadog Agent Log Collection Status")
    print("=" * 60)
    
    stdout, stderr, code = run_command("docker-compose exec -T datadog-agent agent status")
    
    if code != 0:
        print(f"❌ Failed to get agent status: {stderr}")
        return False
    
    # Look for Logs Agent section
    if "Logs Agent" in stdout:
        print("✅ Logs Agent is running")
        
        # Extract log statistics
        lines = stdout.split('\n')
        for i, line in enumerate(lines):
            if "Logs Agent" in line:
                # Look for key metrics in the next 20 lines
                for j in range(i, min(i+20, len(lines))):
                    if "LogsProcessed:" in lines[j]:
                        print(f"   📊 {lines[j].strip()}")
                    elif "LogsSent:" in lines[j]:
                        print(f"   📊 {lines[j].strip()}")
                    elif "BytesSent:" in lines[j]:
                        print(f"   📊 {lines[j].strip()}")
                break
        return True
    else:
        print("❌ Logs Agent not found in status")
        return False

def check_service_log_collection():
    """Check which services are being monitored for logs."""
    print("\n🔍 Checking Service Log Collection")
    print("=" * 60)
    
    stdout, stderr, code = run_command("docker-compose exec -T datadog-agent agent status")
    
    if code != 0:
        print(f"❌ Failed to get agent status: {stderr}")
        return False
    
    services_found = []
    lines = stdout.split('\n')
    
    for i, line in enumerate(lines):
        if "container_collect_all" in line:
            # Look for services in the next 50 lines
            for j in range(i, min(i+50, len(lines))):
                if "Service:" in lines[j]:
                    service_name = lines[j].split("Service:")[1].strip()
                    
                    # Look for bytes read in next few lines
                    bytes_read = "Unknown"
                    for k in range(j, min(j+10, len(lines))):
                        if "Bytes Read:" in lines[k]:
                            bytes_read = lines[k].split("Bytes Read:")[1].strip()
                            break
                    
                    services_found.append((service_name, bytes_read))
                    print(f"   📋 Service: {service_name}")
                    print(f"       📊 Bytes Read: {bytes_read}")
                    print()
            break
    
    if services_found:
        print(f"✅ Found {len(services_found)} services being monitored")
        return True
    else:
        print("❌ No services found in log collection")
        return False

def test_log_generation():
    """Generate logs from all services to test collection."""
    print("🔍 Testing Log Generation from All Services")
    print("=" * 60)
    
    # Generate payment service logs
    print("1. Testing Payment Service log generation...")
    stdout, stderr, code = run_command("""
        curl -X POST http://localhost:8000/api/v1/payments/process \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer test_token_123456789" \
        -d '{
            "merchant_id": "merchant_log_test",
            "amount": 25.50,
            "currency": "USD",
            "payment_method": "credit_card",
            "card_data": {
                "card_number": "4111111111111111",
                "expiry_month": 12,
                "expiry_year": 2025,
                "cvv": "123",
                "cardholder_name": "Log Test User"
            },
            "description": "Payment for log collection testing"
        }' 2>/dev/null
    """)
    
    if code == 0 and "transaction_id" in stdout:
        result = json.loads(stdout)
        transaction_id = result.get("transaction_id")
        print(f"   ✅ Payment processed: {transaction_id}")
    else:
        print(f"   ❌ Payment failed: {stderr}")
        return False
    
    # Check database logs by running a query
    print("2. Testing Database log generation...")
    stdout, stderr, code = run_command("docker-compose exec -T postgres psql -U postgres -d payment_db -c 'SELECT COUNT(*) FROM transactions;'")
    
    if code == 0:
        print("   ✅ Database query executed")
    else:
        print(f"   ❌ Database query failed: {stderr}")
    
    # Check mockserver logs by making a health call
    print("3. Testing Banking Service (MockServer) log generation...")
    stdout, stderr, code = run_command("curl -s http://localhost:1080/health")
    
    if code == 0:
        print("   ✅ Banking service health check completed")
    else:
        print(f"   ❌ Banking service call failed: {stderr}")
    
    return True

def verify_recent_logs():
    """Verify recent logs from services are available."""
    print("\n🔍 Verifying Recent Service Logs")
    print("=" * 60)
    
    services = [
        ("payment-service", "Processing payment"),
        ("mockserver", "received request"),
        ("postgres", "statement:")
    ]
    
    for service, search_term in services:
        print(f"Checking {service} logs...")
        stdout, stderr, code = run_command(f"docker-compose logs {service} | grep '{search_term}' | tail -3")
        
        if stdout.strip():
            lines = stdout.strip().split('\n')
            print(f"   ✅ Found {len(lines)} recent log entries")
            if lines:
                print(f"   📝 Latest: {lines[-1][:100]}...")
        else:
            print(f"   ⚠️  No recent logs found with '{search_term}'")
        print()

def main():
    """Main test function."""
    print("🚀 Datadog Log Collection Test")
    print("=" * 70)
    
    success = True
    
    # Check agent status
    if not check_datadog_agent_status():
        success = False
    
    # Check service collection
    if not check_service_log_collection():
        success = False
    
    # Generate test logs
    if not test_log_generation():
        success = False
    
    # Wait a bit for logs to be processed
    print("\n⏳ Waiting for logs to be processed...")
    time.sleep(5)
    
    # Verify logs
    verify_recent_logs()
    
    print("\n" + "=" * 70)
    if success:
        print("✅ Log collection test completed successfully!")
        print("\n📋 Next Steps:")
        print("1. Check Datadog Logs dashboard")
        print("2. Search for service:payment-service")
        print("3. Search for service:banking-service") 
        print("4. Search for service:payment-database")
        print("5. Verify logs are properly tagged and correlated")
    else:
        print("❌ Some log collection tests failed!")
        print("Check the errors above and ensure all services are running.")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())