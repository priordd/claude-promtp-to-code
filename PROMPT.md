# Payment Processing Service Generator Prompt

Generate a modern, production-ready payment processing microservice with the following specifications:

## **Core Architecture**
Create a Python FastAPI-based payment processing service with:
- **Framework**: FastAPI with Pydantic models for request/response validation
- **Database**: PostgreSQL with psycopg2 for connection management
- **Caching**: In-memory caching with threading locks (no Redis dependency)
- **Containerization**: Docker with docker-compose for development environment
- **Testing**: Comprehensive test suite with pytest and automated API testing scripts
- **package manager**: uv package manager
- **python version**: latest

## **Technical Requirements**

### **Database Schema**
Design PostgreSQL schema with:
- **Transactions table**: Core payment records with JSONB metadata
- **Refunds table**: Refund tracking linked to transactions
- **Proper indexing**: On transaction_id, merchant_id, status, timestamps
- **JSONB serialization**: Properly handle Python dictionaries → JSON for database storage

### **API Endpoints**
Implement REST APIs for:
- `POST /api/v1/payments/process` - Process new payments
- `GET /api/v1/payments/{transaction_id}` - Get payment status
- `POST /api/v1/payments/{transaction_id}/refund` - Process refunds
- `GET /health` - Health check endpoint

### **Payment Processing Flow**
1. **Request validation** with Pydantic models
2. **Security checks** including merchant validation
3. **Card data encryption** handling (simulate with encrypted fields)
4. **Authorization** with external payment networks (mocked)
5. **Transaction persistence** with proper ACID properties
6. **Event publishing** to message queues
7. **Audit logging** for compliance

### **Error Handling**
- Comprehensive exception handling with custom error types
- Proper HTTP status codes and error responses
- Database transaction rollback on failures
- Structured logging with correlation IDs

## **Infrastructure Components**

### **Docker Compose Services**
Include these services in docker-compose.yml:
- **Application service**: Python FastAPI app
- **PostgreSQL**: Database with initialization scripts
- **Kafka + Zookeeper**: Message queuing (with health checks)
- **Mock services**: Banking API simulator using MockServer
- **Monitoring**: Datadog agent for APM, logs, and database monitoring

### **Configuration Management**
- Environment-based configuration with dotenv
- Separate configs for development/production
- Database connection pooling
- Proper secret management (no hardcoded credentials)

### **Monitoring & Observability**
Integrate comprehensive monitoring:
- **APM**: Datadog APM with distributed tracing spans
- **Database Monitoring**: PostgreSQL performance monitoring
- **Data Streams Monitoring**: Kafka message flow tracking
- **Health checks**: Container and service health validation
- **Structured logging**: JSON logs with correlation tracking

## **Development Workflow**

### **Build System**
- **uv** for fast dependency management
- **Makefile** with common development tasks:
  - `make docker-up` - Start all services
  - `make test-api` - Run API integration tests
  - `make docker-logs` - View service logs
  - `make docker-down` - Stop services

### **Testing Strategy**
- **Unit tests**: Test individual components in isolation
- **Integration tests**: Test service interactions
- **API tests**: Automated bash script testing full workflows
- **Test fixtures**: Realistic test data with proper factories
- **Coverage reporting**: Ensure high test coverage

### **Git Workflow**
Follow this commit history pattern:
1. Initial FastAPI application setup
2. Docker configuration for development environment
3. Database schema and data access layer
4. Core payment processing logic
5. API endpoints and controllers
6. Monitoring and observability integration
7. Test suite and automation
8. Documentation and deployment guides

## **Security Considerations**
- **Input validation**: Strict Pydantic models with field validation
- **Authentication**: Bearer token authentication (configurable)
- **Encryption**: Encrypted card data fields (simulated)
- **Audit logging**: Complete audit trail for all operations
- **Environment isolation**: Proper secrets management
- **Database security**: Parameterized queries to prevent SQL injection

## **Performance & Reliability**
- **Connection pooling**: Database connection management
- **Async operations**: Use async/await where appropriate
- **Circuit breakers**: For external service calls
- **Retry logic**: With exponential backoff
- **Health checks**: Deep health validation
- **Graceful shutdown**: Proper cleanup on service termination

## **Code Quality Standards**
- **Type hints**: Full type annotation throughout
- **Documentation**: Comprehensive docstrings
- **Code organization**: Clear separation of concerns
- **Error handling**: Consistent exception patterns
- **Logging**: Structured logging with appropriate levels
- **Configuration**: Environment-based configuration

## **Specific Implementation Notes**

### **Critical Implementation Details**
1. **JSONB Serialization**: Always use `json.dumps()` when inserting Python dictionaries into PostgreSQL JSONB columns with psycopg2
2. **Volume Mounts**: Avoid mounting source code directories in docker-compose to prevent build cache issues
3. **Cache Management**: Implement thread-safe in-memory caching with proper TTL handling
4. **Event Publishing**: Handle Kafka connection failures gracefully with retry logic
5. **Database Transactions**: Use proper transaction management with rollback on errors

### **Testing Requirements**
- Create a comprehensive `test_api.sh` script that tests:
  - Health checks
  - Payment processing (including failures)
  - Status retrieval
  - Refund processing
  - Authentication validation
  - Error scenarios
  - Performance testing

### **Monitoring Integration**
- Configure Datadog agent with:
  - PostgreSQL database monitoring
  - Kafka data streams monitoring
  - APM with custom spans
  - Log collection with proper parsing
  - Custom metrics for business KPIs

## **Expected Deliverables**
1. **Complete microservice** with all components functional
2. **Docker environment** that starts with single command
3. **API documentation** with OpenAPI/Swagger
4. **Test suite** with high coverage
5. **Monitoring dashboards** configuration
6. **Deployment documentation** with setup instructions
7. **Git repository** with clean commit history

## **Quality Gates**
- All API tests must pass (`make test-api` succeeds)
- Database operations handle edge cases properly
- Service starts cleanly in Docker environment
- Health checks validate all dependencies
- Error scenarios return appropriate responses
- Monitoring integration collects metrics successfully

Generate this project with realistic payment processing logic, proper error handling, comprehensive testing, and production-ready monitoring. The service should demonstrate modern microservice patterns while maintaining simplicity and reliability.

## **C4 architectural diagrams**
- based on the created project create the c4 diagrams as code and add it to the docs