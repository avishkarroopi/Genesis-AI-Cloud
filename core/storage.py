"""
GENESIS Object Storage Abstraction.
Provides a unified interface for S3-compatible object storage (AWS S3 / Cloudflare R2).
Placeholder until credentials are provided.
"""

import os

_storage_client = None


def _get_config():
    """Read S3/R2 configuration from environment."""
    return {
        "bucket": os.environ.get("S3_BUCKET", ""),
        "access_key": os.environ.get("S3_ACCESS_KEY", ""),
        "secret_key": os.environ.get("S3_SECRET_KEY", ""),
        "endpoint_url": os.environ.get("S3_ENDPOINT_URL", ""),  # For R2 compatibility
        "region": os.environ.get("S3_REGION", "us-east-1"),
    }


def get_storage_client():
    """Get or create the S3-compatible storage client."""
    global _storage_client

    if _storage_client is not None:
        return _storage_client

    cfg = _get_config()
    if not cfg["bucket"] or not cfg["access_key"] or not cfg["secret_key"]:
        print("[STORAGE] S3/R2 credentials not configured — storage unavailable.", flush=True)
        return None

    try:
        import boto3
        session = boto3.session.Session()
        kwargs = {
            "service_name": "s3",
            "aws_access_key_id": cfg["access_key"],
            "aws_secret_access_key": cfg["secret_key"],
            "region_name": cfg["region"],
        }
        if cfg["endpoint_url"]:
            kwargs["endpoint_url"] = cfg["endpoint_url"]

        _storage_client = session.client(**kwargs)
        print(f"[STORAGE] S3 client initialized (bucket: {cfg['bucket']})", flush=True)
        return _storage_client
    except ImportError:
        print("[STORAGE] boto3 not installed — run: pip install boto3", flush=True)
        return None
    except Exception as e:
        print(f"[STORAGE] Client init failed: {e}", flush=True)
        return None


def upload_object(key: str, data: bytes, content_type: str = "application/octet-stream"):
    """Upload an object to the configured S3 bucket."""
    client = get_storage_client()
    cfg = _get_config()
    if not client:
        return None

    try:
        client.put_object(Bucket=cfg["bucket"], Key=key, Body=data, ContentType=content_type)
        return {"status": "uploaded", "key": key}
    except Exception as e:
        print(f"[STORAGE] Upload error: {e}", flush=True)
        return None


def download_object(key: str):
    """Download an object from the configured S3 bucket."""
    client = get_storage_client()
    cfg = _get_config()
    if not client:
        return None

    try:
        response = client.get_object(Bucket=cfg["bucket"], Key=key)
        return response["Body"].read()
    except Exception as e:
        print(f"[STORAGE] Download error: {e}", flush=True)
        return None


def list_objects(prefix: str = ""):
    """List objects in the configured S3 bucket."""
    client = get_storage_client()
    cfg = _get_config()
    if not client:
        return []

    try:
        response = client.list_objects_v2(Bucket=cfg["bucket"], Prefix=prefix)
        return [obj["Key"] for obj in response.get("Contents", [])]
    except Exception as e:
        print(f"[STORAGE] List error: {e}", flush=True)
        return []


def get_storage_status():
    """Return the current storage configuration status."""
    cfg = _get_config()
    configured = bool(cfg["bucket"] and cfg["access_key"] and cfg["secret_key"])
    return {
        "configured": configured,
        "bucket": cfg["bucket"] if configured else None,
        "provider": "R2" if cfg["endpoint_url"] else "S3" if configured else "none",
    }
