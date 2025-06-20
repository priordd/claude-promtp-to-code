# Payment Service Makefile
# Provides common development tasks for the payment service

.PHONY: help install dev test lint format docker-build docker-up docker-down docker-logs test-api clean terraform-init terraform-plan terraform-apply terraform-destroy

# Variables
PYTHON := python3
UV := uv
DOCKER_COMPOSE := docker-compose
SERVICE_NAME := payment-service

# Default target
help: ## Show this help message
	@echo "Payment Service Development Commands"
	@echo "===================================="
	@echo ""
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# Development setup
venv: ## Create virtual environment with uv
	@echo "Creating virtual environment..."
	$(UV) venv --python 3.12

install: ## Install dependencies with uv
	@echo "Installing dependencies..."
	$(UV) sync --dev

dev: venv install ## Setup development environment
	@echo "Setting up development environment..."
	@if [ ! -f .env ]; then cp .env.example .env; echo "Created .env file from template"; fi
	@echo "Development environment ready!"

add-dep: ## Add a new dependency (usage: make add-dep PACKAGE=package-name)
	@if [ -z "$(PACKAGE)" ]; then echo "Usage: make add-dep PACKAGE=package-name"; exit 1; fi
	@echo "Adding dependency: $(PACKAGE)"
	$(UV) add $(PACKAGE)

add-dev-dep: ## Add a new dev dependency (usage: make add-dev-dep PACKAGE=package-name)
	@if [ -z "$(PACKAGE)" ]; then echo "Usage: make add-dev-dep PACKAGE=package-name"; exit 1; fi
	@echo "Adding dev dependency: $(PACKAGE)"
	$(UV) add --dev $(PACKAGE)

# Code quality
lint: ## Run code linting
	@echo "Running linting..."
	$(UV) run ruff check src/ tests/
	$(UV) run mypy src/

format: ## Format code
	@echo "Formatting code..."
	$(UV) run black src/ tests/
	$(UV) run ruff check --fix src/ tests/

# Testing
test: ## Run unit and integration tests
	@echo "Running tests..."
	PYTHONPATH=src DD_TRACE_ENABLED=false $(UV) run pytest tests/ -v --cov=src --cov-report=term-missing --cov-report=html

test-unit: ## Run only unit tests
	@echo "Running unit tests..."
	PYTHONPATH=src DD_TRACE_ENABLED=false $(UV) run pytest tests/unit/ -v

test-integration: ## Run only integration tests
	@echo "Running integration tests..."
	PYTHONPATH=src DD_TRACE_ENABLED=false $(UV) run pytest tests/integration/ -v

test-api: ## Run API tests against running service
	@echo "Running API tests..."
	@if [ ! -x ./scripts/test_api.sh ]; then chmod +x ./scripts/test_api.sh; fi
	./scripts/test_api.sh

# Docker operations
docker-build: ## Build Docker image
	@echo "Building Docker image..."
	docker build -t $(SERVICE_NAME) .

docker-up: ## Start all services with docker-compose
	@echo "Starting services..."
	$(DOCKER_COMPOSE) up -d
	@echo "Services started. Use 'make docker-logs' to view logs."
	@echo "API will be available at http://localhost:8000"
	@echo "Use 'make test-api' to run API tests."

docker-down: ## Stop all services
	@echo "Stopping services..."
	$(DOCKER_COMPOSE) down

docker-restart: ## Restart all services
	@echo "Restarting services..."
	$(DOCKER_COMPOSE) restart

docker-logs: ## View service logs
	@echo "Viewing logs (Press Ctrl+C to exit)..."
	$(DOCKER_COMPOSE) logs -f

docker-logs-service: ## View logs for payment service only
	@echo "Viewing payment service logs..."
	$(DOCKER_COMPOSE) logs -f payment-service

docker-shell: ## Open shell in payment service container
	@echo "Opening shell in payment service container..."
	$(DOCKER_COMPOSE) exec payment-service /bin/bash

docker-psql: ## Open PostgreSQL shell
	@echo "Opening PostgreSQL shell..."
	$(DOCKER_COMPOSE) exec postgres psql -U payment_user -d payment_db

# Database operations
db-migrate: ## Run database migrations (placeholder)
	@echo "Running database migrations..."
	@echo "Note: Migrations are currently handled by init_db.sql in docker-compose"

db-seed: ## Seed database with test data
	@echo "Seeding database with test data..."
	$(DOCKER_COMPOSE) exec postgres psql -U payment_user -d payment_db -f /docker-entrypoint-initdb.d/01-init_db.sql

