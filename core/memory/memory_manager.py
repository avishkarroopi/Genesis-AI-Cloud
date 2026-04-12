import logging
import json
import os
import threading
from .memory_store import add_memory_safe
from .memory_search import search_memory_safe, get_recent_safe

logger = logging.getLogger(__name__)

# Replaced local JSON with Redis/PostgreSQL in cloud architecture
def _get_redis_client():
    import redis
    redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379")
    try:
        return redis.from_url(redis_url, decode_responses=True)
    except Exception as e:
        logger.warning(f"Memory Manager Redis fallback failed: {e}")
        return None

def _get_context_uid():
    return os.environ.get("CURRENT_USER_ID", "default")

def _load_legacy():
    client = _get_redis_client()
    uid = _get_context_uid()
    if client:
        val = client.get(f"genesis:session_legacy:{uid}")
        if val:
            try:
                return json.loads(val)
            except Exception:
                pass
    return {"user_name": "Avishkar"}

def _save_legacy(data):
    client = _get_redis_client()
    uid = _get_context_uid()
    if client:
        try:
            client.set(f"genesis:session_legacy:{uid}", json.dumps(data))
        except Exception:
            pass

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
