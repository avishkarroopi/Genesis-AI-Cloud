"""
GENESIS Self-Improvement: Learning Memory
Stores reflection insights in PostgreSQL for retrieval in future prompts.
"""
import json
import logging

logger = logging.getLogger(__name__)

class LearningMemory:
    def store_insight(self, intent: str, mistake: str, correction: str):
        """Persist a learned reasoning correction to Postgres."""
        try:
            from core.db_pool import get_connection, release_connection
        except ImportError:
            return

        conn = get_connection()
        if not conn:
            return
            
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS ai_learned_insights (
                        id SERIAL PRIMARY KEY,
                        intent VARCHAR(100),
                        mistake TEXT,
                        correction TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                cur.execute("""
                    INSERT INTO ai_learned_insights (intent, mistake, correction)
                    VALUES (%s, %s, %s)
                """, (intent, mistake, correction))
                conn.commit()
                logger.info(f"[LEARNING] Stored insight for {intent}.")
        except Exception as e:
            logger.error(f"[LEARNING] DB Error: {e}")
        finally:
            release_connection(conn)

    def retrieve_insights(self, intent: str, limit: int = 3) -> str:
        """Fetch past corrections for prompt augmentation."""
        try:
            from core.db_pool import get_connection, release_connection
            conn = get_connection()
            if not conn: return ""
            
            with conn.cursor() as cur:
                cur.execute("SELECT mistake, correction FROM ai_learned_insights WHERE intent = %s ORDER BY id DESC LIMIT %s", (intent, limit))
                rows = cur.fetchall()
                if not rows: return ""
                
                output = "Past Mistakes to Avoid:\n"
                for r in rows:
                    output += f"- Mistake: {r[0]} | Correction: {r[1]}\n"
                return output
        except Exception:
            return ""
        finally:
            if 'conn' in locals() and conn: release_connection(conn)

_global_memory = None
def get_learning_memory() -> LearningMemory:
    global _global_memory
    if _global_memory is None:
        _global_memory = LearningMemory()
    return _global_memory