db-setup-dbm: ## Setup Datadog Database Monitoring
	@echo "Setting up Datadog Database Monitoring..."
	$(DOCKER_COMPOSE) exec postgres psql -U postgres -d payment_db -f /docker-entrypoint-initdb.d/02-setup_dbm.sql

db-test-dbm: ## Test DBM connection and permissions
	@echo "Testing DBM user connection..."
	$(DOCKER_COMPOSE) exec postgres psql -U datadog -d payment_db -c "SELECT current_user, session_user;"
	@echo "Testing pg_stat_statements extension..."
	$(DOCKER_COMPOSE) exec postgres psql -U datadog -d payment_db -c "SELECT count(*) FROM pg_stat_statements LIMIT 1;"
	@echo "Testing table access..."
	$(DOCKER_COMPOSE) exec postgres psql -U datadog -d payment_db -c "SELECT count(*) FROM pg_stat_user_tables;"

db-dbm-metrics: ## Show current DBM metrics
	@echo "Current database metrics:"
	@echo "========================"
	$(DOCKER_COMPOSE) exec postgres psql -U datadog -d payment_db -c "SELECT schemaname, relname as tablename, n_tup_ins, n_tup_upd, n_tup_del, n_live_tup FROM pg_stat_user_tables;"
	@echo ""
	@echo "Query statistics (top 5 by calls):"
	@echo "=================================="
	$(DOCKER_COMPOSE) exec postgres psql -U datadog -d payment_db -c "SELECT query, calls, total_exec_time, mean_exec_time FROM pg_stat_statements ORDER BY calls DESC LIMIT 5;"

# Development workflow
run-local: ## Run service locally (without Docker)
	@echo "Running service locally..."
	@echo "Make sure PostgreSQL and Kafka are running (use docker-compose up postgres kafka zookeeper)"
	$(UV) run uvicorn payment_service.main:app --host 0.0.0.0 --port 8000 --reload

dev-setup: docker-up ## Complete development setup
	@echo "Waiting for services to be ready..."
	@sleep 10
	@echo "Running initial tests..."
	$(MAKE) test-api
	@echo ""
	@echo "Development environment is ready!"
	@echo "- API: http://localhost:8000"
	@echo "- Health: http://localhost:8000/health"
	@echo "- Docs: http://localhost:8000/docs"

# Monitoring and debugging
status: ## Check service status
	@echo "Checking service status..."
	@curl -s http://localhost:8000/health | jq . || echo "Service not responding"

metrics: ## View service metrics (placeholder)
	@echo "Service metrics:"
	@curl -s http://localhost:8000/health | jq '.services' || echo "Service not responding"

# Cleanup
clean: ## Clean up generated files
	@echo "Cleaning up..."
	rm -rf __pycache__/
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf *.egg-info/
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete

clean-venv: ## Remove virtual environment
	@echo "Removing virtual environment..."
	rm -rf .venv/

clean-all: clean clean-venv ## Clean everything including virtual environment
	@echo "All cleaned up!"

clean-docker: ## Clean up Docker resources
	@echo "Cleaning up Docker resources..."
	$(DOCKER_COMPOSE) down -v --remove-orphans
	docker system prune -f

# Production operations
prod-check: ## Run production readiness checks
	@echo "Running production readiness checks..."
	@echo "1. Linting..."
	$(MAKE) lint
	@echo "2. Testing..."
	$(MAKE) test
	@echo "3. Building Docker image..."
	$(MAKE) docker-build
	@echo "4. Security check..."
	@echo "Note: Add security scanning tools here"
	@echo "Production readiness check complete!"

deploy-staging: ## Deploy to staging environment (placeholder)
	@echo "Deploying to staging environment..."
	@echo "Note: Add staging deployment commands here"

deploy-prod: ## Deploy to production environment (placeholder)
	@echo "Deploying to production environment..."
	@echo "Note: Add production deployment commands here"

# Documentation
docs: ## Generate and serve documentation
	@echo "Generating documentation..."
	@echo "API documentation available at: http://localhost:8000/docs (when service is running)"

diagrams: ## Generate C4 diagrams as PNG images
	@echo "Generating C4 diagrams..."
	@if [ ! -x ./scripts/generate_diagrams.sh ]; then chmod +x ./scripts/generate_diagrams.sh; fi
	./scripts/generate_diagrams.sh

diagrams-clean: ## Clean and regenerate all diagrams
	@echo "Cleaning and regenerating diagrams..."
	@if [ ! -x ./scripts/generate_diagrams.sh ]; then chmod +x ./scripts/generate_diagrams.sh; fi
	./scripts/generate_diagrams.sh --clean

