FROM python:3.12-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install uv

# Set work directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml ./

# Install dependencies (without editable mode for Docker)
RUN uv pip install --system fastapi[standard] pydantic pydantic-settings psycopg2-binary python-dotenv structlog ddtrace cryptography httpx tenacity uvicorn

# Copy application code
COPY src/ ./src/
COPY scripts/ ./scripts/

# Add src to Python path
ENV PYTHONPATH=/app/src

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser
RUN chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["uvicorn", "payment_service.main:app", "--host", "0.0.0.0", "--port", "8000"]