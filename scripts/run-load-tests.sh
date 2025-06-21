#!/bin/bash

# Load Testing Runner Script for Payment Service
# This script provides easy commands to run different types of load tests

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
log() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Function to check if services are running
check_services() {
    log "Checking if payment service is running..."
    
    if ! curl -s http://localhost:8000/health > /dev/null 2>&1; then
        error "Payment service is not running on localhost:8000"
        echo "Please start the payment service first:"
        echo "  docker-compose up -d"
        exit 1
    fi
    
    success "Payment service is running"
}

# Function to start load testing
start_load_test() {
    local mode="$1"
    
    log "Starting load test in $mode mode..."
    
    case $mode in
        "web")
            log "Starting Locust web interface..."
            echo "Access the web interface at: http://localhost:8089"
            echo "Press Ctrl+C to stop"
            docker-compose --profile load-testing up locust
            ;;
        "headless")
            local users="${2:-10}"
            local spawn_rate="${3:-2}"
            local time="${4:-60s}"
            
            log "Running headless load test:"
            log "  Users: $users"
            log "  Spawn rate: $spawn_rate users/second"
            log "  Duration: $time"
            
            docker-compose --profile load-testing run --rm locust \
                locust --headless \
                --users $users \
                --spawn-rate $spawn_rate \
                --run-time $time \
                --host http://payment-service:8000 \
                PaymentServiceUser
            ;;
        "quick")
            log "Running quick 30-second test with 5 users..."
            docker-compose --profile load-testing run --rm locust \
                locust --headless \
                --users 5 \
                --spawn-rate 1 \
                --run-time 30s \
                --host http://payment-service:8000 \
                PaymentServiceUser
            ;;
        "stress")
            log "Running stress test with 50 users for 2 minutes..."
            warning "This is a high-load test. Monitor your system resources!"
            docker-compose --profile load-testing run --rm locust \
                locust --headless \
                --users 50 \
                --spawn-rate 5 \
                --run-time 2m \
                --host http://payment-service:8000 \
                PaymentServiceUser
            ;;
        *)
            error "Unknown mode: $mode"
            show_help
            exit 1
            ;;
    esac
}

# Function to show help
show_help() {
    echo "Load Testing Runner for Payment Service"
    echo ""
    echo "Usage: $0 <command> [options]"
    echo ""
    echo "Commands:"
    echo "  web                    Start Locust web interface (recommended)"
    echo "  quick                  Run quick 30-second test with 5 users"
    echo "  headless [users] [spawn_rate] [time]"
    echo "                         Run headless test with custom parameters"
    echo "  stress                 Run stress test (50 users, 2 minutes)"
    echo "  stop                   Stop all load testing containers"
    echo "  logs                   Show locust container logs"
    echo "  status                 Check status of services"
    echo ""
    echo "Examples:"
    echo "  $0 web                              # Start web interface"
    echo "  $0 quick                            # Quick test"
    echo "  $0 headless 20 3 90s               # 20 users, 3/sec spawn, 90 seconds"
    echo "  $0 stress                           # Stress test"
    echo ""
    echo "Web Interface:"
    echo "  When using 'web' mode, access http://localhost:8089 to:"
    echo "  - Configure number of users and spawn rate"
    echo "  - Monitor real-time performance metrics"
    echo "  - Download test results as CSV/HTML"
    echo "  - View detailed statistics and charts"
}

# Function to stop load tests
stop_load_test() {
    log "Stopping load testing containers..."
    docker-compose --profile load-testing down
    success "Load testing stopped"
}

# Function to show logs
show_logs() {
    log "Showing Locust container logs..."
    docker-compose --profile load-testing logs -f locust
}

# Function to show status
show_status() {
    log "Checking service status..."
    
    echo ""
    echo "=== Payment Service Status ==="
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        success "Payment Service: Running (http://localhost:8000)"
        curl -s http://localhost:8000/health | jq -r '.status // "unknown"' 2>/dev/null || echo "healthy"
    else
        error "Payment Service: Not running"
    fi
    
    echo ""
    echo "=== Locust Status ==="
    if curl -s http://localhost:8089 > /dev/null 2>&1; then
        success "Locust Web Interface: Running (http://localhost:8089)"
    else
        warning "Locust Web Interface: Not running"
    fi
    
    echo ""
    echo "=== Docker Containers ==="
    docker-compose ps
}

# Main script logic
case "${1:-help}" in
    "web")
        check_services
        start_load_test "web"
        ;;
    "quick")
        check_services
        start_load_test "quick"
        ;;
    "headless")
        check_services
        start_load_test "headless" "$2" "$3" "$4"
        ;;
    "stress")
        check_services
        start_load_test "stress"
        ;;
    "stop")
        stop_load_test
        ;;
    "logs")
        show_logs
        ;;
    "status")
        show_status
        ;;
    "help" | "-h" | "--help")
        show_help
        ;;
    *)
        error "Unknown command: $1"
        echo ""
        show_help
        exit 1
        ;;
esac