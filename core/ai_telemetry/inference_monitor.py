"""
GENESIS AI Telemetry — Inference Monitor
Batches telemetry events into Redis and periodically flushes them to PostgreSQL
to prevent high-throughput DB locking.
"""
import json
import logging
import time
import threading
from typing import Dict, Any

logger = logging.getLogger(__name__)

REDIS_TELEMETRY_KEY = "genesis:telemetry:batch"

class InferenceMonitor:
    def __init__(self):
        self._flush_interval = 30  # seconds
        self._running = False
        self._thread = None
        
    def _get_redis(self):
        try:
            from server.session_manager import get_redis_client
            return get_redis_client()
        except ImportError:
            return None

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._flush_loop, daemon=True)
        self._thread.start()
        logger.info("[TELEMETRY] Inference Monitor batch processor started.")

    def record_event(self, category: str, dimensions: Dict[str, Any], count: int = 1):
        """Push an event to Redis."""
        r = self._get_redis()
        if not r:
            logger.warning("[TELEMETRY] Redis missing, dropping metric.")
            return
            
        payload = {
            "category": category,
            "dimensions": dimensions,
            "count": count,
            "timestamp": int(time.time())
        }
        try:
            r.rpush(REDIS_TELEMETRY_KEY, json.dumps(payload))
        except Exception as e:
            logger.error(f"[TELEMETRY] Failed to queue metric: {e}")

    def _flush_loop(self):
        while self._running:
            time.sleep(self._flush_interval)
            self.flush_to_db()

    def flush_to_db(self):
        """Pull all queued events from Redis and batch insert into PostgreSQL."""
        r = self._get_redis()
        if not r:
            return

        try:
            # Pop all items currently in the list
            pipe = r.pipeline()
            pipe.lrange(REDIS_TELEMETRY_KEY, 0, -1)
            pipe.delete(REDIS_TELEMETRY_KEY)
            results = pipe.execute()
            
            items = results[0]
            if not items:
                return

            parsed_items = []
            for i in items:
                try:
                    parsed_items.append(json.loads(i))
                except Exception:
                    pass

            if not parsed_items:
                return

            self._batch_insert_pg(parsed_items)

        except Exception as e:
            logger.error(f"[TELEMETRY] Flush failed: {e}")

    def _batch_insert_pg(self, items: list):
        from core.db_pool import get_connection, release_connection
        conn = get_connection()
        if not conn:
            return

        try:
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS ai_telemetry (
                        id SERIAL PRIMARY KEY,
                        category VARCHAR(100),
                        dimensions JSONB,
                        count INTEGER,
                        created_at BIGINT
                    )
                """)
                
                from psycopg2.extras import execute_values
                values = [(i["category"], json.dumps(i.get("dimensions", {})), i.get("count", 1), i["timestamp"]) for i in items]
                execute_values(cur, """
                    INSERT INTO ai_telemetry (category, dimensions, count, created_at)
                    VALUES %s
                """, values)
                conn.commit()
                logger.debug(f"[TELEMETRY] Flushed {len(items)} metrics to PG.")
        except Exception as e:
            logger.error(f"[TELEMETRY] PG Batch insert failed: {e}")
        finally:
            release_connection(conn)


_monitor = None
def get_inference_monitor() -> InferenceMonitor:
    global _monitor
    if _monitor is None:
        _monitor = InferenceMonitor()
        _monitor.start()  # Auto-start daemon thread
    return _monitor
