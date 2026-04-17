#!/usr/bin/env python3
"""
GENESIS RUNTIME TEST SUITE — MASTER RUNNER
===========================================
Runs all test modules, collects results, and generates a forensic audit report.
Usage: python tests/genesis_runtime/run_all_tests.py
"""

import os
import sys
import time
import importlib
import traceback
from datetime import datetime

# ── Path setup ────────────────────────────────────────────────────────────────
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

os.environ.setdefault("CLOUD_MODE", "true")
os.environ.setdefault("GENESIS_SAFE_MODE", "true")

# ── Test Module Registry ─────────────────────────────────────────────────────
TEST_MODULES = [
    ("Project Structure",       "tests.genesis_runtime.test_project_structure"),
    ("Backend Boot",            "tests.genesis_runtime.test_backend_boot"),
    ("API Routes",              "tests.genesis_runtime.test_fastapi_routes"),
    ("WebSocket Voice",         "tests.genesis_runtime.test_websocket_voice"),
    ("Voice Pipeline",          "tests.genesis_runtime.test_voice_pipeline"),
    ("Agent System",            "tests.genesis_runtime.test_agent_system"),
    ("Tool Registry",           "tests.genesis_runtime.test_tool_registry"),
    ("Event Bus",               "tests.genesis_runtime.test_event_bus"),
    ("Memory System",           "tests.genesis_runtime.test_memory_system"),
    ("Digital Twin",            "tests.genesis_runtime.test_digital_twin"),
    ("Self Improvement",        "tests.genesis_runtime.test_self_improvement_engine"),
    ("Cognitive System",        "tests.genesis_runtime.test_cognitive_orchestrator"),
    ("AI Router",               "tests.genesis_runtime.test_ai_router"),
    ("Planner Execution",       "tests.genesis_runtime.test_planner_execution"),
    ("Workspace System",        "tests.genesis_runtime.test_workspace_api"),
    ("System Monitor",          "tests.genesis_runtime.test_system_monitor"),
    ("Learning Engine",         "tests.genesis_runtime.test_learning_engine"),
    ("Security Layer",          "tests.genesis_runtime.test_security_layer"),
    ("Autonomy Engine",         "tests.genesis_runtime.test_autonomy_engine"),
    ("Voice Router",            "tests.genesis_runtime.test_governance_layer"),
    ("System Integration",      "tests.genesis_runtime.test_system_integration"),
]


