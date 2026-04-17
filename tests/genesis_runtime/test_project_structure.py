"""
TEST 1 — PROJECT STRUCTURE VERIFICATION
Verifies that all critical GENESIS directories and modules exist.
"""

import os
import sys

# ── Path Setup ────────────────────────────────────────────────────────────────
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


# ── Critical directories that MUST exist ──────────────────────────────────────
REQUIRED_DIRS = [
    "core",
    "core/agents",
    "core/tools",
    "core/memory",
    "core/digital_twin",
    "core/self_improvement",
    "core/planner",
    "core/cognitive",
    "core/security",
    "lite/face_ui",
    "server",
    "shared",
    "core/cognition",
    "core/ai_monitor",
    "core/ai_telemetry",
    "core/awareness",
    "core/creativity_engine",
    "core/executive_control",
    "core/intelligence",
    "core/monitoring",
    "core/observability",
    "core/perception",
    "core/research",
]

# ── Critical Python files that MUST exist ─────────────────────────────────────
REQUIRED_FILES = [
    "core/event_bus.py",
    "core/tool_registry.py",
    "core/agent_registry.py",
    "core/ai_router.py",
    "core/brain_chain.py",
    "core/genesis_voice.py",
    "core/knowledge_graph.py",
    "core/monitoring.py",
    "core/learning_engine.py",
    "core/autonomous_engine.py",
    "core/automation_engine.py",
    "core/strategy_optimizer.py",
    "core/behavior_engine.py",
    "core/user_model.py",
    "core/world_model.py",
    "core/emotion_engine.py",
    "core/plugin_system.py",
    "core/skill_engine.py",
    "server/api.py",
    "server/voice_ws.py",
    "server/voice_pipeline_adapter.py",
    "core/security/hardrock_security.py",
    "core/security/permissions.py",
    "core/security/safe_mode.py",
    "core/security/tool_sandbox.py",
    "core/digital_twin/behavior_simulator.py",
    "core/self_improvement/self_improvement_engine.py",
    "core/cognitive/cognitive_orchestrator.py",
    "core/cognitive/governance_layer.py",
    "core/planner/planner.py",
    "core/planner/step_executor.py",
    "core/planner/execution_graph_builder.py",
    "core/memory/memory_store.py",
    "core/memory/memory_embed.py",
    "core/memory/memory_search.py",
    "lite/face_ui/workspace_router.js",
]


def run_test():
    """Run project structure verification."""
    results = {"pass": 0, "fail": 0, "details": []}

    print("\n╔══════════════════════════════════════════════════════════╗")
    print("║        TEST 1 — PROJECT STRUCTURE VERIFICATION         ║")
    print("╚══════════════════════════════════════════════════════════╝\n")

    # Check directories
    print("  ── Required Directories ──")
    for d in REQUIRED_DIRS:
        full = os.path.join(PROJECT_ROOT, d.replace("/", os.sep))
        exists = os.path.isdir(full)
        status = "PASS" if exists else "FAIL"
        icon = "✅" if exists else "❌"
        print(f"    {icon} {d}/ ... {status}")
        results["pass" if exists else "fail"] += 1
        if not exists:
            results["details"].append(f"MISSING DIR: {d}/")

    print()

    # Check files
    print("  ── Required Files ──")
    for f in REQUIRED_FILES:
        full = os.path.join(PROJECT_ROOT, f.replace("/", os.sep))
        exists = os.path.isfile(full)
        status = "PASS" if exists else "FAIL"
        icon = "✅" if exists else "❌"
        print(f"    {icon} {f} ... {status}")
        results["pass" if exists else "fail"] += 1
        if not exists:
            results["details"].append(f"MISSING FILE: {f}")

    total = results["pass"] + results["fail"]
    print(f"\n  Summary: {results['pass']}/{total} checks passed")

    if results["details"]:
        print("  Missing modules:")
        for d in results["details"]:
            print(f"    ⚠️  {d}")

    return results


if __name__ == "__main__":
    r = run_test()
    sys.exit(0 if r["fail"] == 0 else 1)
