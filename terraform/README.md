# Payment Service Datadog Dashboard - Terraform

This Terraform configuration creates a comprehensive Datadog dashboard for monitoring the Payment Service with business metrics, database performance, and system health.

## 📊 Dashboard Features

### Business Metrics
- **Payment Volume by Status** - Track payment transactions by status (captured, failed, pending)
- **Total Payment Amount** - Sum of all payment amounts in the last hour
- **Average Payment Amount** - Average transaction value
- **Payment Success Rate** - Percentage of successful payments

### Refund Metrics
- **Refund Volume by Status** - Track refund requests by status
- **Total Refund Amount** - Sum of all refunds processed
- **Average Refund Amount** - Average refund value

### Database Performance
- **Database Table Operations** - Insert, update, delete operations by table
- **Database Table Sizes** - Live tuples count per table
- **Dead Tuples** - Tables needing cleanup/vacuum
- **PostgreSQL System Metrics** - Connections, query performance, database size

### Application Performance
- **Request Rate & Response Time** - API performance metrics
- **Error Rate** - Application error tracking
- **Service Health Score** - Overall service reliability percentage

### System Resources
- **CPU Usage** - System CPU utilization
- **Memory Usage** - System memory consumption

## 🚀 Prerequisites

1. **Terraform** >= 1.0 installed
2. **Datadog Account** with API and Application keys
3. **Payment Service** running with DBM configured

## 📋 Setup Instructions

### 1. Configure Datadog Keys

```bash
# Copy the example variables file
cp terraform.tfvars.example terraform.tfvars

# Edit with your actual Datadog keys
vi terraform.tfvars
```

Set the following variables:
```hcl
datadog_api_key = "your_actual_api_key"
datadog_app_key = "your_actual_app_key"
datadog_api_url = "https://api.datadoghq.com/"  # or your Datadog site URL
environment = "development"  # or production, staging, etc.
service_name = "payment-service"
```

### 2. Initialize Terraform

```bash
cd terraform/
terraform init
```

### 3. Plan the Deployment

```bash
terraform plan
```

### 4. Apply the Configuration

```bash
terraform apply
```

### 5. Access the Dashboard

After successful deployment, the dashboard URL will be displayed:
```
dashboard_url = "https://app.datadoghq.com/dashboard/abc-123-def"
```

## 🔧 Customization

### Environment Variables
- `environment` - Environment name (development, staging, production)
- `service_name` - Service identifier for metric filtering
- `datadog_api_url` - Datadog site URL (US: datadoghq.com, EU: datadoghq.eu)

### Adding Custom Metrics
To add new custom metrics to the dashboard:

1. Update the PostgreSQL configuration in `conf.d/postgres.yaml`
2. Add new widget definitions in `main.tf`
3. Run `terraform plan` and `terraform apply`

### Metric Filters
All metrics are automatically filtered by:
- `env:${var.environment}`
- `service:${var.service_name}`
- `database:payment_db`

## 📈 Available Metrics

### Custom Payment Metrics (from PostgreSQL)
```
payment.service.count
payment.service.avg_amount
payment.service.total_amount
payment.refunds.count
payment.refunds.avg_amount
payment.refunds.total_amount
payment.database.inserts
payment.database.updates
payment.database.deletes
payment.database.live_tuples
payment.database.dead_tuples
```

### PostgreSQL System Metrics
```
postgresql.connections
postgresql.queries_per_second
postgresql.avg_query_time
postgresql.database_size
```

### Application Metrics (via Datadog APM)
```
trace.web.request.hits
trace.web.request.duration
trace.web.request.errors
```

### System Metrics
```
system.cpu.user
system.mem.used
```

## 🚨 Alerts & Thresholds

The dashboard includes visual indicators for:
- **Payment Success Rate** < 95% (Red alert)
- **Dead Tuples** > 1000 (Cleanup needed)
- **Service Health Score** < 95% (Performance issue)
- **Total Refunds** > $5000 (High refund volume)

## 🔄 Updates and Maintenance

### Updating the Dashboard
```bash
# Make changes to main.tf
terraform plan
terraform apply
```

### Destroying the Dashboard
```bash
terraform destroy
```

### Version Updates
Update the Datadog provider version in `versions.tf` as needed.

## 🔐 Security

- **API Keys**: Store in environment variables or use Terraform Cloud/Enterprise
- **State File**: Use remote state storage (S3, Terraform Cloud) for production
- **Access Control**: Limit Terraform execution to authorized personnel

## 📝 Troubleshooting

### Common Issues

1. **Invalid API Key**
   ```
   Error: 403 Forbidden
   ```
   - Verify your `datadog_api_key` and `datadog_app_key`

2. **No Data in Dashboard**
   - Ensure Payment Service is running
   - Verify DBM setup is complete
   - Check metric names match the configuration

3. **Permission Issues**
   ```
   Error: 403 Forbidden: insufficient privileges
   ```
   - Ensure your Datadog keys have dashboard creation permissions

### Validation
```bash
# Check if metrics are flowing
curl -H "DD-API-KEY: ${DD_API_KEY}" \
     "https://api.datadoghq.com/api/v1/metrics?from=$(date -d '1 hour ago' +%s)"
```

## 📚 Additional Resources

- [Datadog Terraform Provider Documentation](https://registry.terraform.io/providers/DataDog/datadog/latest/docs)
- [Datadog Dashboard API](https://docs.datadoghq.com/api/latest/dashboards/)
- [Payment Service Database Monitoring Guide](../docs/DATABASE_MONITORING.md)