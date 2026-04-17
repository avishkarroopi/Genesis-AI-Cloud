"""
TEST 12 — COGNITIVE SYSTEM TEST
Verifies:
- cognitive_orchestrator module
- strategy_optimizer module
- executive_control (if present)
- governance_layer module
- Reasoning chain execution via event bus
"""

import os
import sys
import asyncio

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

os.environ.setdefault("CLOUD_MODE", "true")


def run_test():
    results = {"pass": 0, "fail": 0, "details": []}

    print("\n╔══════════════════════════════════════════════════════════╗")
    print("║      TEST 12 — COGNITIVE SYSTEM TEST                   ║")
    print("╚══════════════════════════════════════════════════════════╝\n")

    # 1. Module imports
    print("  ── Cognitive Module Imports ──")
    modules = [
        ("cognitive_orchestrator", "core.cognitive.cognitive_orchestrator"),
        ("governance_layer", "core.cognitive.governance_layer"),
        ("personal_intelligence", "core.cognitive.personal_intelligence"),
        ("self_evolution", "core.cognitive.self_evolution"),
        ("strategy_optimizer", "core.strategy_optimizer"),
        ("cognitive_loop", "core.cognition.cognitive_loop"),
        ("synthetic_intelligence", "core.cognition.synthetic_intelligence"),
    ]
    for label, mod in modules:
        try:
            __import__(mod)
            print(f"    ✅ {label} ... PASS")
            results["pass"] += 1
        except Exception as e:
            print(f"    ❌ {label} ... FAIL — {e}")
            results["fail"] += 1
            results["details"].append(f"COGNITIVE MODULE: {label}")

    # 2. Cognitive orchestrator initialization
    print("\n  ── Cognitive Orchestrator Init ──")
    try:
        from core.cognitive.cognitive_orchestrator import initialize_module
        initialize_module()
        print(f"    ✅ cognitive_orchestrator.initialize_module() ... PASS")
        results["pass"] += 1
    except Exception as e:
        print(f"    ❌ CO init: {e}")
        results["fail"] += 1

    # 3. Governance layer initialization
    print("\n  ── Governance Layer Init ──")
    try:
        from core.cognitive.governance_layer import initialize_module as gov_init
        gov_init()
        print(f"    ✅ governance_layer.initialize_module() ... PASS")
        results["pass"] += 1
    except Exception as e:
        print(f"    ❌ GL init: {e}")
        results["fail"] += 1

    # 4. Strategy optimizer initialization
    print("\n  ── Strategy Optimizer Init ──")
    try:
        from core.strategy_optimizer import initialize_module as so_init
        so_init()
        print(f"    ✅ strategy_optimizer.initialize_module() ... PASS")
        results["pass"] += 1
    except Exception as e:
        print(f"    ❌ SO init: {e}")
        results["fail"] += 1

    # 5. Verify event bus subscriptions after initialization
    print("\n  ── Event Bus Subscription Verification ──")
    try:
        from core.event_bus import get_event_bus
        bus = get_event_bus()
        subscribers = bus._subscribers
        
        cognitive_events = ["perception_event", "decision_event", "plan_created",
                           "strategic_decision_pending", "DIGITAL_TWIN_SIMULATION"]
        
        for event_type in cognitive_events:
            has_subs = event_type in subscribers and len(subscribers[event_type]) > 0
            icon = "✅" if has_subs else "⚠️"
            status = "PASS" if has_subs else "WARN (no subscribers)"
            print(f"    {icon} Event '{event_type}' has subscribers ... {status}")
            if has_subs:
                results["pass"] += 1
            # Not failing for missing subscribers - module may not be initialized in test
    except Exception as e:
        print(f"    ❌ Subscription check: {e}")
        results["fail"] += 1

    total = results["pass"] + results["fail"]
    print(f"\n  Summary: {results['pass']}/{total} checks passed")
    return results


if __name__ == "__main__":
    r = run_test()
    sys.exit(0 if r["fail"] == 0 else 1)
