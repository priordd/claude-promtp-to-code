# Datadog Database Monitoring (DBM) Setup

This document describes how to configure and use Datadog Database Monitoring with PostgreSQL for the Payment Service.

## Overview

Datadog Database Monitoring (DBM) provides deep insights into database performance including:
- Query performance analysis
- Slow query identification
- Database resource utilization
- Lock monitoring
- Connection pool analysis
- Real-time query activity

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  Payment App    │───▶│    PostgreSQL    │◀───│ Datadog Agent   │
│                 │    │                  │    │                 │
│ - Application   │    │ - DBM User       │    │ - DBM Config    │
│ - Query Logs    │    │ - Extensions     │    │ - Metrics       │
│ - Metrics       │    │ - Statistics     │    │ - Query Samples │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │  Datadog Cloud  │
                       │                 │
                       │ - Dashboards    │
                       │ - Query Analysis│
                       │ - Alerts        │
                       └─────────────────┘
```

## Setup Components

### 1. PostgreSQL Configuration

The setup includes optimized PostgreSQL configuration for monitoring:

**File: `scripts/postgresql_custom.conf`**
- Enables `pg_stat_statements` extension
- Configures detailed query logging
- Optimizes performance settings
- Enables connection and lock monitoring

**Key Settings:**
```sql
shared_preload_libraries = 'pg_stat_statements'
log_statement = 'all'
log_duration = on
log_min_duration_statement = 100
track_io_timing = on
```

### 2. Database User and Permissions

**File: `scripts/setup_dbm.sql`**
- Creates dedicated `datadog` user
- Grants necessary permissions for monitoring
- Sets up required extensions

**User Credentials:**
- Username: `datadog`
- Password: `datadog_password`

### 3. Datadog Agent Configuration

**File: `conf.d/postgres.yaml`**
- Configures DBM monitoring
- Sets up custom queries for payment metrics
- Enables deep database monitoring

## Docker Compose Integration

The setup is integrated into `docker-compose.yml`:

```yaml
postgres:
  # Custom configuration
  command: >
    postgres
    -c config_file=/etc/postgresql/postgresql.conf
    -c shared_preload_libraries=pg_stat_statements
  volumes:
    - ./scripts/setup_dbm.sql:/docker-entrypoint-initdb.d/02-setup_dbm.sql
    - ./scripts/postgresql_custom.conf:/etc/postgresql/postgresql.conf

datadog-agent:
  environment:
    - DD_DATABASE_MONITORING_ENABLED=true
    - DD_POSTGRES_ENABLED=true
  volumes:
    - ./conf.d/postgres.yaml:/etc/datadog-agent/conf.d/postgres.d/conf.yaml:ro
```

## Usage

### Quick Start

1. **Start services with DBM:**
   ```bash
   make docker-up
   ```

2. **Test DBM setup:**
   ```bash
   make db-test-dbm
   ```

3. **View current metrics:**
   ```bash
   make db-dbm-metrics
   ```

### Available Commands

| Command | Description |
|---------|-------------|
| `make db-setup-dbm` | Manual DBM setup (usually automatic) |
| `make db-test-dbm` | Test DBM user and permissions |
| `make db-dbm-metrics` | Show current database metrics |
| `make docker-psql` | Open PostgreSQL shell |

### Environment Variables

Set these environment variables for production:

```bash
# Required for Datadog integration
export DD_API_KEY="your-datadog-api-key"

# Optional: Custom database credentials
export POSTGRES_PASSWORD="secure-password"
export DATADOG_DB_PASSWORD="secure-datadog-password"
```

## Monitoring Features

### 1. Query Performance Metrics

- **Query execution time**: Average, min, max execution times
- **Query frequency**: How often queries are executed
- **Query plans**: Execution plan analysis
- **Slow queries**: Queries exceeding threshold (100ms)

### 2. Database Resource Monitoring

- **Connection usage**: Active connections, connection pools
- **Memory usage**: Buffer cache, work memory
- **I/O statistics**: Read/write operations, timing
- **Lock monitoring**: Lock waits, deadlocks

### 3. Custom Payment Service Metrics

The configuration includes custom queries for payment-specific monitoring:

```sql
-- Transaction status monitoring
SELECT status, COUNT(*), AVG(amount), SUM(amount)
FROM transactions 
WHERE created_at > NOW() - INTERVAL '1 hour'
GROUP BY status

-- Refund analytics
SELECT status, COUNT(*), AVG(amount)
FROM refunds 
WHERE created_at > NOW() - INTERVAL '1 hour'
GROUP BY status

-- Table activity monitoring
SELECT tablename, n_tup_ins, n_tup_upd, n_tup_del
FROM pg_stat_user_tables
```

### 4. Real-time Query Activity

- **Active queries**: Currently running queries
- **Query samples**: Representative query executions
- **Query activity**: Historical query patterns

## Datadog Dashboard

Once configured, DBM provides dashboards for:

### Database Overview
- Database connections
- Query throughput
- Response times
- Error rates

### Query Analysis
- Top queries by execution time
- Slow query trends
- Query plan analysis
- Index usage statistics

### Resource Utilization
- CPU usage
- Memory consumption
- Disk I/O
- Network activity

### Payment Service Specific
- Transaction processing rates
- Payment success/failure ratios
- Refund processing metrics
- Database table growth

## Troubleshooting

### Common Issues

1. **DBM user permissions:**
   ```bash
   make db-test-dbm
   ```

2. **Check Datadog agent logs:**
   ```bash
   docker-compose logs datadog-agent
   ```

3. **Verify PostgreSQL configuration:**
   ```bash
   make docker-psql
   # In psql:
   SHOW shared_preload_libraries;
   SELECT * FROM pg_extension WHERE extname = 'pg_stat_statements';
   ```

4. **Test database connectivity:**
   ```bash
   docker-compose exec datadog-agent agent status
   ```

### Performance Tuning

For high-traffic production environments, consider:

1. **Increase query sample collection:**
   ```yaml
   query_samples:
     collection_interval: 0.5  # More frequent sampling
   ```

2. **Optimize PostgreSQL settings:**
   ```sql
   shared_buffers = 512MB      # Increase for more memory
   effective_cache_size = 2GB  # Match available system memory
   ```

3. **Adjust monitoring intervals:**
   ```yaml
   query_metrics:
     collection_interval: 5    # More frequent metrics
   ```

## Security Considerations

1. **Database credentials**: Store securely, rotate regularly
2. **Network access**: Restrict database access to necessary services
3. **Query obfuscation**: Sensitive data in queries is automatically obfuscated
4. **SSL/TLS**: Enable for production environments

## Production Checklist

- [ ] Set real Datadog API key
- [ ] Configure secure database passwords
- [ ] Enable SSL for database connections
- [ ] Set up alerts for critical metrics
- [ ] Configure backup monitoring
- [ ] Set appropriate retention policies
- [ ] Review query sample collection frequency
- [ ] Configure custom dashboards for business metrics

## Further Reading

- [Datadog Database Monitoring Documentation](https://docs.datadoghq.com/database_monitoring/)
- [PostgreSQL Performance Tuning](https://wiki.postgresql.org/wiki/Performance_Optimization)
- [Payment Service Architecture](./ARCHITECTURE.md)