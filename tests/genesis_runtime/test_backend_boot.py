"""
TEST 2 — BACKEND BOOT TEST
Verifies that the FastAPI backend can initialize without import errors
and all core subsystems load successfully.
"""

import os
import sys
import traceback

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

os.environ.setdefault("CLOUD_MODE", "true")
os.environ.setdefault("GENESIS_SAFE_MODE", "true")


def _try_import(label, import_func):
    """Attempt an import and report result."""
    try:
        import_func()
        print(f"    ✅ {label} ... PASS")
        return True
    except Exception as e:
        print(f"    ❌ {label} ... FAIL — {type(e).__name__}: {e}")
        return False


def run_test():
    results = {"pass": 0, "fail": 0, "details": []}

    print("\n╔══════════════════════════════════════════════════════════╗")
    print("║           TEST 2 — BACKEND BOOT TEST                   ║")
    print("╚══════════════════════════════════════════════════════════╝\n")

    checks = [
        ("FastAPI app import", lambda: __import__("server.api", fromlist=["app"])),
        ("Event Bus module", lambda: __import__("core.event_bus", fromlist=["get_event_bus"])),
        ("Tool Registry module", lambda: __import__("core.tool_registry", fromlist=["get_tool_registry"])),
        ("Agent Registry module", lambda: __import__("core.agent_registry", fromlist=["AGENTS"])),
        ("AI Router module", lambda: __import__("core.ai_router", fromlist=["route_ai_request"])),
        ("Voice WebSocket module", lambda: __import__("server.voice_ws", fromlist=["router"])),
        ("Brain Chain module", lambda: __import__("core.brain_chain", fromlist=["brain_chain"])),
        ("Monitoring module", lambda: __import__("core.system_monitor", fromlist=["SystemMonitor"])),
        ("Security — Hardrock", lambda: __import__("core.security.hardrock_security", fromlist=["sanitize_input"])),
        ("Security — Permissions", lambda: __import__("core.security.permissions", fromlist=["check_permission"])),
        ("Security — SafeMode", lambda: __import__("core.security.safe_mode", fromlist=["is_safe_mode_enabled"])),
        ("Security — Sandbox", lambda: __import__("core.security.tool_sandbox", fromlist=["sandbox_execute"])),
        ("Planner module", lambda: __import__("core.planner.planner", fromlist=["create_plan"])),
        ("Digital Twin", lambda: __import__("core.digital_twin.behavior_simulator", fromlist=["BehaviorSimulator"])),
        ("Self Improvement", lambda: __import__("core.self_improvement.self_improvement_engine", fromlist=["start_self_improvement_daemon"])),
        ("Cognitive Orchestrator", lambda: __import__("core.cognitive.cognitive_orchestrator", fromlist=["initialize_module"])),
        ("Governance Layer", lambda: __import__("core.cognitive.governance_layer", fromlist=["initialize_module"])),
        ("Memory Store", lambda: __import__("core.memory.memory_store", fromlist=["add_memory_safe"])),
        ("Learning Engine", lambda: __import__("core.learning_engine", fromlist=["evaluate_experience"])),
        ("Automation Engine", lambda: __import__("core.automation_engine", fromlist=["trigger_webhook"])),
        ("Knowledge Graph", lambda: __import__("core.knowledge_graph", fromlist=["knowledge_graph"])),
    ]

    print("  ── Module Import Tests ──")
    for label, fn in checks:
        ok = _try_import(label, fn)
        results["pass" if ok else "fail"] += 1
        if not ok:
            results["details"].append(f"IMPORT FAIL: {label}")

    # Verify FastAPI app object
    print("\n  ── FastAPI App Verification ──")
    try:
        from server.api import app
        assert app is not None, "app is None"
        assert hasattr(app, "routes"), "app has no routes"
        route_count = len(app.routes)
        print(f"    ✅ FastAPI app has {route_count} registered routes ... PASS")
        results["pass"] += 1
    except Exception as e:
        print(f"    ❌ FastAPI app verification ... FAIL — {e}")
        results["fail"] += 1
        results["details"].append(f"APP VERIFY FAIL: {e}")

    # Verify singletons can be obtained
    print("\n  ── Singleton Initialization ──")
    singleton_checks = [
        ("EventBus singleton", lambda: __import__("core.event_bus", fromlist=["get_event_bus"]).get_event_bus()),
        ("ToolRegistry singleton", lambda: __import__("core.tool_registry", fromlist=["get_tool_registry"]).get_tool_registry()),
        ("SystemMonitor singleton", lambda: __import__("core.system_monitor", fromlist=["get_system_monitor"]).get_system_monitor()),
    ]

    for label, fn in singleton_checks:
        try:
            obj = fn()
            assert obj is not None
            print(f"    ✅ {label} ... PASS")
            results["pass"] += 1
        except Exception as e:
            print(f"    ❌ {label} ... FAIL — {e}")
            results["fail"] += 1
            results["details"].append(f"SINGLETON FAIL: {label}")

    total = results["pass"] + results["fail"]
    print(f"\n  Summary: {results['pass']}/{total} checks passed")
    return results


if __name__ == "__main__":
    r = run_test()
    sys.exit(0 if r["fail"] == 0 else 1)
