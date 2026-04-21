"""
GENESIS Supabase Storage Layer.
High-level API for file storage using the existing Supabase client.
Provides typed upload/retrieval for AI artifacts, audio, datasets, and media.
"""

import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Default bucket names
BUCKET_ARTIFACTS = "genesis-artifacts"
BUCKET_AUDIO = "genesis-audio"
BUCKET_DATASETS = "genesis-datasets"
BUCKET_MEDIA = "genesis-media"


def _get_client():
    """Get the Supabase client from the existing singleton."""
    try:
        from core.supabase_client import get_supabase_client
        return get_supabase_client()
    except Exception as e:
        logger.error(f"[STORAGE] Supabase client unavailable: {e}")
        return None


def _ensure_bucket(client, bucket_name: str):
    """Ensure a storage bucket exists (create if missing)."""
    try:
        client.storage.get_bucket(bucket_name)
    except Exception:
        try:
            client.storage.create_bucket(bucket_name, options={"public": False})
            logger.info(f"[STORAGE] Created bucket: {bucket_name}")
        except Exception as e:
            # Bucket may already exist or permissions issue
            logger.debug(f"[STORAGE] Bucket create skipped: {e}")


def upload_artifact(filename: str, data: bytes, content_type: str = "application/octet-stream",
                    metadata: dict = None) -> dict:
    """Upload an AI artifact (plan, report, generated code, etc.)."""
    return _upload(BUCKET_ARTIFACTS, f"artifacts/{filename}", data, content_type)


def upload_audio(filename: str, data: bytes, content_type: str = "audio/wav") -> dict:
    """Upload an audio recording (TTS output, voice memo, etc.)."""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = f"audio/{ts}_{filename}"
    return _upload(BUCKET_AUDIO, path, data, content_type)


def upload_dataset(filename: str, data: bytes, content_type: str = "application/json") -> dict:
    """Upload a dataset file."""
    return _upload(BUCKET_DATASETS, f"datasets/{filename}", data, content_type)


def upload_media(filename: str, data: bytes, content_type: str = "image/png") -> dict:
    """Upload generated media (images, videos, etc.)."""
    return _upload(BUCKET_MEDIA, f"media/{filename}", data, content_type)


def _upload(bucket: str, path: str, data: bytes, content_type: str) -> dict:
    """Internal upload helper."""
    client = _get_client()
    if not client:
        return {"error": "Supabase client not available"}

    try:
        _ensure_bucket(client, bucket)
        result = client.storage.from_(bucket).upload(path, data, {"content-type": content_type})
        logger.info(f"[STORAGE] Uploaded: {bucket}/{path}")
        return {"status": "uploaded", "bucket": bucket, "path": path}
    except Exception as e:
        logger.error(f"[STORAGE] Upload error: {e}")
        return {"error": str(e)}


def list_artifacts(prefix: str = "artifacts/") -> list:
    """List files in the artifacts bucket."""
    client = _get_client()
    if not client:
        return []
    try:
        result = client.storage.from_(BUCKET_ARTIFACTS).list(prefix)
        return result or []
    except Exception as e:
        logger.error(f"[STORAGE] List error: {e}")
        return []


def get_artifact_url(path: str) -> str:
    """Get a signed URL for an artifact."""
    client = _get_client()
    if not client:
        return ""
    try:
        return client.storage.from_(BUCKET_ARTIFACTS).get_public_url(path)
    except Exception as e:
        logger.error(f"[STORAGE] URL error: {e}")
        return ""


def get_storage_status() -> dict:
    """Return the current Supabase storage configuration status."""
    client = _get_client()
    configured = client is not None
    return {
        "configured": configured,
        "provider": "supabase" if configured else "none",
        "buckets": [BUCKET_ARTIFACTS, BUCKET_AUDIO, BUCKET_DATASETS, BUCKET_MEDIA],
    }
