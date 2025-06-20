#!/bin/bash

# Load Testing Runner Scripts for Payment Service
# Provides easy commands to run different types of load tests

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default configuration
LOCUST_HOST=${LOCUST_HOST:-"http://localhost:8000"}
USERS=${USERS:-10}
SPAWN_RATE=${SPAWN_RATE:-2}
RUN_TIME=${RUN_TIME:-60s}
REPORT_DIR="reports"

# Functions
print_banner() {
    echo -e "${BLUE}"
    echo "╔═══════════════════════════════════════╗"
    echo "║     Payment Service Load Testing      ║"
    echo "╚═══════════════════════════════════════╝"
    echo -e "${NC}"
}

print_usage() {
    echo -e "${YELLOW}Usage: $0 [command] [options]${NC}"
    echo ""
    echo "Commands:"
    echo "  basic          - Run basic load test"
    echo "  volume         - Run high-volume test"
    echo "  banking        - Run banking API test"
    echo "  failures       - Run failure simulation test"
    echo "  realistic      - Run realistic traffic pattern test"
    echo "  stress         - Run stress test"
    echo "  endurance      - Run endurance test (30 minutes)"
    echo "  smoke          - Run smoke test (quick validation)"
    echo "  docker         - Run tests using Docker Compose"
    echo "  docker-volume  - Run volume tests using Docker"
    echo "  docker-banking - Run banking tests using Docker"
    echo "  docker-failures- Run failure tests using Docker"
    echo "  stop-docker    - Stop all Docker test containers"
    echo "  report         - Generate HTML report from last test"
    echo "  clean          - Clean up test reports"
    echo "  help           - Show this help message"
    echo ""
    echo "Environment Variables:"
    echo "  LOCUST_HOST    - Target host (default: http://localhost:8000)"
    echo "  USERS          - Number of users (default: 10)"
    echo "  SPAWN_RATE     - Users spawned per second (default: 2)"
    echo "  RUN_TIME       - Test duration (default: 60s)"
    echo ""
    echo "Examples:"
    echo "  $0 basic"
    echo "  USERS=50 SPAWN_RATE=5 $0 volume"
    echo "  LOCUST_HOST=http://production:8000 $0 stress"
}

check_dependencies() {
    if ! command -v locust &> /dev/null; then
        echo -e "${RED}Error: Locust is not installed${NC}"
        echo "Install with: pip install locust"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        echo -e "${YELLOW}Warning: docker-compose not found, Docker tests will not work${NC}"
    fi
}

setup_reports_dir() {
    mkdir -p $REPORT_DIR
    echo -e "${GREEN}Reports will be saved to: $REPORT_DIR${NC}"
}

run_basic_test() {
    echo -e "${GREEN}Running basic load test...${NC}"
    echo "Users: $USERS, Spawn Rate: $SPAWN_RATE, Duration: $RUN_TIME"
    
    locust -f locustfile.py \
        --host=$LOCUST_HOST \
        --users=$USERS \
        --spawn-rate=$SPAWN_RATE \
        --run-time=$RUN_TIME \
        --html=$REPORT_DIR/basic-report.html \
        --csv=$REPORT_DIR/basic-results \
        --headless \
        --user-class=PaymentServiceUser
}

run_volume_test() {
    echo -e "${GREEN}Running high-volume test...${NC}"
    
    locust -f locustfile.py \
        --host=$LOCUST_HOST \
        --users=${USERS:-100} \
        --spawn-rate=${SPAWN_RATE:-10} \
        --run-time=${RUN_TIME:-300s} \
        --html=$REPORT_DIR/volume-report.html \
        --csv=$REPORT_DIR/volume-results \
        --headless \
        --user-class=HighVolumePaymentUser
}

run_banking_test() {
    echo -e "${GREEN}Running banking API test...${NC}"
    
    locust -f locustfile.py \
        --host=${BANKING_HOST:-"http://localhost:1080"} \
        --users=$USERS \
        --spawn-rate=$SPAWN_RATE \
        --run-time=$RUN_TIME \
        --html=$REPORT_DIR/banking-report.html \
        --csv=$REPORT_DIR/banking-results \
        --headless \
        --user-class=BankingAPIUser
}

run_failures_test() {
    echo -e "${GREEN}Running failure simulation test...${NC}"
    
    locust -f locustfile.py \
        --host=$LOCUST_HOST \
        --users=$USERS \
        --spawn-rate=$SPAWN_RATE \
        --run-time=$RUN_TIME \
        --html=$REPORT_DIR/failures-report.html \
        --csv=$REPORT_DIR/failures-results \
        --headless \
        --user-class=FailureSimulationUser
}