# Utility targets
env-check: ## Check environment variables
	@echo "Environment Configuration:"
	@echo "========================="
	@if [ -f .env ]; then \
		echo "✓ .env file exists"; \
		grep -E "^[A-Z_]+" .env | head -10 || true; \
	else \
		echo "✗ .env file missing (run 'make dev' to create)"; \
	fi

deps-check: ## Check if dependencies are installed
	@echo "Dependency Check:"
	@echo "================="
	@command -v $(UV) >/dev/null 2>&1 && echo "✓ uv installed" || echo "✗ uv not installed"
	@command -v docker >/dev/null 2>&1 && echo "✓ Docker installed" || echo "✗ Docker not installed"
	@command -v $(DOCKER_COMPOSE) >/dev/null 2>&1 && echo "✓ docker-compose installed" || echo "✗ docker-compose not installed"
	@command -v jq >/dev/null 2>&1 && echo "✓ jq installed" || echo "✗ jq not installed"
	@command -v curl >/dev/null 2>&1 && echo "✓ curl installed" || echo "✗ curl not installed"

# Workflow shortcuts
quick-test: docker-up ## Quick development test cycle
	@echo "Running quick test cycle..."
	@sleep 5
	$(MAKE) test-api

full-test: ## Full test suite including Docker rebuild
	@echo "Running full test suite..."
	$(MAKE) clean
	$(MAKE) docker-build
	$(MAKE) docker-up
	@sleep 10
	$(MAKE) test
	$(MAKE) test-api

# Performance testing
perf-test: ## Run performance tests (placeholder)
	@echo "Running performance tests..."
	@echo "Note: Add performance testing tools here"

load-test: ## Run load tests (placeholder)
	@echo "Running load tests..."
	@echo "Note: Add load testing tools here"

# Security
security-scan: ## Run security scans (placeholder)
	@echo "Running security scans..."
	@echo "Note: Add security scanning tools here"

# Version management
version: ## Show current version
	@echo "Payment Service Version:"
	@grep version pyproject.toml | head -1

# Development helpers
debug: ## Show debug information
	@echo "Debug Information:"
	@echo "=================="
	@echo "Python version: $$(python --version)"
	@echo "Current directory: $$(pwd)"
	@echo "Git branch: $$(git branch --show-current 2>/dev/null || echo 'Not a git repository')"
	@echo "Docker status: $$(docker info >/dev/null 2>&1 && echo 'Running' || echo 'Not running')"
	@echo "Services status:"
	@$(DOCKER_COMPOSE) ps 2>/dev/null || echo "No services running"

# Terraform operations for Datadog dashboard
terraform-init: ## Initialize Terraform for Datadog dashboard
	@echo "Initializing Terraform..."
	@cd terraform && terraform init

terraform-plan: ## Plan Terraform deployment for Datadog dashboard
	@echo "Planning Terraform deployment..."
	@if [ ! -f terraform/terraform.tfvars ]; then \
		echo "❌ terraform.tfvars not found. Copy terraform.tfvars.example and update with your Datadog keys."; \
		exit 1; \
	fi
	@cd terraform && terraform plan

terraform-apply: ## Apply Terraform to create Datadog dashboard
	@echo "Applying Terraform configuration..."
	@if [ ! -f terraform/terraform.tfvars ]; then \
		echo "❌ terraform.tfvars not found. Copy terraform.tfvars.example and update with your Datadog keys."; \
		exit 1; \
	fi
	@cd terraform && terraform apply
	@echo "✅ Datadog dashboard created successfully!"

terraform-destroy: ## Destroy Datadog dashboard
	@echo "Destroying Datadog dashboard..."
	@cd terraform && terraform destroy

terraform-output: ## Show Terraform outputs (dashboard URL)
	@echo "Terraform outputs:"
	@cd terraform && terraform output

terraform-setup: ## Complete Terraform setup for Datadog dashboard
	@echo "Setting up Datadog dashboard with Terraform..."
	@if [ ! -f terraform/terraform.tfvars ]; then \
		echo "📋 Creating terraform.tfvars from example..."; \
		cp terraform/terraform.tfvars.example terraform/terraform.tfvars; \
		echo "✅ Created terraform/terraform.tfvars"; \
		echo "⚠️  Please edit terraform/terraform.tfvars with your actual Datadog API and App keys"; \
		echo "   You can find these at: https://app.datadoghq.com/organization-settings/api-keys"; \
		echo ""; \
		echo "After updating the keys, run:"; \
		echo "  make terraform-init"; \
		echo "  make terraform-apply"; \
	else \
		echo "✅ terraform.tfvars already exists"; \
		echo "Run 'make terraform-init && make terraform-apply' to deploy"; \
	fi

