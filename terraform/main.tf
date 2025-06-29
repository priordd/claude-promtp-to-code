# Terraform configuration is defined in versions.tf

# Configure the Datadog Provider
provider "datadog" {
  api_key = var.datadog_api_key
  app_key = var.datadog_app_key
  api_url = var.datadog_api_url
}

# Variables
variable "datadog_api_key" {
  description = "Datadog API Key"
  type        = string
  sensitive   = true
}

variable "datadog_app_key" {
  description = "Datadog Application Key"
  type        = string
  sensitive   = true
}

variable "datadog_api_url" {
  description = "Datadog API URL"
  type        = string
  default     = "https://api.datadoghq.com/"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "dev"
}

variable "service_name" {
  description = "Service name"
  type        = string
  default     = "payment-service"
}

# Payment Service Dashboard
resource "datadog_dashboard" "payment_service_dashboard" {
  title       = "Payment Service - ${title(var.environment)}"
  description = "Comprehensive monitoring dashboard for Payment Service including business metrics, database performance, and system health"
  layout_type = "ordered"

  # Business Metrics Section
  widget {
    group_definition {
      title            = "💳 Payment Business Metrics"
      layout_type      = "ordered"
      background_color = "blue"

      widget {
        timeseries_definition {
          title       = "Payment Volume by Status"
          title_size  = "16"
          title_align = "left"
          show_legend = true
          legend_layout = "auto"
          legend_columns = ["value"]

          request {
            q = "sum:payment.service.count{env:${var.environment},service:${var.service_name}} by {status}"
            display_type = "line"
            style {
              palette    = "dog_classic"
              line_type  = "solid"
              line_width = "normal"
            }
          }

          yaxis {
            label = "Payments per Minute"
            scale = "linear"
            min   = "0"
          }
        }
      }

      widget {
        query_value_definition {
          title       = "Total Payment Amount (1h)"
          title_size  = "16"
          title_align = "left"
          autoscale   = true
          precision   = 2
          timeseries_background {
            type = "bars"
            yaxis {
              min = "0"
            }
          }

          request {
            q = "sum:payment.service.total_amount{env:${var.environment},service:${var.service_name}}"
            aggregator = "last"
            conditional_formats {
              comparator = ">"
              value      = 10000
              palette    = "green_on_white"
            }
            conditional_formats {
              comparator = "<"
              value      = 1000
              palette    = "yellow_on_white"
            }
          }
        }
      }

      widget {
        query_value_definition {
          title       = "Average Payment Amount"
          title_size  = "16"
          title_align = "left"
          autoscale   = true
          precision   = 2
          timeseries_background {
            type = "bars"
            yaxis {
              min = "0"
            }
          }

          request {
            q = "avg:payment.service.avg_amount{env:${var.environment},service:${var.service_name}}"
            aggregator = "last"
          }
        }
      }

      widget {
        timeseries_definition {
          title       = "Payment Success Rate"
          title_size  = "16"
          title_align = "left"
          show_legend = true

          request {
            q = "(sum:payment.service.count{env:${var.environment},service:${var.service_name},status:captured} / sum:payment.service.count{env:${var.environment},service:${var.service_name}}) * 100"
            display_type = "line"
            style {
              palette    = "green"
              line_type  = "solid"
              line_width = "thick"
            }
          }

          yaxis {
            label = "Success Rate (%)"
            scale = "linear"
            min   = "0"
            max   = "100"
          }
        }
      }


    }
  }

  # Refunds Section
  widget {
    group_definition {
      title            = "↩️ Refund Metrics"
      layout_type      = "ordered"
      background_color = "orange"

      widget {
        timeseries_definition {
          title       = "Refund Volume by Status"
          title_size  = "16"
          title_align = "left"
          show_legend = true

          request {
            q = "sum:payment.refunds.count{env:${var.environment},service:${var.service_name}} by {status}"
            display_type = "bars"
            style {
              palette    = "orange"
              line_type  = "solid"
              line_width = "normal"
            }
          }

          yaxis {
            label = "Count"
            scale = "linear"
            min   = "0"
          }
        }
      }

      widget {
        query_value_definition {
          title       = "Total Refund Amount (1h)"
          title_size  = "16"
          title_align = "left"
          autoscale   = true
          precision   = 2
          timeseries_background {
            type = "bars"
            yaxis {
              min = "0"
            }
          }

          request {
            q = "sum:payment.refunds.total_amount{env:${var.environment},service:${var.service_name}}"
            aggregator = "last"
            conditional_formats {
              comparator = ">"
              value      = 5000
              palette    = "red_on_white"
            }
          }
        }
      }

      widget {
        query_value_definition {
          title       = "Average Refund Amount"
          title_size  = "16"
          title_align = "left"
          autoscale   = true
          precision   = 2
          timeseries_background {
            type = "bars"
            yaxis {
              min = "0"
            }
          }

          request {
            q = "avg:payment.refunds.avg_amount{env:${var.environment},service:${var.service_name}}"
            aggregator = "last"
          }
        }
      }
    }
  }

  # Database Performance Section
  widget {
    group_definition {
      title            = "🗃️ Database Performance"
      layout_type      = "ordered"
      background_color = "purple"

      widget {
        timeseries_definition {
          title       = "Database Table Operations"
          title_size  = "16"
          title_align = "left"
          show_legend = true

          request {
            q = "sum:payment.database.inserts{env:${var.environment},service:${var.service_name}} by {tablename}"
            display_type = "line"
            style {
              palette    = "cool"
              line_type  = "solid"
              line_width = "normal"
            }
          }

          request {
            q = "sum:payment.database.updates{env:${var.environment},service:${var.service_name}} by {tablename}"
            display_type = "line"
            style {
              palette    = "warm"
              line_type  = "solid"
              line_width = "normal"
            }
          }

          request {
            q = "sum:payment.database.deletes{env:${var.environment},service:${var.service_name}} by {tablename}"
            display_type = "line"
            style {
              palette    = "red"
              line_type  = "solid"
              line_width = "normal"
            }
          }

          yaxis {
            label = "Operations"
            scale = "linear"
            min   = "0"
          }
        }
      }

      widget {
        timeseries_definition {
          title       = "Database Table Sizes"
          title_size  = "16"
          title_align = "left"
          show_legend = true

          request {
            q = "avg:payment.database.live_tuples{env:${var.environment},service:${var.service_name}} by {tablename}"
            display_type = "area"
            style {
              palette    = "purple"
              line_type  = "solid"
              line_width = "normal"
            }
          }

          yaxis {
            label = "Live Tuples"
            scale = "linear"
            min   = "0"
          }
        }
      }

      widget {
        query_value_definition {
          title       = "Dead Tuples (Cleanup Needed)"
          title_size  = "16"
          title_align = "left"
          autoscale   = true
          timeseries_background {
            type = "bars"
            yaxis {
              min = "0"
            }
          }

          request {
            q = "sum:payment.database.dead_tuples{env:${var.environment},service:${var.service_name}}"
            aggregator = "last"
            conditional_formats {
              comparator = ">"
              value      = 1000
              palette    = "red_on_white"
            }
            conditional_formats {
              comparator = "<"
              value      = 100
              palette    = "green_on_white"
            }
          }
        }
      }
    }
  }

  # PostgreSQL System Metrics
  widget {
    group_definition {
      title            = "🐘 PostgreSQL System Metrics"
      layout_type      = "ordered"
      background_color = "gray"

      widget {
        timeseries_definition {
          title       = "Database Connections"
          title_size  = "16"
          title_align = "left"
          show_legend = true

          request {
            q = "avg:postgresql.connections{env:${var.environment},database:payment_db}"
            display_type = "line"
            style {
              palette    = "dog_classic"
              line_type  = "solid"
              line_width = "normal"
            }
          }

          yaxis {
            label = "Connections"
            scale = "linear"
            min   = "0"
          }
        }
      }

      widget {
        timeseries_definition {
          title       = "Query Performance"
          title_size  = "16"
          title_align = "left"
          show_legend = true

          request {
            q = "avg:postgresql.queries_per_second{env:${var.environment},database:payment_db}"
            display_type = "line"
            style {
              palette    = "green"
              line_type  = "solid"
              line_width = "normal"
            }
          }

          request {
            q = "avg:postgresql.avg_query_time{env:${var.environment},database:payment_db}"
            display_type = "line"
            style {
              palette    = "orange"
              line_type  = "solid"
              line_width = "normal"
            }
          }

          yaxis {
            label = "QPS / Avg Time (ms)"
            scale = "linear"
            min   = "0"
          }
        }
      }

      widget {
        timeseries_definition {
          title       = "Database Size"
          title_size  = "16"
          title_align = "left"
          show_legend = true

          request {
            q = "avg:postgresql.database_size{env:${var.environment},database:payment_db}"
            display_type = "area"
            style {
              palette    = "purple"
              line_type  = "solid"
              line_width = "normal"
            }
          }

          yaxis {
            label = "Size (bytes)"
            scale = "linear"
            min   = "0"
          }
        }
      }
    }
  }

  # Application Performance Section
  widget {
    group_definition {
      title            = "🚀 Application Performance"
      layout_type      = "ordered"
      background_color = "green"

      widget {
        timeseries_definition {
          title       = "FastAPI Request Rate & Response Time"
          title_size  = "16"
          title_align = "left"
          show_legend = true

          request {
            q = "sum:trace.fastapi.request.hits{env:${var.environment},service:${var.service_name},span.kind:server}.as_rate()"
            display_type = "line"
            style {
              palette    = "blue"
              line_type  = "solid"
              line_width = "normal"
            }
          }

          request {
            q = "avg:trace.fastapi.request.duration{env:${var.environment},service:${var.service_name},span.kind:server}"
            display_type = "line"
            style {
              palette    = "orange"
              line_type  = "solid"
              line_width = "normal"
            }
          }

          yaxis {
            label = "RPS / Duration (ms)"
            scale = "linear"
            min   = "0"
          }
        }
      }

      widget {
        timeseries_definition {
          title       = "Application-Level Metrics"
          title_size  = "16"
          title_align = "left"
          show_legend = true

          request {
            q = "sum:payment.processed{env:${var.environment}}.as_rate()"
            display_type = "line"
            style {
              palette    = "green"
              line_type  = "solid"
              line_width = "normal"
            }
          }

          request {
            q = "sum:refund.processed{env:${var.environment}}.as_rate()"
            display_type = "line"
            style {
              palette    = "orange"
              line_type  = "solid"
              line_width = "normal"
            }
          }

          yaxis {
            label = "Operations/sec"
            scale = "linear"
            min   = "0"
          }
        }
      }

      widget {
        timeseries_definition {
          title       = "FastAPI Error Rate"
          title_size  = "16"
          title_align = "left"
          show_legend = true

          request {
            q = "sum:trace.fastapi.request.errors{env:${var.environment},service:${var.service_name},span.kind:server}.as_rate()"
            display_type = "line"
            style {
              palette    = "red"
              line_type  = "solid"
              line_width = "thick"
            }
          }

          yaxis {
            label = "Errors/sec"
            scale = "linear"
            min   = "0"
          }
        }
      }

      widget {
        query_value_definition {
          title       = "Service Health Score"
          title_size  = "16"
          title_align = "left"
          autoscale   = true
          precision   = 1
          timeseries_background {
            type = "bars"
            yaxis {
              min = "0"
              max = "100"
            }
          }

          request {
            q = "((sum:trace.fastapi.request.hits{env:${var.environment},service:${var.service_name},span.kind:server} - sum:trace.fastapi.request.errors{env:${var.environment},service:${var.service_name},span.kind:server}) / sum:trace.fastapi.request.hits{env:${var.environment},service:${var.service_name},span.kind:server}) * 100"
            aggregator = "last"
            conditional_formats {
              comparator = ">"
              value      = 99
              palette    = "green_on_white"
            }
            conditional_formats {
              comparator = "<"
              value      = 95
              palette    = "red_on_white"
            }
          }
        }
      }

      widget {
        timeseries_definition {
          title       = "Database Pool & Cache Metrics"
          title_size  = "16"
          title_align = "left"
          show_legend = true

          request {
            q = "avg:payment.database.pool.size{env:${var.environment},service:${var.service_name}}"
            display_type = "line"
            style {
              palette    = "purple"
              line_type  = "solid"
              line_width = "normal"
            }
          }

          request {
            q = "avg:payment.cache.max_size{env:${var.environment},service:${var.service_name}}"
            display_type = "line"
            style {
              palette    = "blue"
              line_type  = "solid"
              line_width = "normal"
            }
          }

          yaxis {
            label = "Count"
            scale = "linear"
            min   = "0"
          }
        }
      }
    }
  }

  # Docker Container Resources
  widget {
    group_definition {
      title            = "🐳 Docker Container Resources"
      layout_type      = "ordered"
      background_color = "yellow"

      widget {
        timeseries_definition {
          title       = "Container CPU Usage"
          title_size  = "16"
          title_align = "left"
          show_legend = true

          request {
            q = "avg:docker.cpu.usage{env:${var.environment},service:payment-service}"
            display_type = "line"
            style {
              palette    = "orange"
              line_type  = "solid"
              line_width = "normal"
            }
          }

          yaxis {
            label = "CPU %"
            scale = "linear"
            min   = "0"
            max   = "100"
          }
        }
      }

      widget {
        timeseries_definition {
          title       = "Container Memory Usage"
          title_size  = "16"
          title_align = "left"
          show_legend = true

          request {
            q = "avg:docker.mem.usage{env:${var.environment},service:payment-service}"
            display_type = "line"
            style {
              palette    = "purple"
              line_type  = "solid"
              line_width = "normal"
            }
          }

          request {
            q = "avg:docker.mem.limit{env:${var.environment},service:payment-service}"
            display_type = "line"
            style {
              palette    = "red"
              line_type  = "dashed"
              line_width = "thin"
            }
          }

          yaxis {
            label = "Memory (bytes)"
            scale = "linear"
            min   = "0"
          }
        }
      }

      widget {
        timeseries_definition {
          title       = "Container Network I/O"
          title_size  = "16"
          title_align = "left"
          show_legend = true

          request {
            q = "avg:docker.net.bytes_rcvd{env:${var.environment},service:payment-service}"
            display_type = "line"
            style {
              palette    = "green"
              line_type  = "solid"
              line_width = "normal"
            }
          }

          request {
            q = "avg:docker.net.bytes_sent{env:${var.environment},service:payment-service}"
            display_type = "line"
            style {
              palette    = "blue"
              line_type  = "solid"
              line_width = "normal"
            }
          }

          yaxis {
            label = "Bytes/sec"
            scale = "linear"
            min   = "0"
          }
        }
      }

      widget {
        timeseries_definition {
          title       = "Container Disk I/O"
          title_size  = "16"
          title_align = "left"
          show_legend = true

          request {
            q = "avg:docker.io.read_bytes{env:${var.environment},service:payment-service}"
            display_type = "line"
            style {
              palette    = "warm"
              line_type  = "solid"
              line_width = "normal"
            }
          }

          request {
            q = "avg:docker.io.write_bytes{env:${var.environment},service:payment-service}"
            display_type = "line"
            style {
              palette    = "cool"
              line_type  = "solid"
              line_width = "normal"
            }
          }

          yaxis {
            label = "Bytes/sec"
            scale = "linear"
            min   = "0"
          }
        }
      }

      widget {
        query_value_definition {
          title       = "Container Status"
          title_size  = "16"
          title_align = "left"
          autoscale   = true
          precision   = 0
          timeseries_background {
            type = "bars"
            yaxis {
              min = "0"
              max = "1"
            }
          }

          request {
            q = "avg:docker.containers.running{env:${var.environment},service:payment-service}"
            aggregator = "last"
            conditional_formats {
              comparator = "="
              value      = 1
              palette    = "green_on_white"
            }
            conditional_formats {
              comparator = "<"
              value      = 1
              palette    = "red_on_white"
            }
          }
        }
      }
    }
  }

  # Real-time Alerts Section
  widget {
    note_definition {
      content          = <<-EOF
## 🚨 Key Metrics & Monitoring

**Available Metrics:**
- **API Metrics:** api.payment.success, api.payment.error, api.refund.success
- **Business Metrics:** payment.service.count, payment.service.avg_amount, payment.service.total_amount
- **Database Metrics:** payment.database.{inserts,updates,deletes,live_tuples,dead_tuples}
- **Application Metrics:** payment.processed, refund.processed
- **System Metrics:** postgresql.connections, postgresql.queries_per_second

**Key Thresholds:**
- Payment Success Rate < 95% → Critical Alert
- Dead Tuples > 1000 → Cleanup Needed
- API Error Rate > 5% → Critical Alert
- Database Pool Size Monitoring

**Configuration:**
- Environment: ${var.environment}
- Service: ${var.service_name}
- Dashboard Updates: Every 15 seconds
EOF
      background_color = "gray"
      font_size        = "14"
      text_align       = "left"
      show_tick        = true
      tick_edge        = "left"
      tick_pos         = "50%"
    }
  }

  template_variable {
    name     = "env"
    prefix   = "env"
    defaults = [var.environment]
  }

  template_variable {
    name     = "service"
    prefix   = "service"
    defaults = [var.service_name]
  }
}

# Output the dashboard URL
output "dashboard_url" {
  description = "URL of the created Datadog dashboard"
  value       = datadog_dashboard.payment_service_dashboard.url
}

output "dashboard_id" {
  description = "ID of the created Datadog dashboard"
  value       = datadog_dashboard.payment_service_dashboard.id
}