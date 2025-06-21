#!/bin/bash

# Payment Service API Testing Script
# This script tests all API endpoints with various scenarios

set -e  # Exit on any error

# Configuration
BASE_URL="http://localhost:8000"
AUTH_TOKEN="Bearer test_token_123456789"  # Demo auth token
CORRELATION_ID="test_$(date +%s)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test counters
TESTS_PASSED=0
TESTS_FAILED=0
TOTAL_TESTS=0

# Helper functions
log() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

success() {
    echo -e "${GREEN}[PASS]${NC} $1"
    ((TESTS_PASSED++))
}

error() {
    echo -e "${RED}[FAIL]${NC} $1"
    ((TESTS_FAILED++))
}

warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

# Function to make HTTP requests with proper error handling
make_request() {
    local method="$1"
    local endpoint="$2"
    local data="$3"
    local expected_status="$4"
    local description="$5"
    
    ((TOTAL_TESTS++))
    
    log "Testing: $description"
    log "Request: $method $endpoint"
    
    if [ "$method" = "GET" ]; then
        response=$(curl -s -w "\n%{http_code}" \
            -H "Authorization: $AUTH_TOKEN" \
            -H "Content-Type: application/json" \
            -H "X-Correlation-ID: $CORRELATION_ID" \
            "$BASE_URL$endpoint")
    else
        response=$(curl -s -w "\n%{http_code}" \
            -X "$method" \
            -H "Authorization: $AUTH_TOKEN" \
            -H "Content-Type: application/json" \
            -H "X-Correlation-ID: $CORRELATION_ID" \
            -d "$data" \
            "$BASE_URL$endpoint")
    fi
    
    # Extract HTTP status code (last line)
    status_code=$(echo "$response" | tail -n 1)
    
    # Extract response body (all lines except last) - macOS compatible
    response_body=$(echo "$response" | sed '$d')
    
    if [ "$status_code" = "$expected_status" ]; then
        success "$description - Status: $status_code"
        if [ -n "$response_body" ] && echo "$response_body" | jq . >/dev/null 2>&1; then
            echo "$response_body" | jq .
        else
            echo "Response: $response_body"
        fi
    else
        error "$description - Expected: $expected_status, Got: $status_code"
        echo "Response: $response_body"
    fi
    
    echo ""
}

# Function to extract transaction ID from response
extract_transaction_id() {
    if [ -n "$1" ] && echo "$1" | jq . >/dev/null 2>&1; then
        echo "$1" | jq -r '.transaction_id' 2>/dev/null || echo ""
    else
        echo ""
    fi
}

# Function to wait for service to be ready
wait_for_service() {
    log "Waiting for payment service to be ready..."
    
    max_attempts=30
    attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s "$BASE_URL/health" > /dev/null 2>&1; then
            success "Payment service is ready!"
            return 0
        fi
        
        log "Attempt $attempt/$max_attempts - Service not ready, waiting..."
        sleep 2
        ((attempt++))
    done
    
    error "Service failed to start within expected time"
    exit 1
}

# Test data
VALID_PAYMENT_REQUEST='{
    "merchant_id": "merchant_test_123",
    "amount": 99.99,
    "currency": "USD",
    "payment_method": "credit_card",
    "card_data": {
        "card_number": "4111111111111111",
        "expiry_month": 12,
        "expiry_year": 2025,
        "cvv": "123",
        "cardholder_name": "John Doe"
    },
    "description": "Test payment via API script",
    "metadata": {
        "test": true,
        "script": "test_api.sh"
    }
}'

DECLINED_PAYMENT_REQUEST='{
    "merchant_id": "merchant_test_123",
    "amount": 99.99,
    "currency": "USD",
    "payment_method": "credit_card",
    "card_data": {
        "card_number": "4000000000000002",
        "expiry_month": 12,
        "expiry_year": 2025,
        "cvv": "123",
        "cardholder_name": "John Doe"
    },
    "description": "Test declined payment",
    "metadata": {
        "test": true,
        "expected": "declined"
    }
}'

INVALID_PAYMENT_REQUEST='{
    "merchant_id": "",
    "amount": -10.00,
    "currency": "INVALID",
    "payment_method": "invalid_method"
}'

REFUND_REQUEST='{
    "amount": 50.00,
    "reason": "Customer requested refund",
    "metadata": {
        "refund_test": true
    }
}'

FULL_REFUND_REQUEST='{
    "reason": "Full refund requested",
    "metadata": {
        "full_refund": true
    }
}'

