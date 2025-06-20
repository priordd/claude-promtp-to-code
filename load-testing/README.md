# Payment Service Load Testing with Locust

Comprehensive load testing suite for the Payment Service ecosystem using Locust. This package provides realistic traffic simulation for both the PaymentService API and BankingAPI (MockServer).

## 🎯 Features

### Comprehensive Test Scenarios
- **PaymentService Testing**: Process payments, refunds, transaction lookups, merchant operations
- **BankingAPI Testing**: Authorization, capture, refund, settlement, batch processing  
- **Mixed Workload**: Coordinated testing across both services
- **Realistic Traffic**: Simulates actual user behavior patterns
- **Failure Simulation**: Tests error handling and resilience
- **High Volume**: Stress testing with configurable load levels

### Realistic Data Generation
- **1000+ unique customers** with realistic profiles
- **Multiple merchants** across different categories
- **Valid and invalid credit cards** for testing scenarios
- **International currencies** and transaction types
- **Realistic transaction amounts** and descriptions
- **Failure simulation** with configurable rates

### Multiple Execution Modes
- **Standalone Locust**: Direct Python execution
- **Docker Compose**: Distributed load testing with master/worker setup
- **Different User Classes**: Specialized testing scenarios
- **Automated Scripts**: Easy-to-use test runners

## 🚀 Quick Start

### Prerequisites
```bash
# Install Python dependencies
pip install -r requirements.txt

# Or install Locust directly
pip install locust faker requests pydantic python-dotenv

# Ensure Payment Service is running
docker-compose up -d
```

### Basic Usage

#### 1. Simple Load Test
```bash
# Run basic load test with Locust UI
locust -f locustfile.py --host=http://localhost:8000

# Open browser to http://localhost:8089
# Configure: 10 users, 2 spawn rate, run for 60 seconds
```

#### 2. Headless Testing
```bash
# Run without UI
locust -f locustfile.py \
  --host=http://localhost:8000 \
  --users=20 \
  --spawn-rate=2 \
  --run-time=60s \
  --headless \
  --html=reports/test-report.html
```

#### 3. Using Test Runner Scripts
```bash
# Make script executable
chmod +x scripts/run_tests.sh

# Run different test scenarios
./scripts/run_tests.sh basic           # Basic load test
./scripts/run_tests.sh volume          # High-volume test  
./scripts/run_tests.sh banking         # Banking API test
./scripts/run_tests.sh failures        # Failure simulation
./scripts/run_tests.sh realistic       # Realistic traffic
./scripts/run_tests.sh stress          # Stress test
./scripts/run_tests.sh endurance       # 30-minute endurance test
./scripts/run_tests.sh smoke           # Quick smoke test
```

### Docker Compose Testing

#### 1. Distributed Load Testing
```bash
# Run with master + 2 workers
docker-compose -f docker-compose.locust.yml up

# Access Locust UI at http://localhost:8089
```

#### 2. Specialized Test Profiles
```bash
# High-volume testing
docker-compose -f docker-compose.locust.yml --profile volume-test up

# Banking API testing  
docker-compose -f docker-compose.locust.yml --profile banking-test up

# Failure simulation testing
docker-compose -f docker-compose.locust.yml --profile failure-test up
```

#### 3. Stop All Tests
```bash
./scripts/run_tests.sh stop-docker
```

## 📊 Test Scenarios

### PaymentService Tests (`PaymentServiceUser`)
- **Process Payment** (70%): Credit card payments with validation
- **Process Refund** (10%): Full and partial refunds
- **Transaction Status** (15%): Status lookups and tracking
- **Merchant Transactions** (3%): Merchant transaction listings
- **Health Checks** (2%): Service health monitoring

### BankingAPI Tests (`BankingAPIUser`)  
- **Authorize Payment** (40%): Card authorization requests
- **Capture Payment** (25%): Capture authorized payments
- **Process Refund** (15%): Banking refund processing
- **Transaction Status** (10%): Banking transaction lookups
- **Settlement Reports** (5%): Settlement and reporting
- **Health Checks** (3%): Banking API health
- **Batch Operations** (2%): Bulk transaction processing

### Failure Simulation (`FailureSimulationUser`)
- **Invalid Requests**: Malformed JSON, missing fields
- **Declined Cards**: Test card numbers that simulate declines
- **Unauthorized Access**: Requests without proper authentication
- **Non-existent Resources**: 404 error scenarios

### Realistic Traffic (`RealisticTrafficUser`)
- **Casual Users**: Longer wait times, simple transactions
- **Power Users**: Frequent transactions, status checking
- **Business Users**: Merchant reports, transaction monitoring
- **Realistic Delays**: Simulates human thinking time

## ⚙️ Configuration

### Environment Variables
Create `.env` file from `.env.example`:

