"""Database connection management with connection pooling."""

import json
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional, AsyncGenerator
import psycopg2
import psycopg2.extras
import psycopg2.pool
import structlog

from payment_service.config import settings


class DatabaseManager:
    """Manages database connections with connection pooling."""

    def __init__(self):
        self.pool: Optional[psycopg2.pool.ThreadedConnectionPool] = None
        self.logger = structlog.get_logger(__name__)

    async def initialize(self) -> None:
        """Initialize the database connection pool."""
        try:
            self.pool = psycopg2.pool.ThreadedConnectionPool(
                minconn=1,
                maxconn=settings.database_pool_size,
                dsn=settings.database_url,
                cursor_factory=psycopg2.extras.RealDictCursor,
            )
            self.logger.info("Database connection pool initialized")
        except Exception as e:
            self.logger.error("Failed to initialize database pool", error=str(e))
            raise

    async def close(self) -> None:
        """Close all database connections."""
        if self.pool:
            self.pool.closeall()
            self.logger.info("Database connections closed")

    @asynccontextmanager
    async def get_connection(self) -> AsyncGenerator[psycopg2.extensions.connection, None]:
        """Get a database connection from the pool."""
        if not self.pool:
            raise RuntimeError("Database pool not initialized")

        conn = None
        try:
            conn = self.pool.getconn()
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            self.logger.error("Database connection error", error=str(e))
            raise
        finally:
            if conn:
                self.pool.putconn(conn)

    async def execute_query(
        self,
        query: str,
        params: Optional[tuple] = None,
        fetch_one: bool = False,
        fetch_all: bool = False,
    ) -> Any:
        """Execute a database query with connection pooling."""
        async with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, params)

                if fetch_one:
                    return cursor.fetchone()
                elif fetch_all:
                    return cursor.fetchall()
                else:
                    conn.commit()
                    return cursor.rowcount

    async def execute_transaction(self, operations: List[tuple]) -> None:
        """Execute multiple operations in a single transaction."""
        async with self.get_connection() as conn:
            try:
                with conn.cursor() as cursor:
                    for query, params in operations:
                        cursor.execute(query, params)
                    conn.commit()
            except Exception as e:
                conn.rollback()
                self.logger.error("Transaction failed", error=str(e))
                raise

    async def health_check(self) -> bool:
        """Check database connectivity."""
        try:
            result = await self.execute_query("SELECT 1", fetch_one=True)
            return result is not None
        except Exception as e:
            self.logger.error("Database health check failed", error=str(e))
            return False


# Global database manager instance
database_manager = DatabaseManager()


def serialize_json(data: Dict[str, Any]) -> str:
    """Serialize Python dict to JSON string for JSONB storage."""
    return json.dumps(data, default=str)


def deserialize_json(data: str) -> Dict[str, Any]:
    """Deserialize JSON string to Python dict."""
    if not data:
        return {}
    return json.loads(data)
