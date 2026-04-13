"""
GENESIS Connection Pool
Centralized psycopg2 ThreadedConnectionPool to prevent PG database saturation
under high concurrent HTTP / Websocket loads on the Fastapi ingress.
"""
import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

_pool = None


def get_db_pool():
    """Initializes and returns the shared ThreadedConnectionPool."""
    global _pool
    if _pool is None:
        db_url = os.environ.get("DATABASE_URL")
        if db_url:
            try:
                from psycopg2 import pool
                # 1 min connection, max 20 concurrent connections
                _pool = pool.ThreadedConnectionPool(1, 20, dsn=db_url)
                logger.info("[DB POOL] ThreadedConnectionPool successfully initialized.")
            except Exception as e:
                logger.error(f"[DB POOL] Failed to initialize ThreadedConnectionPool: {e}")
    return _pool


def get_connection():
    """
    Acquire a connection from the pool.
    You MUST call `release_connection(conn)` inside a finally block when done.
    """
    p = get_db_pool()
    if p:
        try:
            return p.getconn()
        except Exception as e:
            logger.error(f"[DB POOL] getconn failed: {e}")
    return None


def release_connection(conn):
    """Return a connection back to the pool."""
    p = get_db_pool()
    if p and conn:
        try:
            p.putconn(conn)
        except Exception as e:
            logger.error(f"[DB POOL] putconn failed: {e}")