```bash
# Service URLs
PAYMENT_SERVICE_URL=http://localhost:8000
BANKING_API_URL=http://localhost:1080

# Authentication  
AUTH_TOKEN=Bearer test_token_123456789

# Test Behavior
MIN_WAIT_TIME=1000          # Minimum wait between requests (ms)
MAX_WAIT_TIME=5000          # Maximum wait between requests (ms)
SIMULATE_FAILURES=true      # Enable failure simulation
CARD_DECLINE_RATE=0.05      # 5% card decline rate
REFUND_PROBABILITY=0.1      # 10% refund probability

# Test Data Scale
MERCHANT_COUNT=10           # Number of test merchants
CUSTOMER_COUNT=1000         # Number of test customers
```

### Test Data Customization
Modify `data_generators.py` to customize:
- **Payment amounts**: Min/max transaction values
- **Card networks**: Valid and invalid test cards
- **Merchant categories**: Business types and descriptions
- **Currency codes**: International payment testing
- **Customer profiles**: Realistic user demographics

## 📈 Monitoring & Reports

### Locust Web UI
- **Real-time metrics**: RPS, response times, error rates
- **Request statistics**: Per-endpoint performance
- **Failure analysis**: Error tracking and categorization
- **Charts**: Visual performance monitoring

### Generated Reports
```bash
reports/
├── basic-report.html       # Basic test results
├── volume-report.html      # High-volume test results  
├── banking-report.html     # Banking API test results
├── failures-report.html    # Failure simulation results
├── realistic-report.html   # Realistic traffic results
├── stress-report.html      # Stress test results
└── *.csv                   # Raw data exports
```

### Datadog Integration
The load tests will populate your Datadog dashboard with:
- **Payment metrics**: Transaction volumes, success rates
- **Database metrics**: Query performance, connection counts
- **System metrics**: CPU, memory, response times
- **Custom metrics**: Business KPIs and operational data

## 🔧 Advanced Usage

### Custom User Classes
```python
class CustomUser(PaymentServiceUser):
    wait_time = between(1, 3)
    
    @task
    def custom_scenario(self):
        # Your custom test logic
        pass
```

### Environment-Specific Testing
```bash
# Production testing (with caution!)
LOCUST_HOST=https://api.production.com ./scripts/run_tests.sh smoke

# Staging environment
LOCUST_HOST=https://api.staging.com ./scripts/run_tests.sh realistic
```

### Load Testing Best Practices

#### 1. Start Small
```bash
# Begin with smoke tests
./scripts/run_tests.sh smoke

# Gradually increase load
USERS=10 ./scripts/run_tests.sh basic
USERS=50 ./scripts/run_tests.sh basic  
USERS=100 ./scripts/run_tests.sh volume
```

#### 2. Monitor Resources
- Watch Datadog dashboard during tests
- Monitor database connections and query performance
- Check system resources (CPU, memory, disk I/O)
- Observe application logs for errors

#### 3. Test Different Scenarios
```bash
# Test normal operations
./scripts/run_tests.sh realistic

# Test error handling  
./scripts/run_tests.sh failures

# Test high load
./scripts/run_tests.sh volume

# Test sustained load
./scripts/run_tests.sh endurance
```

### Debugging & Troubleshooting

#### Common Issues
1. **Connection Refused**: Ensure Payment Service is running
2. **Authentication Errors**: Check AUTH_TOKEN configuration
3. **High Error Rates**: Review service logs and reduce load
4. **Docker Issues**: Verify network connectivity between containers

#### Debug Mode
```bash
# Run with verbose logging
locust -f locustfile.py --host=http://localhost:8000 --loglevel=DEBUG

# Check container logs
docker-compose logs payment-service
docker-compose logs datadog-agent
```

## 📋 Test Checklist

### Pre-Test
- [ ] Payment Service is healthy (`curl http://localhost:8000/health`)
- [ ] Database is responsive
- [ ] Datadog agent is collecting metrics
- [ ] MockServer is running for banking tests
- [ ] Test configuration is appropriate for environment

### During Test
- [ ] Monitor Locust UI for error rates
- [ ] Watch Datadog dashboard for system metrics
- [ ] Check application logs for errors
- [ ] Verify database performance remains stable

### Post-Test
- [ ] Review generated HTML reports
- [ ] Analyze Datadog metrics and trends
- [ ] Document any performance issues found
- [ ] Clean up test data if necessary

## 🚦 Performance Baselines

### Expected Performance (Local Development)
- **Payment Processing**: >100 RPS with <500ms response time
- **Database Queries**: <100ms average query time  
- **Error Rate**: <5% under normal load
- **Memory Usage**: <2GB for full stack
- **CPU Usage**: <80% during peak load

### Scaling Targets
- **Production**: >1000 RPS sustained
- **Peak Load**: >5000 RPS for 5 minutes
- **Availability**: 99.9% uptime
- **Response Time**: 95th percentile <1000ms

This load testing suite provides comprehensive coverage for validating the performance, reliability, and scalability of the Payment Service ecosystem. Use it regularly to ensure your service can handle production traffic loads and maintain SLA requirements.