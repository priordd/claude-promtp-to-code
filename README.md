# Payment Processing Service

A production-ready payment processing microservice built with FastAPI, PostgreSQL, and comprehensive monitoring.

## Features

- 🚀 **FastAPI** - Modern, fast web framework with automatic API documentation
- 🗄️ **PostgreSQL** - Robust database with JSONB support for metadata
- 🔒 **Security** - Card data encryption, authentication, and audit logging
- 📊 **Monitoring** - Comprehensive Datadog integration with APM and metrics
- 🧪 **Testing** - Extensive test suite with unit, integration, and API tests
- 🐳 **Docker** - Complete containerized development environment
- ⚡ **Performance** - Connection pooling, caching, and async operations
- 🔄 **Reliability** - Retry logic, circuit breakers, and graceful error handling

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.12+ (for local development)
- `make` command
- `curl` and `jq` (for API testing)


### Fast track

```bash
# Clone the repository and navigate to the service directory and cd into it
cp .env.example .env ## add DD_API_KEY and DD_APP_KEY values
make full-test ## install everything and run tests
make clean-all ## cleanup everything
```


### Start the Service

```bash
# Clone the repository and navigate to the service directory
cd payment-service

# Start all services (API, PostgreSQL, Kafka, etc.)
make docker-up

# Wait for services to be ready and run API tests
make test-api
```

The service will be available at:
- **API**: http://localhost:8000
- **Health Check**: http://localhost:8000/health
- **API Documentation**: http://localhost:8000/docs

### Development Setup

```bash
# Complete development setup
make dev-setup

# Or step by step:
make dev           # Setup local environment
make docker-up     # Start services
make test-api      # Verify everything works
```

## API Endpoints

### Process Payment
```bash
POST /api/v1/payments/process
Authorization: Bearer <token>
Content-Type: application/json

{
  "merchant_id": "merchant_123",
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
  "description": "Test payment",
  "metadata": {"order_id": "12345"}
}
```

### Get Payment Status
```bash
GET /api/v1/payments/{transaction_id}
Authorization: Bearer <token>
```

### Process Refund
```bash
POST /api/v1/payments/{transaction_id}/refund
Authorization: Bearer <token>
Content-Type: application/json

{
  "amount": 50.00,
  "reason": "Customer request",
  "metadata": {"support_ticket": "67890"}
}
```

### Health Check
```bash
GET /health
```

## Development Commands

```bash
# View all available commands
make help

# Development
make dev           # Setup development environment
make run-local     # Run service locally (without Docker)
make test          # Run all tests
make lint          # Run code linting
make format        # Format code

# Docker operations
make docker-up     # Start all services
make docker-down   # Stop all services
make docker-logs   # View logs
make docker-shell  # Open shell in service container

# Testing
make test-api      # Run API tests
make test-unit     # Run unit tests
make test-integration  # Run integration tests

# Database
make docker-psql   # Open PostgreSQL shell
make db-seed       # Seed database with test data

# Monitoring
make status        # Check service status
make metrics       # View service metrics
```

## Architecture

### System Components

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   FastAPI App   │    │   PostgreSQL    │    │      Kafka      │
│                 │────│                 │    │                 │
│ • Payment API   │    │ • Transactions  │    │ • Event Stream  │
│ • Health Check  │    │ • Refunds       │    │ • Audit Trail   │
│ • Monitoring    │    │ • Audit Logs    │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   MockServer    │    │   Datadog       │    │    Redis        │
│                 │    │                 │    │   (Cache)       │
│ • Banking API   │    │ • APM Traces    │    │ • Session Data  │
│ • Test Data     │    │ • Metrics       │    │ • Rate Limits   │
│                 │    │ • Logs          │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Database Schema

**Transactions Table**
- Core payment records with JSONB metadata
- Proper indexing on transaction_id, merchant_id, status
- Encrypted card data storage

**Refunds Table**
- Refund tracking linked to transactions
- Support for partial and full refunds

**Audit Logs Table**
- Complete audit trail for compliance
- Event-based logging with correlation IDs

### Security Features

- **Card Data Encryption**: AES encryption for sensitive card information
- **Authentication**: Bearer token authentication
- **Input Validation**: Strict Pydantic models with field validation
- **Audit Logging**: Complete audit trail for all operations
- **SQL Injection Prevention**: Parameterized queries

## Configuration

### Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
# Database
DATABASE_URL=postgresql://payment_user:payment_password@localhost:5432/payment_db

# API
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=true

# Security
SECRET_KEY=your-secret-key-here
ENCRYPTION_KEY=your-encryption-key-here

# External Services
BANKING_API_URL=http://localhost:1080

# Kafka
KAFKA_BOOTSTRAP_SERVERS=localhost:9092

# Datadog (optional)
DD_API_KEY=your-datadog-api-key
DD_TRACE_ENABLED=true
```

## Testing

### Test Coverage

- **Unit Tests**: Service layer, models, utilities
- **Integration Tests**: API endpoints, database operations
- **API Tests**: End-to-end workflow testing

```bash
# Run all tests
make test

# Run specific test types
make test-unit
make test-integration
make test-api

# Run with coverage report
pytest --cov=src --cov-report=html
```

### Test Data

The service includes realistic test data:
- Valid credit card numbers (test cards)
- Declined card numbers for error testing
- Sample merchant and transaction data

## Monitoring

### Datadog Integration

- **APM**: Distributed tracing with custom spans
- **Metrics**: Business and system metrics
- **Logs**: Structured JSON logging
- **Database Monitoring**: PostgreSQL performance
- **Data Streams**: Kafka message flow

### Health Checks

The `/health` endpoint provides comprehensive health status:
- Database connectivity
- External service availability
- Application status

### Metrics

Custom metrics include:
- Payment processing rates
- Success/failure ratios
- Response times
- Business KPIs

## Deployment

### Production Checklist

```bash
# Run production readiness checks
make prod-check

# This includes:
# - Code linting
# - Full test suite
# - Security scanning
# - Docker image build
```

### Environment Setup

1. **Staging**: `make deploy-staging`
2. **Production**: `make deploy-prod`

### Scaling Considerations

- **Database**: Read replicas for status queries
- **Caching**: Redis for session and rate limiting
- **Load Balancing**: Multiple API instances
- **Message Queues**: Kafka partitioning

## Troubleshooting

### Common Issues

**Service won't start**
```bash
make docker-logs        # Check service logs
make status            # Check service status
make deps-check        # Verify dependencies
```

**Database connection issues**
```bash
make docker-psql       # Test database connectivity
make db-seed          # Reset database
```

**API tests failing**
```bash
make docker-up         # Ensure services are running
sleep 10              # Wait for services to be ready
make test-api         # Re-run tests
```

### Debug Information

```bash
make debug            # Show debug information
make env-check        # Check environment configuration
```

## Contributing

1. Follow the existing code style (Black, Ruff)
2. Write tests for new features
3. Update documentation
4. Run `make prod-check` before submitting

### Code Quality

```bash
make lint             # Check code quality
make format           # Auto-format code
make test             # Run test suite
```

## License

This project is licensed under the MIT License.

## Support

For questions or issues:
1. Check the troubleshooting section
2. Review the API documentation at `/docs`
3. Check the health endpoint at `/health`
4. Review service logs with `make docker-logs`