import os
import uuid
import time
import json
import logging
import sqlite3
import threading
from .memory_embed import get_embedding

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Local SQLite fallback path (last-resort persistence)
# ---------------------------------------------------------------------------
_FALLBACK_DB_PATH = os.path.join(os.path.dirname(__file__), "memory_fallback.db")
_fallback_lock = threading.Lock()


def _ensure_fallback_table():
    """Create the local SQLite fallback table if it doesn't exist."""
    with _fallback_lock:
        conn = sqlite3.connect(_FALLBACK_DB_PATH)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS memory_fallback (
                id TEXT PRIMARY KEY,
                user_id TEXT,
                text_content TEXT,
                embedding TEXT,
                metadata TEXT,
                created_at REAL
            )
        """)
        conn.commit()
        conn.close()


def _write_to_fallback(doc_id: str, user_id: str, text: str, embedding, metadata: dict) -> bool:
    """Write memory to local SQLite fallback — guaranteed to never lose data."""
    try:
        _ensure_fallback_table()
        with _fallback_lock:
            conn = sqlite3.connect(_FALLBACK_DB_PATH)
            conn.execute(
                "INSERT OR REPLACE INTO memory_fallback (id, user_id, text_content, embedding, metadata, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (doc_id, user_id, text, json.dumps(embedding), json.dumps(metadata), time.time())
            )
            conn.commit()
            conn.close()
        logger.info(f"[MEMORY] Fallback SQLite write OK: {doc_id}")
        return True
    except Exception as e:
        logger.error(f"[MEMORY] Fallback SQLite write FAILED: {e}")
        return False


def _write_to_redis(doc_id: str, user_id: str, text: str, metadata: dict) -> bool:
    """Write memory to Redis (fast cache layer)."""
    try:
        import redis
        redis_url = os.environ.get("REDIS_URL")
        if not redis_url:
            return False
        r = redis.from_url(redis_url, decode_responses=True, socket_connect_timeout=3)
        key = f"genesis:memory:{user_id}:{doc_id}"
        payload = json.dumps({
            "id": doc_id,
            "text": text,
            "metadata": metadata,
            "timestamp": time.time()
        })
        r.set(key, payload, ex=86400 * 30)  # 30-day TTL
        logger.debug(f"[MEMORY] Redis write OK: {key}")
        return True
    except Exception as e:
        logger.warning(f"[MEMORY] Redis write failed: {e}")
        return False


def _write_to_postgres(doc_id: str, user_id: str, text: str, embedding, metadata: dict) -> bool:
    """Write memory to PostgreSQL (durable store)."""
    try:
        import psycopg2
        db_url = os.environ.get("DATABASE_URL")
        if not db_url:
            return False
        conn = psycopg2.connect(db_url, connect_timeout=5)
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS memory_store (
                    id VARCHAR(255) PRIMARY KEY,
                    user_id VARCHAR(255),
                    text_content TEXT,
                    embedding JSONB,
                    metadata JSONB
                )
            """)
            cur.execute("""
                INSERT INTO memory_store (id, user_id, text_content, embedding, metadata)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET text_content = EXCLUDED.text_content,
                    embedding = EXCLUDED.embedding, metadata = EXCLUDED.metadata
            """, (doc_id, user_id, text, json.dumps(embedding), json.dumps(metadata)))
        conn.commit()
        conn.close()
        logger.debug(f"[MEMORY] Postgres write OK: {doc_id}")
        return True
    except Exception as e:
        logger.warning(f"[MEMORY] Postgres write failed: {e}")
        return False


def add_memory_safe(text: str, metadata: dict = None, collection_name="genesis_long_term_memory") -> bool:
    """Store raw text and its embedding with shadow persistence.

    Write hierarchy:
        1. Redis   (fast cache)
        2. Postgres (durable)
        3. Local SQLite fallback (last resort — never discards data)
    """
    try:
        user_id = os.environ.get("CURRENT_USER_ID", "default")
        doc_id = str(uuid.uuid4())

        if metadata is None:
            metadata = {}
        if "timestamp" not in metadata:
            metadata["timestamp"] = time.time()

        embedding = get_embedding(text)

        # --- Shadow persistence: write to ALL available layers ---
        redis_ok = _write_to_redis(doc_id, user_id, text, metadata)
        postgres_ok = _write_to_postgres(doc_id, user_id, text, embedding, metadata)

        # If both cloud stores failed, use local fallback
        if not redis_ok and not postgres_ok:
            logger.warning("[MEMORY] Cloud stores unreachable — writing to local fallback")
            fallback_ok = _write_to_fallback(doc_id, user_id, text, embedding, metadata)
            if not fallback_ok:
                logger.error("[MEMORY] ALL persistence layers failed!")
                return False

        # Emit MEMORY_UPDATED event
        try:
            from core.event_bus import get_event_bus
            bus = get_event_bus()
            if bus:
                bus.publish_sync("MEMORY_UPDATED", "memory_store", {
                    "doc_id": doc_id,
                    "text_preview": text[:100],
                    "metadata": metadata,
                    "redis": redis_ok,
                    "postgres": postgres_ok,
                })
        except Exception as e:
            logger.debug(f"Event publish failed (non-fatal): {e}")

        return True
    except Exception as e:
        logger.error(f"Memory Store Error: {str(e)}")
        # Absolute last resort — try fallback even if embedding failed
        try:
            _write_to_fallback(str(uuid.uuid4()), "default", text, [], metadata or {})
        except Exception:
            pass
        return False
