import json
import urllib.request
import logging

logger = logging.getLogger(__name__)

# Using local Ollama default port
OLLAMA_URL = "http://127.0.0.1:11434/api/embeddings"
EMBED_MODEL = "nomic-embed-text" # Allowed: nomic-embed-text, mxbai, bge

def get_embedding(text: str) -> list:
    """Gets an embedding from the local Ollama instance."""
    for attempt in range(3):
        try:
            data = {
                "model": EMBED_MODEL,
                "prompt": text
            }
            
            req = urllib.request.Request(
                OLLAMA_URL,
                data=json.dumps(data).encode("utf-8"),
                headers={"Content-Type": "application/json"}
            )
            
            with urllib.request.urlopen(req, timeout=5) as response:
                result = json.loads(response.read().decode("utf-8"))
                return result.get("embedding", [])
        except Exception as e:
            if attempt < 2:
                import time
                time.sleep(1)
            else:
                logger.warning(f"Failed to get embedding from Ollama after 3 attempts: {str(e)}")
                logger.warning("Embedding model nomic-embed-text not installed. Install with: ollama pull nomic-embed-text")
                return []
    return []
