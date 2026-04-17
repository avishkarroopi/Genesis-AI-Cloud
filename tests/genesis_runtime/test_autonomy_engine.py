"""
TEST 19 — AUTONOMY ENGINE TEST
Verifies:
- autonomous_engine module
- automation_engine module
- Autonomous loop can reference planner
- Automation webhook interface
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
    print("║       TEST 19 — AUTONOMY ENGINE TEST                   ║")
    print("╚══════════════════════════════════════════════════════════╝\n")

    # 1. Autonomous engine import
    print("  ── Autonomous Engine ──")
    try:
        from core.autonomous_engine import AutonomousReasoningEngine, TaskPriority
        
        assert TaskPriority.LOW == 3
        assert TaskPriority.NORMAL == 2
        assert TaskPriority.HIGH == 1
        assert TaskPriority.CRITICAL == 0
        print(f"    ✅ AutonomousReasoningEngine imported ... PASS")
        print(f"    ✅ TaskPriority levels correct ... PASS")
        results["pass"] += 2
    except Exception as e:
        print(f"    ❌ Autonomous engine: {e}")
        results["fail"] += 1
        results["details"].append(f"AUTONOMOUS: {e}")

    # 2. Cognitive loop (underlying engine)
    print("\n  ── Cognitive Loop ──")
    try:
        from core.cognition.cognitive_loop import CognitiveLoop, get_cognitive_loop
        loop = get_cognitive_loop()
        assert loop is not None
        print(f"    ✅ CognitiveLoop singleton ... PASS")
        results["pass"] += 1
    except Exception as e:
        print(f"    ❌ Cognitive loop: {e}")
        results["fail"] += 1

    # 3. Automation engine
    print("\n  ── Automation Engine ──")
    try:
        from core.automation_engine import trigger_webhook, run_workflow, get_workflows, execute_action, send_n8n_command

        funcs = [
            ("trigger_webhook", trigger_webhook),
            ("run_workflow", run_workflow),
            ("get_workflows", get_workflows),
            ("execute_action", execute_action),
            ("send_n8n_command", send_n8n_command),
        ]
        for name, fn in funcs:
            ok = callable(fn)
            icon = "✅" if ok else "❌"
            print(f"    {icon} {name}() callable ... {'PASS' if ok else 'FAIL'}")
            results["pass" if ok else "fail"] += 1
    except Exception as e:
        print(f"    ❌ Automation engine: {e}")
        results["fail"] += 1

    # 4. Webhook trigger (without actual n8n — should return gracefully)
    print("\n  ── Webhook Trigger (No n8n) ──")
    try:
        result = trigger_webhook({"test": "data"})
        assert isinstance(result, str)
        print(f"    ✅ trigger_webhook() → '{result}' ... PASS")
        results["pass"] += 1
    except Exception as e:
        print(f"    ❌ Webhook trigger: {e}")
        results["fail"] += 1

    # 5. Get workflows
    print("\n  ── Get Workflows ──")
    try:
        workflows = get_workflows()
        assert isinstance(workflows, list)
        print(f"    ✅ get_workflows() → {workflows} ... PASS")
        results["pass"] += 1
    except Exception as e:
        print(f"    ❌ Get workflows: {e}")
        results["fail"] += 1

    # 6. Automation bridge
    print("\n  ── Automation Bridge ──")
    try:
        from core.automation_bridge import generate_ai_response
        assert callable(generate_ai_response)
        print(f"    ✅ automation_bridge importable ... PASS")
        results["pass"] += 1
    except Exception as e:
        print(f"    ❌ Automation bridge: {e}")
        results["fail"] += 1

    total = results["pass"] + results["fail"]
    print(f"\n  Summary: {results['pass']}/{total} checks passed")
    return results


if __name__ == "__main__":
    r = run_test()
    sys.exit(0 if r["fail"] == 0 else 1)
