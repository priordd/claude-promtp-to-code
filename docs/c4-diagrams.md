# C4 Architecture Diagrams

This document contains C4 model diagrams for the Payment Processing Service, providing different levels of architectural detail.

## C1 - System Context Diagram

```mermaid
graph TB
    Customer[Customer<br/>Person using payment system]
    Merchant[Merchant<br/>Business accepting payments]
    
    PaymentService[Payment Processing Service<br/>Handles payment transactions, refunds, and status tracking]
    
    BankingAPI[Banking API<br/>External payment processor]
    DatadogAPI[Datadog<br/>Monitoring and observability]
    
    Customer -->|Makes payments| PaymentService
    Merchant -->|Processes payments<br/>Views transactions<br/>Initiates refunds| PaymentService
    
    PaymentService -->|Authorizes & captures payments<br/>Processes refunds| BankingAPI
    PaymentService -->|Sends metrics, traces, logs| DatadogAPI
    
    classDef person fill:#08427b,stroke:#052e56,stroke-width:2px,color:#fff
    classDef system fill:#1168bd,stroke:#0b4884,stroke-width:2px,color:#fff
    classDef external fill:#999999,stroke:#666666,stroke-width:2px,color:#fff
    
    class Customer,Merchant person
    class PaymentService system
    class BankingAPI,DatadogAPI external
```

## C2 - Container Diagram

```mermaid
graph TB
    subgraph "Payment Processing System"
        WebApp[FastAPI Web Application<br/>Python, FastAPI<br/>Handles HTTP requests, authentication,<br/>payment processing logic]
        
        Database[PostgreSQL Database<br/>Stores transactions, refunds,<br/>audit logs, encrypted card data]
        
        MessageBus[Kafka Message Bus<br/>Event streaming for<br/>payment events and audit trail]
        
        Cache[In-Memory Cache<br/>Python threading<br/>Caches payment status<br/>and session data]
    end
    
    Customer[Customer]
    Merchant[Merchant]
    BankingAPI[Banking API<br/>External Service]
    MockServer[MockServer<br/>Banking API Simulator]
    DatadogAgent[Datadog Agent<br/>Monitoring Container]
    
    Customer -->|HTTPS/JSON| WebApp
    Merchant -->|HTTPS/JSON| WebApp
    
    WebApp -->|SQL queries<br/>ACID transactions| Database
    WebApp -->|Publishes events| MessageBus
    WebApp -->|Get/Set cached data| Cache
    WebApp -->|HTTP requests<br/>Payment operations| BankingAPI
    WebApp -->|HTTP requests<br/>Development/Testing| MockServer
    WebApp -->|Sends traces, metrics| DatadogAgent
    
    classDef person fill:#08427b,stroke:#052e56,stroke-width:2px,color:#fff
    classDef container fill:#1168bd,stroke:#0b4884,stroke-width:2px,color:#fff
    classDef database fill:#2e7d32,stroke:#1b5e20,stroke-width:2px,color:#fff
    classDef external fill:#999999,stroke:#666666,stroke-width:2px,color:#fff
    
    class Customer,Merchant person
    class WebApp,Cache container
    class Database,MessageBus database
    class BankingAPI,MockServer,DatadogAgent external
```

## C3 - Component Diagram (Web Application)

