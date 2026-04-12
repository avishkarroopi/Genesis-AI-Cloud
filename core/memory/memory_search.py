import os
import logging
from .memory_embed import get_embedding

logger = logging.getLogger(__name__)

def search_memory_safe(query: str, n_results: int = 3, collection_name="genesis_long_term_memory", filter_metadata=None) -> list:
    """Search for relevant memories safely through PostgreSQL."""
    try:
        import psycopg2
        db_url = os.environ.get("DATABASE_URL")
        if not db_url: return []
        
        user_id = os.environ.get("CURRENT_USER_ID", "default")
        
        try:
            conn = psycopg2.connect(db_url)
        except Exception:
            return []
            
        results = []
        with conn.cursor() as cur:
            cur.execute(
                "SELECT text_content FROM memory_store WHERE user_id = %s LIMIT %s", 
                (user_id, 20)
            )
            rows = cur.fetchall()
            for row in rows:
                content = row[0]
                if query.lower() in content.lower() or any(word in content.lower() for word in query.lower().split()):
                    results.append(content)
        conn.close()
        return results[:n_results]
    except Exception as e:
        logger.error(f"PostgreSQL Memory Search Error: {str(e)}")
        return []

def get_recent_safe(limit: int = 5, collection_name="genesis_long_term_memory") -> list:
    """Retrieve recent memories ordered by timestamp (newest first)."""
    try:
        import psycopg2
        db_url = os.environ.get("DATABASE_URL")
        if not db_url: return []
        
        user_id = os.environ.get("CURRENT_USER_ID", "default")
        
        try:
            conn = psycopg2.connect(db_url)
        except Exception:
            return []
            
        results = []
        with conn.cursor() as cur:
            cur.execute("""
                SELECT text_content FROM memory_store 
                WHERE user_id = %s 
                ORDER BY metadata->>'timestamp' DESC 
                LIMIT %s
            """, (user_id, limit))
            rows = cur.fetchall()
            results = [row[0] for row in rows]
        conn.close()
        return results
    except Exception as e:
        logger.error(f"Failed to get recent memory safely: {str(e)}")
        return []
