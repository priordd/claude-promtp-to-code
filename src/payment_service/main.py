"""Main FastAPI application entry point."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import structlog
from datetime import datetime, timezone

from payment_service.config import settings
from payment_service.api.routes import router
from payment_service.database.connection import database_manager
from payment_service.utils.logging import setup_logging
from payment_service.utils.monitoring import setup_monitoring

try:
    from ddtrace import tracer
    DDTRACE_AVAILABLE = True
except ImportError:
    DDTRACE_AVAILABLE = False

# Removed unused imports


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan management."""
    # Startup
    setup_logging()
    setup_monitoring()

    logger = structlog.get_logger(__name__)
    logger.info("Starting payment service", version=settings.dd_version)

    # Initialize database
    await database_manager.initialize()

    yield

    # Shutdown
    logger.info("Shutting down payment service")
    await database_manager.close()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="Payment Processing Service",
        description="A production-ready payment processing microservice",
        version=settings.dd_version,
        debug=settings.debug,
        lifespan=lifespan,
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if settings.debug else [],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Add trace correlation middleware
    @app.middleware("http")
    async def trace_correlation_middleware(request: Request, call_next):
        """Middleware to ensure proper trace correlation in logs."""
        # Get trace context if available
        if DDTRACE_AVAILABLE:
            span = tracer.current_span()
            if span:
                # Add trace context to structlog context
                structlog.contextvars.clear_contextvars()
                structlog.contextvars.bind_contextvars(
                    trace_id=str(span.trace_id),
                    span_id=str(span.span_id),
                    service=settings.dd_service,
                    version=settings.dd_version,
                    env=settings.dd_env,
                )
        
        response = await call_next(request)
        
        # Clear context after request
        if DDTRACE_AVAILABLE:
            structlog.contextvars.clear_contextvars()
        
        return response

    # Include API routes
    app.include_router(router)

    # Add error handlers
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        """Handle HTTP exceptions."""
        logger = structlog.get_logger(__name__)
        logger.warning(
            "HTTP exception",
            status_code=exc.status_code,
            detail=exc.detail,
        )

        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": f"HTTP_{exc.status_code}",
                "message": exc.detail,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """Handle general exceptions."""
        logger = structlog.get_logger(__name__)
        logger.error(
            "Unhandled exception",
            error=str(exc),
            error_type=type(exc).__name__,
        )

        return JSONResponse(
            status_code=500,
            content={
                "error": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )

    return app


# Application instance
app = create_app()
