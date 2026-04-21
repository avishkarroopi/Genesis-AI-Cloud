import logging
import json
import os
import threading
from .memory_store import add_memory_safe
from .memory_search import search_memory_safe, get_recent_safe

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Redis / Postgres / Local fallback for legacy key-value memory
# ---------------------------------------------------------------------------

def _get_redis_client():
    import redis
    redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379")
    try:
        client = redis.from_url(redis_url, decode_responses=True, socket_connect_timeout=3)
        client.ping()
        return client
    except Exception as e:
        logger.warning(f"Memory Manager Redis unavailable: {e}")
        return None


def _get_postgres_conn():
    """Get a Postgres connection for legacy memory fallback."""
    try:
        import psycopg2
        db_url = os.environ.get("DATABASE_URL")
        if not db_url:
            return None
        conn = psycopg2.connect(db_url, connect_timeout=5)
        return conn
    except Exception as e:
        logger.warning(f"Memory Manager Postgres unavailable: {e}")
        return None


def _get_context_uid():
    return os.environ.get("CURRENT_USER_ID", "default")


# ---------------------------------------------------------------------------
# Legacy data load / save with triple fallback
# ---------------------------------------------------------------------------

_LOCAL_FALLBACK_FILE = os.path.join(os.path.dirname(__file__), "legacy_memory.json")
_legacy_lock = threading.Lock()


def _load_local_fallback():
    """Load legacy memory from local JSON file."""
    try:
        if os.path.exists(_LOCAL_FALLBACK_FILE):
            with open(_LOCAL_FALLBACK_FILE, "r") as f:
                return json.load(f)
    except Exception:
        pass
    return None


def _save_local_fallback(data):
    """Save legacy memory to local JSON file."""
    try:
        with _legacy_lock:
            with open(_LOCAL_FALLBACK_FILE, "w") as f:
                json.dump(data, f)
    except Exception as e:
        logger.error(f"Local fallback save failed: {e}")


def _load_legacy():
    """Load legacy session data: Redis → Postgres → Local file."""
    uid = _get_context_uid()

    # Try Redis first
    client = _get_redis_client()
    if client:
        val = client.get(f"genesis:session_legacy:{uid}")
        if val:
            try:
                return json.loads(val)
            except Exception:
                pass

    # Try Postgres
    conn = _get_postgres_conn()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS legacy_memory (
                        user_id VARCHAR(255) PRIMARY KEY,
                        data JSONB
                    )
                """)
                cur.execute("SELECT data FROM legacy_memory WHERE user_id = %s", (uid,))
                row = cur.fetchone()
                conn.commit()
                conn.close()
                if row:
                    return row[0] if isinstance(row[0], dict) else json.loads(row[0])
        except Exception as e:
            logger.warning(f"Postgres legacy load failed: {e}")
            try:
                conn.close()
            except Exception:
                pass

    # Try local file
    local = _load_local_fallback()
    if local:
        return local

    return {"user_name": "Avishkar"}


def _save_legacy(data):
    """Save legacy session data: Redis + Postgres + Local file (shadow write)."""
    uid = _get_context_uid()
    saved_anywhere = False

    # Redis
    client = _get_redis_client()
    if client:
        try:
            client.set(f"genesis:session_legacy:{uid}", json.dumps(data))
            saved_anywhere = True
        except Exception:
            pass

    # Postgres
    conn = _get_postgres_conn()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS legacy_memory (
                        user_id VARCHAR(255) PRIMARY KEY,
                        data JSONB
                    )
                """)
                cur.execute("""
                    INSERT INTO legacy_memory (user_id, data) VALUES (%s, %s)
                    ON CONFLICT (user_id) DO UPDATE SET data = EXCLUDED.data
                """, (uid, json.dumps(data)))
            conn.commit()
            conn.close()
            saved_anywhere = True
        except Exception as e:
            logger.warning(f"Postgres legacy save failed: {e}")
            try:
                conn.close()
            except Exception:
                pass

    # Always write local fallback
    _save_local_fallback(data)
    saved_anywhere = True

    if not saved_anywhere:
        logger.error("[MEMORY] Legacy save failed on ALL layers!")


# ---------------------------------------------------------------------------
# Public API — unchanged signatures for backward compatibility
# ---------------------------------------------------------------------------

def save_memory(text: str) -> bool:
    """Save general memory."""
    try:
        return add_memory_safe(text, metadata={"type": "general"})
    except Exception as e:
        logger.error(f"Memory system failed gracefully in save_memory: {str(e)}")
        return False

def search_memory(query: str) -> list:
    """Search all memory types."""
    try:
        results = search_memory_safe(query)
        return results if isinstance(results, list) else []
    except Exception as e:
        logger.error(f"Memory system failed gracefully in search_memory: {str(e)}")
        return []

def get_recent_memory() -> list:
    """Retrieve recent memories."""
    try:
        return get_recent_safe()
    except Exception as e:
        logger.error(f"Memory system failed gracefully in get_recent_memory: {str(e)}")
        return []

def store_user_memory(text: str) -> bool:
    """Store specific memory about the user."""
    try:
        return add_memory_safe(text, metadata={"type": "user_memory"})
    except Exception as e:
        logger.error(f"Memory system failed gracefully in store_user_memory: {str(e)}")
        return False

def store_knowledge(text: str) -> bool:
    """Store acquired knowledge/facts."""
    try:
        return add_memory_safe(text, metadata={"type": "knowledge"})
    except Exception as e:
        logger.error(f"Memory system failed gracefully in store_knowledge: {str(e)}")
        return False

def recall_memory_for_prompt(query: str) -> str:
    """Get formatted memory context string to add to a prompt."""
    try:
        results = search_memory(query)
        if not results:
            return ""
        context = "Relevant Memories:\n"
        for mem in results:
            context += f"- {mem}\n"
        return context
    except Exception as e:
        logger.error(f"Memory system failed gracefully in recall_memory_for_prompt: {str(e)}")
        return ""

def load_memory():
    return _load_legacy()

def get_all_memory():
    return _load_legacy()

def get_user_name():
    return _load_legacy().get("user_name", "Avishkar").strip()

def set_user_name(name):
    data = _load_legacy()
    data["user_name"] = name.strip()
    _save_legacy(data)

def get_memory_key(key, default=None):
    return _load_legacy().get(key, default)

def set_memory_key(key, value):
    data = _load_legacy()
    data[key] = value
    _save_legacy(data)

def store_entity(entity_name, key, value):
    data = _load_legacy()
    if "entities" not in data:
        data["entities"] = {}
    name = entity_name.strip().capitalize()
    if name not in data["entities"]:
        data["entities"][name] = {}
    data["entities"][name][key.strip()] = value.strip() if isinstance(value, str) else value
    _save_legacy(data)

def get_entities():
    return _load_legacy().get("entities", {})