```mermaid
graph TB
    subgraph "FastAPI Web Application"
        subgraph "API Layer"
            PaymentController[Payment Controller<br/>Handles payment processing<br/>endpoints and validation]
            StatusController[Status Controller<br/>Handles payment status<br/>and lookup endpoints]
            RefundController[Refund Controller<br/>Handles refund processing<br/>and management]
            HealthController[Health Controller<br/>System health checks<br/>and diagnostics]
        end
        
        subgraph "Service Layer"
            PaymentService[Payment Service<br/>Core payment processing<br/>business logic]
            BankingService[Banking Service<br/>External payment API<br/>integration]
            EventService[Event Service<br/>Kafka event publishing<br/>and management]
            EncryptionService[Encryption Service<br/>Card data encryption<br/>and security]
            CacheService[Cache Service<br/>In-memory caching<br/>with TTL support]
        end
        
        subgraph "Data Layer"
            DatabaseManager[Database Manager<br/>Connection pooling<br/>and query execution]
            Models[Pydantic Models<br/>Request/response validation<br/>and serialization]
        end
        
        subgraph "Utils"
            Monitoring[Monitoring Utils<br/>Datadog integration<br/>and metrics]
            Security[Security Utils<br/>Authentication and<br/>authorization]
            Logging[Logging Utils<br/>Structured logging<br/>and correlation]
        end
    end
    
    External[External Systems]
    Database[PostgreSQL]
    Kafka[Kafka]
    Cache[Memory Cache]
    
    PaymentController -->|Uses| PaymentService
    StatusController -->|Uses| PaymentService
    RefundController -->|Uses| PaymentService
    HealthController -->|Uses| PaymentService
    HealthController -->|Uses| BankingService
    
    PaymentService -->|Uses| BankingService
    PaymentService -->|Uses| EventService
    PaymentService -->|Uses| EncryptionService
    PaymentService -->|Uses| CacheService
    PaymentService -->|Uses| DatabaseManager
    
    BankingService -->|HTTP requests| External
    EventService -->|Publishes events| Kafka
    DatabaseManager -->|SQL queries| Database
    CacheService -->|Read/Write| Cache
    
    PaymentController -->|Uses| Models
    StatusController -->|Uses| Models
    RefundController -->|Uses| Models
    
    PaymentService -->|Uses| Monitoring
    PaymentController -->|Uses| Security
    PaymentService -->|Uses| Logging
    
    classDef controller fill:#1976d2,stroke:#0d47a1,stroke-width:2px,color:#fff
    classDef service fill:#388e3c,stroke:#1b5e20,stroke-width:2px,color:#fff
    classDef data fill:#f57c00,stroke:#e65100,stroke-width:2px,color:#fff
    classDef utils fill:#7b1fa2,stroke:#4a148c,stroke-width:2px,color:#fff
    classDef external fill:#999999,stroke:#666666,stroke-width:2px,color:#fff
    
    class PaymentController,StatusController,RefundController,HealthController controller
    class PaymentService,BankingService,EventService,EncryptionService,CacheService service
    class DatabaseManager,Models data
    class Monitoring,Security,Logging utils
    class External,Database,Kafka,Cache external
```

## C4 - Code Diagram (Payment Service)

```mermaid
graph TB
    subgraph "Payment Service Component"
        subgraph "Public Interface"
            ProcessPayment[process_payment()<br/>async def]
            GetStatus[get_payment_status()<br/>async def]
            ProcessRefund[process_refund()<br/>async def]
        end
        
        subgraph "Private Methods"
            ValidateMerchant[_validate_merchant()<br/>async def]
            CreateTransaction[_create_transaction()<br/>async def]
            AuthorizePayment[_authorize_payment()<br/>async def]
            CapturePayment[_capture_payment()<br/>async def]
            UpdateStatus[_update_transaction_status()<br/>async def]
            PublishEvent[_publish_payment_event()<br/>async def]
            CreateAuditLog[_create_audit_log()<br/>async def]
        end
        
        subgraph "Dependencies"
            BankingServiceDep[banking_service<br/>BankingService]
            EventServiceDep[event_service<br/>EventService]
            EncryptionServiceDep[encryption_service<br/>EncryptionService]
            CacheServiceDep[cache_service<br/>CacheService]
        end
        
        subgraph "Models"
            PaymentRequest[PaymentRequest<br/>Pydantic Model]
            PaymentResponse[PaymentResponse<br/>Pydantic Model]
            RefundRequest[RefundRequest<br/>Pydantic Model]
            RefundResponse[RefundResponse<br/>Pydantic Model]
        end
    end
    
    subgraph "External Dependencies"
        DatabaseManager[database_manager<br/>Global instance]
        MonitoringUtils[monitoring utils<br/>create_span, increment_counter]
        Logger[structlog logger<br/>Structured logging]
    end
    
    ProcessPayment -->|calls| ValidateMerchant
    ProcessPayment -->|calls| CreateTransaction
    ProcessPayment -->|calls| AuthorizePayment
    ProcessPayment -->|calls| CapturePayment
    ProcessPayment -->|calls| UpdateStatus
    ProcessPayment -->|calls| PublishEvent
    ProcessPayment -->|calls| CreateAuditLog
    
    ProcessPayment -->|uses| BankingServiceDep
    ProcessPayment -->|uses| EncryptionServiceDep
    ProcessPayment -->|uses| EventServiceDep
    ProcessPayment -->|uses| CacheServiceDep
    
    GetStatus -->|uses| CacheServiceDep
    GetStatus -->|uses| DatabaseManager
    
    ProcessRefund -->|calls| AuthorizePayment
    ProcessRefund -->|calls| PublishEvent
    ProcessRefund -->|calls| CreateAuditLog
    
    ProcessPayment -->|accepts| PaymentRequest
    ProcessPayment -->|returns| PaymentResponse
    ProcessRefund -->|accepts| RefundRequest
    ProcessRefund -->|returns| RefundResponse
    
    ProcessPayment -->|uses| MonitoringUtils
    ProcessPayment -->|uses| Logger
    
    classDef public fill:#1976d2,stroke:#0d47a1,stroke-width:2px,color:#fff
    classDef private fill:#388e3c,stroke:#1b5e20,stroke-width:2px,color:#fff
    classDef dependency fill:#f57c00,stroke:#e65100,stroke-width:2px,color:#fff
    classDef model fill:#7b1fa2,stroke:#4a148c,stroke-width:2px,color:#fff
    classDef external fill:#999999,stroke:#666666,stroke-width:2px,color:#fff
    
    class ProcessPayment,GetStatus,ProcessRefund public
    class ValidateMerchant,CreateTransaction,AuthorizePayment,CapturePayment,UpdateStatus,PublishEvent,CreateAuditLog private
    class BankingServiceDep,EventServiceDep,EncryptionServiceDep,CacheServiceDep dependency
    class PaymentRequest,PaymentResponse,RefundRequest,RefundResponse model
    class DatabaseManager,MonitoringUtils,Logger external
```

