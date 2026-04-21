"""
GENESIS Supabase Client — Vector Storage & File Storage Interface.
Provides connection management and vector operations for AI semantic memory.
"""

import os

_supabase_client = None


def get_supabase_client():
    """Get or create the singleton Supabase client."""
    global _supabase_client

    if _supabase_client is not None:
        return _supabase_client

    url = os.environ.get("SUPABASE_URL", "")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get("SUPABASE_ANON_KEY", "")

    if not url or not key:
        print("[SUPABASE] Missing SUPABASE_URL or key — client unavailable.", flush=True)
        return None

    try:
        from supabase import create_client
        _supabase_client = create_client(url, key)
        print(f"[SUPABASE] Client initialized → {url}", flush=True)
        return _supabase_client
    except Exception as e:
        print(f"[SUPABASE] Client init failed: {e}", flush=True)
        return None


# ── Vector Storage Operations ────────────────────────────────────────────────

def store_vector(table: str, embedding: list, content: str, metadata: dict = None):
    """Store a vector embedding with its content and optional metadata.
    
    Requires a Supabase table with columns:
      - id (uuid, auto-generated)
      - embedding (vector)
      - content (text)
      - metadata (jsonb)
    """
    client = get_supabase_client()
    if not client:
        return None

    try:
        row = {"embedding": embedding, "content": content}
        if metadata:
            row["metadata"] = metadata
        result = client.table(table).insert(row).execute()
        return result.data
    except Exception as e:
        print(f"[SUPABASE] Vector store error: {e}", flush=True)
        return None


def search_vectors(table: str, query_embedding: list, match_count: int = 5):
    """Search for similar vectors using Supabase pgvector match function.
    
    Requires an RPC function 'match_<table>' configured in Supabase.
    """
    client = get_supabase_client()
    if not client:
        return []

    try:
        result = client.rpc(
            f"match_{table}",
            {"query_embedding": query_embedding, "match_count": match_count}
        ).execute()
        return result.data or []
    except Exception as e:
        print(f"[SUPABASE] Vector search error: {e}", flush=True)
        return []


# ── File Storage Operations ──────────────────────────────────────────────────

def upload_file(bucket: str, path: str, file_data: bytes, content_type: str = "application/octet-stream"):
    """Upload a file to Supabase Storage."""
    client = get_supabase_client()
    if not client:
        return None

    try:
        result = client.storage.from_(bucket).upload(path, file_data, {"content-type": content_type})
        return result
    except Exception as e:
        print(f"[SUPABASE] File upload error: {e}", flush=True)
        return None


def get_file_url(bucket: str, path: str):
    """Get the public URL for a file in Supabase Storage."""
    client = get_supabase_client()
    if not client:
        return None

    try:
        return client.storage.from_(bucket).get_public_url(path)
    except Exception as e:
        print(f"[SUPABASE] File URL error: {e}", flush=True)
        return None


def list_files(bucket: str, folder: str = ""):
    """List files in a Supabase Storage bucket."""
    client = get_supabase_client()
    if not client:
        return []

    try:
        result = client.storage.from_(bucket).list(folder)
        return result or []
    except Exception as e:
        print(f"[SUPABASE] File list error: {e}", flush=True)
        return []


# ── Connectivity Test ────────────────────────────────────────────────────────

def test_connection():
    """Test Supabase connectivity by querying server health."""
    client = get_supabase_client()
    if not client:
        return {"status": "failed", "error": "Client not initialized"}

    try:
        # Simple query to verify connectivity
        result = client.table("_health_check").select("*").limit(1).execute()
        return {"status": "connected", "data": result.data}
    except Exception as e:
        # Even if the table doesn't exist, a 404 means we connected
        error_str = str(e)
        if "404" in error_str or "does not exist" in error_str.lower() or "42P01" in error_str:
            return {"status": "connected", "note": "Auth OK, no health_check table"}
        return {"status": "error", "error": error_str}
