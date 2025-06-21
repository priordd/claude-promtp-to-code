"""Configuration management for the payment service."""

from typing import Optional
from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    # Database Configuration
    database_url: str = "postgresql://payment_user:payment_password@localhost:5432/payment_db"
    database_pool_size: int = 10
    database_max_overflow: int = 20

    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_workers: int = 1
    debug: bool = False

    # Security
    secret_key: str = "development-secret-key"
    encryption_key: str = "development-encryption-key"
    auth_token_expiry: int = 3600

    # External Services
    banking_api_url: str = "http://localhost:1080"
    banking_api_timeout: int = 30

    # Event Configuration
    event_logging_enabled: bool = True

    # Datadog Configuration
    dd_api_key: Optional[str] = None
    dd_app_key: Optional[str] = None
    dd_service: str = "payment-service"
    dd_env: str = "dev"
    dd_version: str = "0.1.0"
    dd_trace_enabled: bool = True
    dd_logs_enabled: bool = True
    dd_profiling_enabled: bool = True

    # Monitoring
    health_check_timeout: int = 5
    metrics_enabled: bool = True

    # Cache Configuration
    cache_ttl: int = 300
    cache_max_size: int = 1000

    model_config = ConfigDict(env_file=".env", case_sensitive=False)


# Global settings instance
settings = Settings()
