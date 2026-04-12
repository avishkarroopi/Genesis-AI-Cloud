import os
import json
import logging

logger = logging.getLogger(__name__)

def get_redis_client():
    import redis
    redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379")
    try:
        return redis.from_url(redis_url, decode_responses=True)
    except Exception:
        return None

def store_frame(user_id: str, frame_data: dict, max_frames: int = 10):
    """
    Store a perception frame in Redis, namespaced by user_id.
    Frame data is a dict from MediaPipe detection result, e.g.:
      {"type": "face", "landmarks": [...], "timestamp": ...}
    Maintains a rolling buffer of recent frames.
    """
    r_client = get_redis_client()
    if not r_client:
        return False
    
    key = f"genesis:perception:{user_id}"
    try:
        r_client.lpush(key, json.dumps(frame_data))
        r_client.ltrim(key, 0, max_frames - 1)
        r_client.expire(key, 3600)
        return True
    except Exception as e:
        logger.error(f"Perception buffer store error: {e}")
        return False

def get_latest_frames(user_id: str, count: int = 5) -> list:
    """Retrieve the latest N perception frames for a user from Redis."""
    r_client = get_redis_client()
    if not r_client:
        return []
    
    key = f"genesis:perception:{user_id}"
    try:
        items = r_client.lrange(key, 0, count - 1)
        return [json.loads(item) for item in items]
    except Exception as e:
        logger.error(f"Perception buffer get error: {e}")
        return []

def clear_buffer(user_id: str):
    """Remove all perception frames for a user."""
    r_client = get_redis_client()
    if not r_client:
        return
    try:
        r_client.delete(f"genesis:perception:{user_id}")
    except Exception as e:
        logger.error(f"Perception buffer clear error: {e}")