# Load testing with Locust
load-test: ## Run basic load test with Locust
	@echo "Running basic load test..."
	@cd load-testing && $(UV) run locust -f locustfile.py --host=http://localhost:8000 --users=10 --spawn-rate=2 --run-time=60s --headless --html=reports/basic-report.html --csv=reports/basic-results

load-test-ui: ## Run load test with Locust web UI
	@echo "Starting Locust web UI..."
	@echo "Open http://localhost:8089 in your browser"
	@cd load-testing && $(UV) run locust -f locustfile.py --host=http://localhost:8000

load-test-smoke: ## Run quick smoke test
	@echo "Running smoke test..."
	@cd load-testing && $(UV) run locust -f locustfile.py --users=5 --spawn-rate=1 --run-time=30s --headless --html=reports/smoke-report.html

load-test-volume: ## Run high-volume load test
	@echo "Running high-volume test..."
	@cd load-testing && $(UV) run locust -f locustfile.py --host=http://localhost:8000 --users=100 --spawn-rate=10 --run-time=300s --headless --html=reports/volume-report.html --csv=reports/volume-results

load-test-banking: ## Run banking API load test
	@echo "Running banking API test..."
	@cd load-testing && $(UV) run locust -f locustfile.py --host=http://localhost:1080 --users=20 --spawn-rate=2 --run-time=120s --headless --html=reports/banking-report.html --csv=reports/banking-results

load-test-failures: ## Run failure simulation test
	@echo "Running failure simulation test..."
	@cd load-testing && $(UV) run locust -f locustfile.py --host=http://localhost:8000 --users=15 --spawn-rate=2 --run-time=90s --headless --html=reports/failures-report.html --csv=reports/failures-results

load-test-docker: ## Run distributed load test with Docker
	@echo "Starting distributed load test with Docker..."
	@cd load-testing && docker-compose -f docker-compose.locust.yml up --build

load-test-stop: ## Stop Docker load test containers
	@echo "Stopping load test containers..."
	@cd load-testing && docker-compose -f docker-compose.locust.yml down --remove-orphans

load-test-reports: ## Open latest load test reports
	@echo "Opening load test reports..."
	@if [ -f load-testing/reports/smoke-report.html ]; then \
		open load-testing/reports/smoke-report.html || xdg-open load-testing/reports/smoke-report.html || echo "Report: load-testing/reports/smoke-report.html"; \
	elif [ -f load-testing/reports/basic-report.html ]; then \
		open load-testing/reports/basic-report.html || xdg-open load-testing/reports/basic-report.html || echo "Report: load-testing/reports/basic-report.html"; \
	else \
		echo "No reports found. Run a load test first."; \
	fi

load-test-clean: ## Clean load test reports
	@echo "Cleaning load test reports..."
	@rm -rf load-testing/reports/*
	@echo "Reports cleaned."

load-test-install: ## Install load testing dependencies (already included in UV dev dependencies)
	@echo "Load testing dependencies are included in dev dependencies."
	@echo "Run 'uv sync --dev' to install all development dependencies including Locust."

# Authentication token generation
generate-auth-tokens: ## Generate test authentication tokens
	@echo "Generating authentication tokens..."
	@$(UV) run python scripts/generate_auth_tokens.py --save-env --curl-examples

generate-auth-simple: ## Generate simple test token
	@echo "Generating simple auth token..."
	@$(UV) run python scripts/generate_auth_tokens.py --type simple --count 1

generate-auth-jwt: ## Generate JWT-like token
	@echo "Generating JWT-like token..."
	@$(UV) run python scripts/generate_auth_tokens.py --type jwt --count 1

test-auth: ## Test authentication with generated token
	@echo "Testing authentication..."
	@if [ -f test_tokens.env ]; then \
		source test_tokens.env && curl -s -X GET http://localhost:8000/health \
		-H "Authorization: $$AUTH_TOKEN" | jq . || echo "Service not responding"; \
	else \
		echo "No tokens found. Run 'make generate-auth-tokens' first."; \
	fi

curl-examples: ## Show curl command examples with valid tokens
	@echo "📋 Curl Examples:"
	@if [ -f test_tokens.env ]; then \
		echo "Using tokens from test_tokens.env"; \
		$(UV) run python scripts/generate_auth_tokens.py --curl-examples; \
	else \
		echo "No tokens found. Run 'make generate-auth-tokens' first."; \
	fi