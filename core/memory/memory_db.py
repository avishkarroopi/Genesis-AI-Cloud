import os
import logging

logger = logging.getLogger(__name__)

# Replaced ChromaDB with Cloud PostgreSQL implementation.
CHROMA_AVAILABLE = False

def get_db_collection(collection_name="genesis_long_term_memory"):
    """Legacy shim removed for cloud architecture."""
    return None

def init_memory_db():
    """Ensure PostgreSQL structure is initialized."""
    import psycopg2
    db_url = os.environ.get("DATABASE_URL")
    if not db_url: return False
    
    try:
        conn = psycopg2.connect(db_url)
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
        conn.commit()
        conn.close()
        logger.info("PostgreSQL memory store initialized successfully.")
        return True
    except Exception as e:
        logger.error(f"PostgreSQL initialization failed: {e}")
        return False
