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

class SessionContext:
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.redis_memory_reference = f"genesis:memory:{user_id}"
        self.perception_state_reference = f"genesis:perception:{user_id}"
        self.session_state_reference = f"genesis:session:{user_id}"
        
    def to_dict(self):
        return {
            "user_id": self.user_id,
            "memory_key": self.redis_memory_reference,
            "perception_key": self.perception_state_reference
        }

def generate_session_context(user_id: str) -> SessionContext:
    """Generate a SessionContext object and track active sessions in Redis."""
    ctx = SessionContext(user_id)
    r_client = get_redis_client()
    if r_client:
        try:
            r_client.setex(ctx.session_state_reference, 3600, json.dumps({"active": True}))
        except Exception as e:
            logger.debug(f"Redis session tracking failed: {e}")
    return ctx