## Deployment Diagram

```mermaid
graph TB
    subgraph "Development Environment (Docker Compose)"
        subgraph "Application Tier"
            AppContainer[payment-service<br/>FastAPI Application<br/>Port: 8000]
        end
        
        subgraph "Data Tier"
            PostgresContainer[postgres<br/>PostgreSQL 16<br/>Port: 5432]
            KafkaContainer[kafka<br/>Apache Kafka<br/>Port: 9092]
            ZookeeperContainer[zookeeper<br/>Kafka Coordination<br/>Port: 2181]
        end
        
        subgraph "External Services"
            MockServerContainer[mockserver<br/>Banking API Mock<br/>Port: 1080]
            DatadogContainer[datadog-agent<br/>Monitoring Agent<br/>Port: 8126]
        end
        
        subgraph "Volumes"
            PostgresData[(postgres_data<br/>Persistent Storage)]
        end
    end
    
    Developer[Developer<br/>Local Machine]
    
    Developer -->|HTTP requests| AppContainer
    AppContainer -->|SQL queries| PostgresContainer
    AppContainer -->|Events| KafkaContainer
    AppContainer -->|HTTP requests| MockServerContainer
    AppContainer -->|Metrics/Traces| DatadogContainer
    
    PostgresContainer -->|Data persistence| PostgresData
    KafkaContainer -->|Coordination| ZookeeperContainer
    
    classDef app fill:#1976d2,stroke:#0d47a1,stroke-width:2px,color:#fff
    classDef data fill:#388e3c,stroke:#1b5e20,stroke-width:2px,color:#fff
    classDef external fill:#f57c00,stroke:#e65100,stroke-width:2px,color:#fff
    classDef storage fill:#7b1fa2,stroke:#4a148c,stroke-width:2px,color:#fff
    classDef person fill:#08427b,stroke:#052e56,stroke-width:2px,color:#fff
    
    class AppContainer app
    class PostgresContainer,KafkaContainer,ZookeeperContainer data
    class MockServerContainer,DatadogContainer external
    class PostgresData storage
    class Developer person
```

## Data Flow Diagram

```mermaid
sequenceDiagram
    participant Client
    participant API as FastAPI App
    participant PaymentService
    participant BankingAPI
    participant Database
    participant Kafka
    participant Cache
    participant Datadog
    
    Client->>API: POST /api/v1/payments/process
    API->>API: Validate auth token
    API->>PaymentService: process_payment()
    
    PaymentService->>PaymentService: validate_merchant()
    PaymentService->>Database: create_transaction()
    PaymentService->>BankingAPI: authorize_payment()
    BankingAPI-->>PaymentService: authorization_result
    
    PaymentService->>Database: update_authorization()
    PaymentService->>BankingAPI: capture_payment()
    BankingAPI-->>PaymentService: capture_result
    
    PaymentService->>Database: update_capture()
    PaymentService->>Kafka: publish_event()
    PaymentService->>Database: create_audit_log()
    PaymentService->>Cache: cache_status()
    PaymentService->>Datadog: send_metrics()
    
    PaymentService-->>API: PaymentResponse
    API-->>Client: HTTP 200 + response
    
    Note over Client,Datadog: All operations include correlation ID for tracing
```

## Security Architecture