# Main test execution
main() {
    echo "=================================================="
    echo "Payment Service API Test Suite"
    echo "=================================================="
    echo "Base URL: $BASE_URL"
    echo "Correlation ID: $CORRELATION_ID"
    echo ""
    
    # Wait for service to be ready
    wait_for_service
    
    echo "=================================================="
    echo "1. HEALTH CHECK TESTS"
    echo "=================================================="
    
    # Test health check
    make_request "GET" "/health" "" "200" "Health check endpoint"
    
    # Test root endpoint
    make_request "GET" "/" "" "200" "Root endpoint"
    
    echo "=================================================="
    echo "2. AUTHENTICATION TESTS"
    echo "=================================================="
    
    # Test without authentication
    ((TOTAL_TESTS++))
    log "Testing: Payment processing without authentication"
    response=$(curl -s -w "\n%{http_code}" \
        -X POST \
        -H "Content-Type: application/json" \
        -d "$VALID_PAYMENT_REQUEST" \
        "$BASE_URL/api/v1/payments/process")
    
    status_code=$(echo "$response" | tail -n 1)
    if [ "$status_code" = "401" ]; then
        success "Payment processing without auth - Status: $status_code"
    else
        error "Payment processing without auth - Expected: 401, Got: $status_code"
    fi
    echo ""
    
    # Test with invalid authentication
    ((TOTAL_TESTS++))
    log "Testing: Payment processing with invalid authentication"
    response=$(curl -s -w "\n%{http_code}" \
        -X POST \
        -H "Authorization: Bearer invalid_token" \
        -H "Content-Type: application/json" \
        -d "$VALID_PAYMENT_REQUEST" \
        "$BASE_URL/api/v1/payments/process")
    
    status_code=$(echo "$response" | tail -n 1)
    if [ "$status_code" = "401" ]; then
        success "Payment processing with invalid auth - Status: $status_code"
    else
        error "Payment processing with invalid auth - Expected: 401, Got: $status_code"
    fi
    echo ""
    
    echo "=================================================="
    echo "3. PAYMENT PROCESSING TESTS"
    echo "=================================================="
    
    # Test valid payment processing
    response=$(curl -s -w "\n%{http_code}" \
        -X POST \
        -H "Authorization: $AUTH_TOKEN" \
        -H "Content-Type: application/json" \
        -H "X-Correlation-ID: $CORRELATION_ID" \
        -d "$VALID_PAYMENT_REQUEST" \
        "$BASE_URL/api/v1/payments/process")
    
    status_code=$(echo "$response" | tail -n 1)
    response_body=$(echo "$response" | sed '$d')
    
    ((TOTAL_TESTS++))
    if [ "$status_code" = "200" ]; then
        success "Valid payment processing - Status: $status_code"
        TRANSACTION_ID=$(extract_transaction_id "$response_body")
        log "Transaction ID: $TRANSACTION_ID"
        if [ -n "$response_body" ] && echo "$response_body" | jq . >/dev/null 2>&1; then
            echo "$response_body" | jq .
        else
            echo "Response: $response_body"
        fi
    else
        error "Valid payment processing - Expected: 200, Got: $status_code"
        echo "Response: $response_body"
        TRANSACTION_ID=""
    fi
    echo ""
    
    # Test invalid payment request
    make_request "POST" "/api/v1/payments/process" "$INVALID_PAYMENT_REQUEST" "422" "Invalid payment request validation"
    
    # Test declined payment
    make_request "POST" "/api/v1/payments/process" "$DECLINED_PAYMENT_REQUEST" "200" "Declined payment processing"
    
    echo "=================================================="
    echo "4. PAYMENT STATUS TESTS"
    echo "=================================================="
    
    if [ -n "$TRANSACTION_ID" ]; then
        # Test payment status retrieval
        make_request "GET" "/api/v1/payments/$TRANSACTION_ID" "" "200" "Payment status retrieval - valid transaction"
    else
        warning "Skipping payment status test - no valid transaction ID"
    fi
    
    # Test payment status for non-existent transaction
    make_request "GET" "/api/v1/payments/nonexistent_transaction" "" "404" "Payment status retrieval - non-existent transaction"
    
    echo "=================================================="
    echo "5. REFUND PROCESSING TESTS"
    echo "=================================================="
    
    if [ -n "$TRANSACTION_ID" ]; then
        # Test partial refund
        make_request "POST" "/api/v1/payments/$TRANSACTION_ID/refund" "$REFUND_REQUEST" "200" "Partial refund processing"
        
        # Test full refund (should work if partial refund amount allows)
        make_request "POST" "/api/v1/payments/$TRANSACTION_ID/refund" "$FULL_REFUND_REQUEST" "200" "Full refund processing"
    else
        warning "Skipping refund tests - no valid transaction ID"
    fi
    
    # Test refund for non-existent transaction
    make_request "POST" "/api/v1/payments/nonexistent_transaction/refund" "$REFUND_REQUEST" "400" "Refund for non-existent transaction"
    
    echo "=================================================="
    echo "6. PERFORMANCE TESTS"
    echo "=================================================="
    
    # Test concurrent payment processing
    log "Testing concurrent payment processing (5 requests)"
    start_time=$(date +%s)
    
    for i in {1..5}; do
        if echo "$VALID_PAYMENT_REQUEST" | jq . >/dev/null 2>&1; then
            CONCURRENT_REQUEST=$(echo "$VALID_PAYMENT_REQUEST" | jq --arg desc "Concurrent test payment $i" '.description = $desc')
        else
            CONCURRENT_REQUEST="$VALID_PAYMENT_REQUEST"
        fi
        
        curl -s \
            -X POST \
            -H "Authorization: $AUTH_TOKEN" \
            -H "Content-Type: application/json" \
            -H "X-Correlation-ID: concurrent_$i_$CORRELATION_ID" \
            -d "$CONCURRENT_REQUEST" \
            "$BASE_URL/api/v1/payments/process" > /dev/null &
    done
    
    # Wait for all background requests to complete
    wait
    
    end_time=$(date +%s)
    duration=$((end_time - start_time))
    
    ((TOTAL_TESTS++))
    if [ $duration -le 10 ]; then
        success "Concurrent processing test completed in ${duration}s"
    else
        warning "Concurrent processing took ${duration}s (may indicate performance issues)"
    fi
    echo ""
    
    echo "=================================================="
    echo "7. ERROR HANDLING TESTS"
    echo "=================================================="
    
    # Test malformed JSON
    ((TOTAL_TESTS++))
    log "Testing: Malformed JSON request"
    response=$(curl -s -w "\n%{http_code}" \
        -X POST \
        -H "Authorization: $AUTH_TOKEN" \
        -H "Content-Type: application/json" \
        -d '{"invalid": json}' \
        "$BASE_URL/api/v1/payments/process")
    
    status_code=$(echo "$response" | tail -n 1)
    if [ "$status_code" = "422" ] || [ "$status_code" = "400" ]; then
        success "Malformed JSON handling - Status: $status_code"
    else
        error "Malformed JSON handling - Expected: 422 or 400, Got: $status_code"
    fi
    echo ""
    
    # Test very large request
    LARGE_DESCRIPTION=$(printf "%*s" 10000 | tr ' ' 'A')
    if echo "$VALID_PAYMENT_REQUEST" | jq . >/dev/null 2>&1; then
        LARGE_REQUEST=$(echo "$VALID_PAYMENT_REQUEST" | jq --arg desc "$LARGE_DESCRIPTION" '.description = $desc')
    else
        LARGE_REQUEST="$VALID_PAYMENT_REQUEST"
    fi
    
    make_request "POST" "/api/v1/payments/process" "$LARGE_REQUEST" "422" "Very large request handling"
    
    echo "=================================================="
    echo "TEST SUMMARY"
    echo "=================================================="
    
    echo "Total Tests: $TOTAL_TESTS"
    echo -e "${GREEN}Passed: $TESTS_PASSED${NC}"
    echo -e "${RED}Failed: $TESTS_FAILED${NC}"
    
    if [ $TESTS_FAILED -eq 0 ]; then
        echo -e "${GREEN}All tests passed! ✅${NC}"
        exit 0
    else
        echo -e "${RED}Some tests failed! ❌${NC}"
        exit 1
    fi
}

# Check if required tools are available
check_dependencies() {
    for cmd in curl jq; do
        if ! command -v $cmd &> /dev/null; then
            error "$cmd is required but not installed"
            exit 1
        fi
    done
}

# Script execution
if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    echo "Payment Service API Test Script"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -h, --help     Show this help message"
    echo "  --url URL      Set base URL (default: $BASE_URL)"
    echo "  --token TOKEN  Set auth token (default: test token)"
    echo ""
    echo "Environment Variables:"
    echo "  BASE_URL      Payment service base URL"
    echo "  AUTH_TOKEN    Authentication token"
    echo ""
    echo "Examples:"
    echo "  $0                                    # Run with defaults"
    echo "  $0 --url http://localhost:8001       # Use different URL"
    echo "  BASE_URL=http://prod.example.com $0  # Use environment variable"
    exit 0
fi

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --url)
            BASE_URL="$2"
            shift 2
            ;;
        --token)
            AUTH_TOKEN="$2"
            shift 2
            ;;
        *)
            error "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Override with environment variables if set
BASE_URL=${BASE_URL:-"http://localhost:8000"}
AUTH_TOKEN=${AUTH_TOKEN:-"Bearer test_token_123456789"}

# Run the tests
check_dependencies
main