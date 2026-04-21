"""
TEST 16 — SYSTEM MONITOR TEST
Verifies:
- SystemMonitor class instantiation
- Health metrics collection
- Component status tracking
- Health report generation
"""

import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

os.environ.setdefault("CLOUD_MODE", "true")


def run_test():
    results = {"pass": 0, "fail": 0, "details": []}

    print("\n╔══════════════════════════════════════════════════════════╗")
    print("║       TEST 16 — SYSTEM MONITOR TEST                    ║")
    print("╚══════════════════════════════════════════════════════════╝\n")

    # 1. Import
    print("  ── Monitor Module Import ──")
    try:
        from core.system_monitor import (
            SystemMonitor, SelfRecoverySystem, HealthStatus,
            ComponentType, HealthMetric, Failure, get_system_monitor,
            ModuleRestartStrategy, ConfigReloadStrategy
        )
        print(f"    ✅ Monitoring module imported ... PASS")
        results["pass"] += 1
    except Exception as e:
        print(f"    ❌ Import: {e}")
        results["fail"] += 1
        return results

    # 2. HealthStatus enum
    print("\n  ── HealthStatus Enum ──")
    statuses = ["HEALTHY", "WARNING", "CRITICAL", "RECOVERING", "OFFLINE"]
    for s in statuses:
        ok = hasattr(HealthStatus, s)
        icon = "✅" if ok else "❌"
        print(f"    {icon} HealthStatus.{s} ... {'PASS' if ok else 'FAIL'}")
        results["pass" if ok else "fail"] += 1

    # 3. ComponentType enum
    print("\n  ── ComponentType Enum ──")
    components = ["MEMORY", "PROCESSOR", "DISK", "NETWORK", "AI_ENGINE", "EVENT_BUS"]
    for c in components:
        ok = hasattr(ComponentType, c)
        icon = "✅" if ok else "❌"
        print(f"    {icon} ComponentType.{c} ... {'PASS' if ok else 'FAIL'}")
        results["pass" if ok else "fail"] += 1

    # 4. SystemMonitor instantiation
    print("\n  ── SystemMonitor Instance ──")
    try:
        monitor = get_system_monitor()
        assert monitor is not None
        assert hasattr(monitor, "health_metrics")
        assert hasattr(monitor, "failures")
        assert hasattr(monitor, "component_status")
        print(f"    ✅ SystemMonitor instantiated ... PASS")
        results["pass"] += 1
    except Exception as e:
        print(f"    ❌ Monitor instance: {e}")
        results["fail"] += 1

    # 5. Health report generation
    print("\n  ── Health Report ──")
    try:
        report = monitor.get_health_report()
        assert isinstance(report, dict)
        assert "timestamp" in report
        assert "overall_status" in report
        assert "component_status" in report
        assert "recent_metrics" in report
        assert "failures" in report
        print(f"    ✅ Health report structure valid ... PASS")
        print(f"      Overall Status: {report['overall_status']}")
        results["pass"] += 1
    except Exception as e:
        print(f"    ❌ Health report: {e}")
        results["fail"] += 1

    # 6. Overall health calculation
    print("\n  ── Overall Health Calculation ──")
    try:
        health = monitor.get_overall_health()
        assert isinstance(health, HealthStatus)
        print(f"    ✅ Overall health: {health.value} ... PASS")
        results["pass"] += 1
    except Exception as e:
        print(f"    ❌ Health calc: {e}")
        results["fail"] += 1

    # 7. HealthMetric creation
    print("\n  ── HealthMetric Object ──")
    try:
        metric = HealthMetric(
            component_type=ComponentType.PROCESSOR,
            metric_name="cpu_usage",
            value=45.0,
            unit="%"
        )
        d = metric.to_dict()
        assert d["component"] == "processor"
        assert d["metric"] == "cpu_usage"
        assert d["value"] == 45.0
        print(f"    ✅ HealthMetric.to_dict() ... PASS")
        results["pass"] += 1
    except Exception as e:
        print(f"    ❌ HealthMetric: {e}")
        results["fail"] += 1

    # 8. Threshold logic
    print("\n  ── Threshold Status Logic ──")
    try:
        # Below threshold = HEALTHY
        s1 = monitor._get_status(50.0, 85.0)
        assert s1 == HealthStatus.HEALTHY
        # Above threshold = CRITICAL
        s2 = monitor._get_status(90.0, 85.0)
        assert s2 == HealthStatus.CRITICAL
        # Near threshold (85% of threshold ~ 72.25) = WARNING
        s3 = monitor._get_status(75.0, 85.0)
        assert s3 == HealthStatus.WARNING
        print(f"    ✅ Threshold logic correct ... PASS")
        results["pass"] += 1
    except Exception as e:
        print(f"    ❌ Threshold logic: {e}")
        results["fail"] += 1

    total = results["pass"] + results["fail"]
    print(f"\n  Summary: {results['pass']}/{total} checks passed")
    return results


if __name__ == "__main__":
    r = run_test()
    sys.exit(0 if r["fail"] == 0 else 1)
