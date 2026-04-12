import os
import uuid
import time
import json
import logging
from .memory_embed import get_embedding

logger = logging.getLogger(__name__)

def add_memory_safe(text: str, metadata: dict = None, collection_name="genesis_long_term_memory") -> bool:
    """Store raw text and its embedding safely to PostgreSQL."""
    try:
        import psycopg2
        db_url = os.environ.get("DATABASE_URL")
        # Fail gracefully if DB is disabled
        if not db_url:
            return False
            
        user_id = os.environ.get("CURRENT_USER_ID", "default")
        
        try:
            conn = psycopg2.connect(db_url)
        except Exception:
            return False
            
        with conn.cursor() as cur:
            if metadata is None: 
                metadata = {}
            if "timestamp" not in metadata: 
                metadata["timestamp"] = time.time()
                
            embedding = get_embedding(text)
            
            cur.execute("""
                CREATE TABLE IF NOT EXISTS memory_store (
                    id VARCHAR(255) PRIMARY KEY,
                    user_id VARCHAR(255),
                    text_content TEXT,
                    embedding JSONB,
                    metadata JSONB
                )
            """)
            
            doc_id = str(uuid.uuid4())
            cur.execute("""
                INSERT INTO memory_store (id, user_id, text_content, embedding, metadata)
                VALUES (%s, %s, %s, %s, %s)
            """, (doc_id, user_id, text, json.dumps(embedding), json.dumps(metadata)))
        conn.commit()
        conn.close()

        # Emit MEMORY_UPDATED event
        try:
            from core.event_bus import get_event_bus
            bus = get_event_bus()
            if bus:
                bus.publish_sync("MEMORY_UPDATED", "memory_store", {
                    "doc_id": doc_id,
                    "text_preview": text[:100],
                    "metadata": metadata,
                })
        except Exception as e:
            logger.debug(f"Event publish failed (non-fatal): {e}")

        return True
    except Exception as e:
        logger.error(f"PostgreSQL Memory Store Error: {str(e)}")
        return False
