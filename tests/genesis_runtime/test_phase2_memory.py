"""
TEST — Phase 2 Memory Reliability
Verifies memory fallback chain: Redis → Postgres → SQLite.
"""

import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

os.environ.setdefault("CLOUD_MODE", "true")


def test_memory_store_import():
    """memory_store module should import with fallback functions."""
    from core.memory.memory_store import (
        add_memory_safe,
        _write_to_fallback,
        _write_to_redis,
        _write_to_postgres,
    )
    assert callable(add_memory_safe)
    assert callable(_write_to_fallback)


def test_local_fallback_write():
    """SQLite fallback should always succeed locally."""
    from core.memory.memory_store import _write_to_fallback
    result = _write_to_fallback(
        doc_id="test-001",
        user_id="test_user",
        text="Test memory entry for fallback verification",
        embedding=[0.1, 0.2, 0.3],
        metadata={"type": "test"}
    )
    assert result is True


def test_local_fallback_db_exists():
    """After a fallback write, the SQLite file should exist."""
    import sqlite3
    db_path = os.path.join(PROJECT_ROOT, "core", "memory", "memory_fallback.db")
    assert os.path.exists(db_path), f"Fallback DB not found: {db_path}"
    conn = sqlite3.connect(db_path)
    cursor = conn.execute("SELECT COUNT(*) FROM memory_fallback")
    count = cursor.fetchone()[0]
    conn.close()
    assert count >= 1, "No entries in fallback DB"


def test_memory_manager_legacy_fallback():
    """Legacy memory should work even without Redis/Postgres."""
    # Clear env to simulate cloud-down scenario
    old_redis = os.environ.pop("REDIS_URL", None)
    old_db = os.environ.pop("DATABASE_URL", None)
    try:
        from core.memory.memory_manager import load_memory
        data = load_memory()
        assert isinstance(data, dict)
        assert "user_name" in data
    finally:
        if old_redis:
            os.environ["REDIS_URL"] = old_redis
        if old_db:
            os.environ["DATABASE_URL"] = old_db


def test_add_memory_safe_never_loses_data():
    """add_memory_safe should return True even if cloud stores are unreachable."""
    old_redis = os.environ.pop("REDIS_URL", None)
    old_db = os.environ.pop("DATABASE_URL", None)
    try:
        from core.memory.memory_store import add_memory_safe
        result = add_memory_safe("This must never be lost", metadata={"type": "resilience_test"})
        assert result is True, "Memory was discarded despite fallback availability"
    finally:
        if old_redis:
            os.environ["REDIS_URL"] = old_redis
        if old_db:
            os.environ["DATABASE_URL"] = old_db


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