def run_all():
    """Execute all test modules and collect results."""
    print("=" * 70)
    print("  GENESIS RUNTIME TEST SUITE — MASTER EXECUTION")
    print(f"  Timestamp: {datetime.now().isoformat()}")
    print(f"  Project:   {PROJECT_ROOT}")
    print("=" * 70)

    all_results = {}
    total_pass = 0
    total_fail = 0
    start_time = time.time()

    for test_name, module_path in TEST_MODULES:
        try:
            mod = importlib.import_module(module_path)
            result = mod.run_test()
            all_results[test_name] = result
            total_pass += result.get("pass", 0)
            total_fail += result.get("fail", 0)
        except Exception as e:
            print(f"\n  ❌ FATAL ERROR in {test_name}: {e}")
            traceback.print_exc()
            all_results[test_name] = {"pass": 0, "fail": 1, "details": [f"FATAL: {e}"]}
            total_fail += 1

    elapsed = time.time() - start_time

    # ── Summary Report ────────────────────────────────────────────────────
    print("\n")
    print("=" * 70)
    print("  GENESIS RUNTIME TEST SUITE — FINAL RESULTS")
    print("=" * 70)
    print()

    # Results table
    max_name = max(len(name) for name, _ in TEST_MODULES) + 2
    for test_name, _ in TEST_MODULES:
        r = all_results.get(test_name, {"pass": 0, "fail": 0})
        p, f = r.get("pass", 0), r.get("fail", 0)
        status = "PASS" if f == 0 else "FAIL"
        icon = "✅" if f == 0 else "❌"
        dots = "." * (max_name - len(test_name) + 4)
        print(f"  {icon} {test_name} {dots} {status}  ({p} passed, {f} failed)")

    print()
    print("─" * 70)
    total = total_pass + total_fail
    print(f"  Total Checks:  {total}")
    print(f"  Passed:        {total_pass}")
    print(f"  Failed:        {total_fail}")
    print(f"  Success Rate:  {(total_pass / total * 100) if total > 0 else 0:.1f}%")
    print(f"  Elapsed:       {elapsed:.2f}s")
    print("─" * 70)

    # ── Forensic Audit Report ─────────────────────────────────────────────
    print()
    print("=" * 70)
    print("  GENESIS FORENSIC AUDIT REPORT")
    print("=" * 70)

    # Calculate scores
    struct_r = all_results.get("Project Structure", {"pass": 0, "fail": 0})
    boot_r = all_results.get("Backend Boot", {"pass": 0, "fail": 0})
    api_r = all_results.get("API Routes", {"pass": 0, "fail": 0})
    voice_r = all_results.get("Voice Pipeline", {"pass": 0, "fail": 0})
    ws_voice_r = all_results.get("WebSocket Voice", {"pass": 0, "fail": 0})
    agent_r = all_results.get("Agent System", {"pass": 0, "fail": 0})
    tool_r = all_results.get("Tool Registry", {"pass": 0, "fail": 0})
    bus_r = all_results.get("Event Bus", {"pass": 0, "fail": 0})
    mem_r = all_results.get("Memory System", {"pass": 0, "fail": 0})
    dt_r = all_results.get("Digital Twin", {"pass": 0, "fail": 0})
    si_r = all_results.get("Self Improvement", {"pass": 0, "fail": 0})
    cog_r = all_results.get("Cognitive System", {"pass": 0, "fail": 0})
    router_r = all_results.get("AI Router", {"pass": 0, "fail": 0})
    plan_r = all_results.get("Planner Execution", {"pass": 0, "fail": 0})
    ws_r = all_results.get("Workspace System", {"pass": 0, "fail": 0})
    mon_r = all_results.get("System Monitor", {"pass": 0, "fail": 0})
    learn_r = all_results.get("Learning Engine", {"pass": 0, "fail": 0})
    sec_r = all_results.get("Security Layer", {"pass": 0, "fail": 0})
    aut_r = all_results.get("Autonomy Engine", {"pass": 0, "fail": 0})
    vr_r = all_results.get("Voice Router", {"pass": 0, "fail": 0})
    integ_r = all_results.get("System Integration", {"pass": 0, "fail": 0})

    def _score(r):
        t = r.get("pass", 0) + r.get("fail", 0)
        return (r.get("pass", 0) / t * 100) if t > 0 else 0

    # System stability = overall pass rate
    system_stability = (total_pass / total * 100) if total > 0 else 0

    # Backend readiness = boot + API + websocket
    backend_total_p = boot_r["pass"] + api_r["pass"] + ws_voice_r["pass"]
    backend_total = backend_total_p + boot_r["fail"] + api_r["fail"] + ws_voice_r["fail"]
    backend_readiness = (backend_total_p / backend_total * 100) if backend_total > 0 else 0

    # Voice pipeline
    voice_total_p = voice_r["pass"] + vr_r["pass"] + ws_voice_r["pass"]
    voice_total = voice_total_p + voice_r["fail"] + vr_r["fail"] + ws_voice_r["fail"]
    voice_status = (voice_total_p / voice_total * 100) if voice_total > 0 else 0

    # AI Architecture integrity = router + planner + cognitive + agents + tools + bus
    ai_total_p = router_r["pass"] + plan_r["pass"] + cog_r["pass"] + agent_r["pass"] + tool_r["pass"] + bus_r["pass"]
    ai_total = ai_total_p + router_r["fail"] + plan_r["fail"] + cog_r["fail"] + agent_r["fail"] + tool_r["fail"] + bus_r["fail"]
    ai_integrity = (ai_total_p / ai_total * 100) if ai_total > 0 else 0

    # Production readiness = weighted average
    prod_readiness = (system_stability * 0.3 + backend_readiness * 0.25 +
                      voice_status * 0.15 + ai_integrity * 0.3)

    print()
    print(f"  ┌─────────────────────────────────────┬────────────┐")
    print(f"  │ System Stability                     │ {system_stability:6.1f}%    │")
    print(f"  │ Backend Readiness                    │ {backend_readiness:6.1f}%    │")
    print(f"  │ Voice Pipeline Status                │ {voice_status:6.1f}%    │")
    print(f"  │ AI Architecture Integrity            │ {ai_integrity:6.1f}%    │")
    print(f"  │ Production Readiness                 │ {prod_readiness:6.1f}%    │")
    print(f"  └─────────────────────────────────────┴────────────┘")

    # ── Failure Details ───────────────────────────────────────────────────
    all_failures = []
    for test_name, r in all_results.items():
        for detail in r.get("details", []):
            all_failures.append(f"{test_name}: {detail}")

    if all_failures:
        print()
        print("  ── Failure Details ──")
        for f in all_failures[:30]:
            print(f"    ⚠️  {f}")

    # ── Risk Assessment ───────────────────────────────────────────────────
    print()
    print("  ── Risk Assessment ──")
    risks = []
    if sec_r.get("fail", 0) > 0:
        risks.append("🔴 CRITICAL: Security layer has failures — immediate review required")
    if bus_r.get("fail", 0) > 0:
        risks.append("🔴 CRITICAL: Event bus failures — core PubSub may be compromised")
    if boot_r.get("fail", 0) > 0:
        risks.append("🟡 HIGH: Backend boot issues — some modules fail to import")
    if mem_r.get("fail", 0) > 0:
        risks.append("🟡 MEDIUM: Memory system issues — DB connectivity may be required")
    if dt_r.get("fail", 0) > 0:
        risks.append("🟡 MEDIUM: Digital Twin issues — behavioral simulation degraded")
    if aut_r.get("fail", 0) > 0:
        risks.append("🟡 MEDIUM: Autonomy engine issues — autonomous operation may fail")
    if not risks:
        print("    ✅ No critical risks detected")
    else:
        for risk in risks:
            print(f"    {risk}")

    print()
    print("=" * 70)
    print(f"  AUDIT COMPLETE — {datetime.now().isoformat()}")
    print("=" * 70)
    print()

    return {
        "total_pass": total_pass,
        "total_fail": total_fail,
        "system_stability": system_stability,
        "backend_readiness": backend_readiness,
        "voice_status": voice_status,
        "ai_integrity": ai_integrity,
        "production_readiness": prod_readiness,
        "all_results": all_results,
        "failures": all_failures,
    }


if __name__ == "__main__":
    result = run_all()
    sys.exit(0 if result["total_fail"] == 0 else 1)
