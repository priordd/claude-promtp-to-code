"""Main FastAPI application entry point."""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import structlog

from payment_service.config import settings
from payment_service.api.routes import router
from payment_service.database.connection import database_manager
from payment_service.utils.logging import setup_logging
from payment_service.utils.monitoring import setup_monitoring


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
    
    # Include API routes
    app.include_router(router)
    
    return app


# Application instance
app = create_app()