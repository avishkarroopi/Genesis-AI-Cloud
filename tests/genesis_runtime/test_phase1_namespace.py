"""
TEST — Phase 1 Namespace Verification
Verifies core.system_monitor imports work and old monitoring.py is gone.
"""

import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

os.environ.setdefault("CLOUD_MODE", "true")


def test_old_monitoring_file_removed():
    """core/monitoring.py should no longer exist."""
    old_path = os.path.join(PROJECT_ROOT, "core", "monitoring.py")
    assert not os.path.exists(old_path), f"Old file still exists: {old_path}"


def test_new_system_monitor_exists():
    """core/system_monitor.py should exist."""
    new_path = os.path.join(PROJECT_ROOT, "core", "system_monitor.py")
    assert os.path.exists(new_path), f"New file missing: {new_path}"


def test_system_monitor_import():
    """core.system_monitor module should import cleanly."""
    from core.system_monitor import SystemMonitor, get_system_monitor, HealthStatus
    monitor = get_system_monitor()
    assert monitor is not None
    assert hasattr(monitor, "get_health_report")


def test_monitoring_directory_intact():
    """core/monitoring/ directory should still exist with self_improvement_engine."""
    dir_path = os.path.join(PROJECT_ROOT, "core", "monitoring")
    assert os.path.isdir(dir_path)
    assert os.path.isfile(os.path.join(dir_path, "self_improvement_engine.py"))


def test_health_report_structure():
    from core.system_monitor import get_system_monitor
    monitor = get_system_monitor()
    report = monitor.get_health_report()
    assert "overall_status" in report
    assert "component_status" in report
    assert "timestamp" in report


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