run_realistic_test() {
    echo -e "${GREEN}Running realistic traffic test...${NC}"
    
    locust -f locustfile.py \
        --host=$LOCUST_HOST \
        --users=${USERS:-20} \
        --spawn-rate=${SPAWN_RATE:-1} \
        --run-time=${RUN_TIME:-600s} \
        --html=$REPORT_DIR/realistic-report.html \
        --csv=$REPORT_DIR/realistic-results \
        --headless \
        --user-class=RealisticTrafficUser
}

run_stress_test() {
    echo -e "${GREEN}Running stress test...${NC}"
    
    locust -f locustfile.py \
        --host=$LOCUST_HOST \
        --users=${USERS:-200} \
        --spawn-rate=${SPAWN_RATE:-20} \
        --run-time=${RUN_TIME:-600s} \
        --html=$REPORT_DIR/stress-report.html \
        --csv=$REPORT_DIR/stress-results \
        --headless \
        --user-class=MixedWorkloadUser
}

run_endurance_test() {
    echo -e "${GREEN}Running endurance test (30 minutes)...${NC}"
    
    locust -f locustfile.py \
        --host=$LOCUST_HOST \
        --users=${USERS:-50} \
        --spawn-rate=${SPAWN_RATE:-5} \
        --run-time=1800s \
        --html=$REPORT_DIR/endurance-report.html \
        --csv=$REPORT_DIR/endurance-results \
        --headless \
        --user-class=RealisticTrafficUser
}

run_smoke_test() {
    echo -e "${GREEN}Running smoke test...${NC}"
    
    locust -f locustfile.py \
        --host=$LOCUST_HOST \
        --users=5 \
        --spawn-rate=1 \
        --run-time=30s \
        --html=$REPORT_DIR/smoke-report.html \
        --csv=$REPORT_DIR/smoke-results \
        --headless \
        --user-class=PaymentServiceUser
}

run_docker_tests() {
    echo -e "${GREEN}Running tests with Docker Compose...${NC}"
    docker-compose -f docker-compose.locust.yml up --build
}

run_docker_volume() {
    echo -e "${GREEN}Running volume tests with Docker...${NC}"
    docker-compose -f docker-compose.locust.yml --profile volume-test up --build
}

run_docker_banking() {
    echo -e "${GREEN}Running banking tests with Docker...${NC}"
    docker-compose -f docker-compose.locust.yml --profile banking-test up --build
}

run_docker_failures() {
    echo -e "${GREEN}Running failure tests with Docker...${NC}"
    docker-compose -f docker-compose.locust.yml --profile failure-test up --build
}

stop_docker_tests() {
    echo -e "${YELLOW}Stopping Docker test containers...${NC}"
    docker-compose -f docker-compose.locust.yml down --remove-orphans
    docker-compose -f docker-compose.locust.yml --profile volume-test down --remove-orphans
    docker-compose -f docker-compose.locust.yml --profile banking-test down --remove-orphans
    docker-compose -f docker-compose.locust.yml --profile failure-test down --remove-orphans
}

generate_report() {
    echo -e "${GREEN}Opening latest test report...${NC}"
    if [ -f "$REPORT_DIR/basic-report.html" ]; then
        if command -v open &> /dev/null; then
            open "$REPORT_DIR/basic-report.html"
        elif command -v xdg-open &> /dev/null; then
            xdg-open "$REPORT_DIR/basic-report.html"
        else
            echo "Report available at: $REPORT_DIR/basic-report.html"
        fi
    else
        echo -e "${RED}No reports found. Run a test first.${NC}"
    fi
}

clean_reports() {
    echo -e "${YELLOW}Cleaning up test reports...${NC}"
    rm -rf $REPORT_DIR/*
    echo -e "${GREEN}Reports cleaned.${NC}"
}

# Main script logic
print_banner

case "${1:-help}" in
    basic)
        check_dependencies
        setup_reports_dir
        run_basic_test
        ;;
    volume)
        check_dependencies
        setup_reports_dir
        run_volume_test
        ;;
    banking)
        check_dependencies
        setup_reports_dir
        run_banking_test
        ;;
    failures)
        check_dependencies
        setup_reports_dir
        run_failures_test
        ;;
    realistic)
        check_dependencies
        setup_reports_dir
        run_realistic_test
        ;;
    stress)
        check_dependencies
        setup_reports_dir
        run_stress_test
        ;;
    endurance)
        check_dependencies
        setup_reports_dir
        run_endurance_test
        ;;
    smoke)
        check_dependencies
        setup_reports_dir
        run_smoke_test
        ;;
    docker)
        setup_reports_dir
        run_docker_tests
        ;;
    docker-volume)
        setup_reports_dir
        run_docker_volume
        ;;
    docker-banking)
        setup_reports_dir
        run_docker_banking
        ;;
    docker-failures)
        setup_reports_dir
        run_docker_failures
        ;;
    stop-docker)
        stop_docker_tests
        ;;
    report)
        generate_report
        ;;
    clean)
        clean_reports
        ;;
    help|*)
        print_usage
        ;;
esac

echo -e "${GREEN}Done!${NC}"