```mermaid
graph TB
    subgraph "Security Layers"
        subgraph "Transport Security"
            HTTPS[HTTPS/TLS<br/>Encrypted communication]
            AuthHeaders[Authorization Headers<br/>Bearer token authentication]
        end
        
        subgraph "Application Security"
            InputValidation[Input Validation<br/>Pydantic models<br/>Field constraints]
            Authentication[Authentication<br/>Token validation<br/>User identification]
            Authorization[Authorization<br/>Resource access control]
        end
        
        subgraph "Data Security"
            CardEncryption[Card Data Encryption<br/>AES encryption<br/>Secure key management]
            DatabaseSecurity[Database Security<br/>Parameterized queries<br/>Connection pooling]
            AuditLogging[Audit Logging<br/>Complete event trail<br/>Compliance tracking]
        end
        
        subgraph "Infrastructure Security"
            ContainerSecurity[Container Security<br/>Non-root user<br/>Minimal attack surface]
            NetworkSecurity[Network Security<br/>Internal communication<br/>Service isolation]
            SecretManagement[Secret Management<br/>Environment variables<br/>No hardcoded secrets]
        end
    end
    
    Request[Incoming Request] -->|1| HTTPS
    HTTPS -->|2| AuthHeaders
    AuthHeaders -->|3| InputValidation
    InputValidation -->|4| Authentication
    Authentication -->|5| Authorization
    Authorization -->|6| CardEncryption
    CardEncryption -->|7| DatabaseSecurity
    DatabaseSecurity -->|8| AuditLogging
    
    classDef transport fill:#1976d2,stroke:#0d47a1,stroke-width:2px,color:#fff
    classDef application fill:#388e3c,stroke:#1b5e20,stroke-width:2px,color:#fff
    classDef data fill:#f57c00,stroke:#e65100,stroke-width:2px,color:#fff
    classDef infrastructure fill:#7b1fa2,stroke:#4a148c,stroke-width:2px,color:#fff
    classDef flow fill:#999999,stroke:#666666,stroke-width:2px,color:#fff
    
    class HTTPS,AuthHeaders transport
    class InputValidation,Authentication,Authorization application
    class CardEncryption,DatabaseSecurity,AuditLogging data
    class ContainerSecurity,NetworkSecurity,SecretManagement infrastructure
    class Request flow
```

## Monitoring and Observability

```mermaid
graph TB
    subgraph "Payment Service"
        Application[FastAPI Application<br/>Instrumented with<br/>Datadog tracing]
    end
    
    subgraph "Observability Stack"
        subgraph "Metrics"
            BusinessMetrics[Business Metrics<br/>• Payment success rate<br/>• Transaction volume<br/>• Processing time]
            SystemMetrics[System Metrics<br/>• HTTP response times<br/>• Database queries<br/>• Memory usage]
        end
        
        subgraph "Tracing"
            APMTraces[APM Traces<br/>• Request flow<br/>• Service dependencies<br/>• Performance bottlenecks]
            CustomSpans[Custom Spans<br/>• Payment processing<br/>• Database operations<br/>• External API calls]
        end
        
        subgraph "Logging"
            StructuredLogs[Structured Logs<br/>• JSON format<br/>• Correlation IDs<br/>• Security events]
            AuditTrail[Audit Trail<br/>• Payment events<br/>• State changes<br/>• Compliance logs]
        end
        
        subgraph "Alerting"
            HealthChecks[Health Checks<br/>• Service availability<br/>• Database connectivity<br/>• External services]
            Dashboards[Dashboards<br/>• Real-time monitoring<br/>• Business KPIs<br/>• System health]
        end
    end
    
    Application -->|Sends| BusinessMetrics
    Application -->|Sends| SystemMetrics
    Application -->|Creates| APMTraces
    Application -->|Creates| CustomSpans
    Application -->|Emits| StructuredLogs
    Application -->|Records| AuditTrail
    Application -->|Provides| HealthChecks
    
    BusinessMetrics -->|Displayed in| Dashboards
    SystemMetrics -->|Displayed in| Dashboards
    APMTraces -->|Visualized in| Dashboards
    HealthChecks -->|Monitored in| Dashboards
    
    classDef app fill:#1976d2,stroke:#0d47a1,stroke-width:2px,color:#fff
    classDef metrics fill:#388e3c,stroke:#1b5e20,stroke-width:2px,color:#fff
    classDef tracing fill:#f57c00,stroke:#e65100,stroke-width:2px,color:#fff
    classDef logging fill:#7b1fa2,stroke:#4a148c,stroke-width:2px,color:#fff
    classDef alerting fill:#d32f2f,stroke:#b71c1c,stroke-width:2px,color:#fff
    
    class Application app
    class BusinessMetrics,SystemMetrics metrics
    class APMTraces,CustomSpans tracing
    class StructuredLogs,AuditTrail logging
    class HealthChecks,Dashboards alerting
```

---

These C4 diagrams provide a comprehensive view of the Payment Processing Service architecture at different levels of detail, from the high-level system context down to specific component implementations. Each diagram serves a different audience and purpose:

- **C1 (Context)**: For business stakeholders and project managers
- **C2 (Containers)**: For solution architects and DevOps teams
- **C3 (Components)**: For software architects and senior developers
- **C4 (Code)**: For developers working on specific components

The additional diagrams (Deployment, Data Flow, Security, Monitoring) provide specialized views for operations, security, and observability concerns.