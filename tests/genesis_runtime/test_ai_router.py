"""
TEST 13 — AI ROUTER TEST
Verifies:
- AI router loads correctly
- Intent classification works
- Routing decision model exists
- Model constants are set
- Keyword task lists are populated
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
    print("║          TEST 13 — AI ROUTER TEST                      ║")
    print("╚══════════════════════════════════════════════════════════╝\n")

    # 1. Import
    print("  ── AI Router Import ──")
    try:
        from core.ai_router import (
            _classify_intent, route_ai_request, analyze_routing,
            RoutingDecision, CODING_TASKS, RESEARCH_TASKS,
            REASONING_TASKS, AUTOMATION_TASKS, MEMORY_TASKS,
            OR_CODING_MODEL, OR_REASONING_MODEL, OLLAMA_FALLBACK_MODEL,
            warmup_models
        )
        print(f"    ✅ AI Router imported ... PASS")
        results["pass"] += 1
    except Exception as e:
        print(f"    ❌ AI Router import: {e}")
        results["fail"] += 1
        results["details"].append(f"ROUTER IMPORT: {e}")
        return results

    # 2. Model constants
    print("\n  ── Model Constants ──")
    constants = [
        ("OR_CODING_MODEL", OR_CODING_MODEL),
        ("OR_REASONING_MODEL", OR_REASONING_MODEL),
        ("OLLAMA_FALLBACK_MODEL", OLLAMA_FALLBACK_MODEL),
    ]
    for name, val in constants:
        ok = val is not None and len(val) > 0
        icon = "✅" if ok else "❌"
        print(f"    {icon} {name} = '{val}' ... {'PASS' if ok else 'FAIL'}")
        results["pass" if ok else "fail"] += 1

    # 3. Keyword task list integrity
    print("\n  ── Task Keyword Lists ──")
    keyword_lists = [
        ("CODING_TASKS", CODING_TASKS),
        ("RESEARCH_TASKS", RESEARCH_TASKS),
        ("REASONING_TASKS", REASONING_TASKS),
        ("AUTOMATION_TASKS", AUTOMATION_TASKS),
        ("MEMORY_TASKS", MEMORY_TASKS),
    ]
    for name, lst in keyword_lists:
        ok = isinstance(lst, list) and len(lst) > 0
        icon = "✅" if ok else "❌"
        print(f"    {icon} {name} ({len(lst)} keywords) ... {'PASS' if ok else 'FAIL'}")
        results["pass" if ok else "fail"] += 1

    # 4. Intent classification exhaustive test
    print("\n  ── Intent Classification ──")
    test_cases = [
        ("write a python script", "CODING"),
        ("debug this function", "CODING"),
        ("explain how gravity works", "RESEARCH"),
        ("analyze market trends", "RESEARCH"),
        ("evaluate pros and cons", "REASONING"),
        ("create a strategy for growth", "REASONING"),
        ("open my browser", "AUTOMATION"),
        ("launch the application", "AUTOMATION"),
        ("remember my name is Alice", "MEMORY"),
        ("recall my last meeting", "MEMORY"),
        ("hello there", "GENERAL"),
        ("good morning", "GENERAL"),
    ]
    for cmd, expected in test_cases:
        result = _classify_intent(cmd)
        ok = result == expected
        icon = "✅" if ok else "❌"
        print(f"    {icon} \"{cmd[:35]}\" → {result} (expect {expected}) ... {'PASS' if ok else 'FAIL'}")
        results["pass" if ok else "fail"] += 1
        if not ok:
            results["details"].append(f"INTENT: '{cmd}' → {result} != {expected}")

    # 5. RoutingDecision structure
    print("\n  ── RoutingDecision Structure ──")
    try:
        rd = RoutingDecision(intent="TEST", model="test-model", use_planner=True, use_tools=False)
        assert rd.intent == "TEST"
        assert rd.model == "test-model"
        assert rd.use_planner is True
        assert rd.use_tools is False
        print(f"    ✅ RoutingDecision object ... PASS")
        results["pass"] += 1
    except Exception as e:
        print(f"    ❌ RoutingDecision: {e}")
        results["fail"] += 1

    # 6. Warmup models
    print("\n  ── Model Warmup ──")
    try:
        result = warmup_models()
        print(f"    ✅ warmup_models() → {result} ... PASS")
        results["pass"] += 1
    except Exception as e:
        print(f"    ❌ Warmup: {e}")
        results["fail"] += 1

    total = results["pass"] + results["fail"]
    print(f"\n  Summary: {results['pass']}/{total} checks passed")
    return results


if __name__ == "__main__":
    r = run_test()
    sys.exit(0 if r["fail"] == 0 else 1)
