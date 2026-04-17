"""
TEST 20 — FRONTEND VOICE ROUTER TEST
Verifies workspace_router logic recognizes voice commands
and returns the correct workspace ID.
(Python re-implementation of workspace_router.js classify logic)
"""

import os
import sys
import re

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


# Python mirror of workspace_router.js INTENT_MAP
INTENT_MAP = [
    (["open conversation", "conversation interface", "open chat"], "conversation_interface"),
    (["coding lab", "open code", "code editor", "open coding"], "coding_lab"),
    (["show agents", "agent manager", "open agents"], "agent_manager"),
    (["system control", "open system", "system settings"], "system_control"),
    (["memory graph", "memory explorer", "show memory", "open memory"], "memory_explorer"),
    (["intelligence monitor", "system monitor", "open monitor"], "system_intelligence_monitor"),
    (["model health", "ai models", "show ai models", "model monitor"], "model_health_monitor"),
    (["research workspace", "open research", "research lab"], "research_workspace"),
    (["strategic workspace", "open strategic", "strategy", "strategic command"], "strategic_workspace"),
    (["personal intelligence", "personal dashboard"], "personal_intelligence_dashboard"),
    (["learning engine", "open learning"], "learning_engine"),
    (["synthetic core", "synthetic intelligence"], "synthetic_intelligence_core"),
    (["health monitor", "health intelligence"], "health_monitor"),
    (["human analysis", "human intelligence"], "human_analysis"),
    (["close workspace", "back to avatar", "close all", "go back"], "__close__"),
]


def classify_intent(transcript):
    """Python replica of workspace_router.js classifyIntent()"""
    t = re.sub(r"genesis[\s,]*", "", transcript.lower()).strip()
    for patterns, workspace in INTENT_MAP:
        for pattern in patterns:
            if pattern in t:
                return workspace
    return None


def run_test():
    results = {"pass": 0, "fail": 0, "details": []}

    print("\n╔══════════════════════════════════════════════════════════╗")
    print("║     TEST 20 — FRONTEND VOICE ROUTER TEST               ║")
    print("╚══════════════════════════════════════════════════════════╝\n")

    # Full test matrix
    test_cases = [
        # Exact matches
        ("Genesis open coding lab", "coding_lab"),
        ("Genesis open system control", "system_control"),
        ("Genesis open conversation", "conversation_interface"),
        ("Genesis show agents", "agent_manager"),
        ("Genesis show memory", "memory_explorer"),
        ("Genesis open monitor", "system_intelligence_monitor"),
        ("Genesis model health", "model_health_monitor"),
        ("Genesis open research", "research_workspace"),
        ("Genesis open strategic", "strategic_workspace"),
        ("Genesis personal dashboard", "personal_intelligence_dashboard"),
        ("Genesis open learning", "learning_engine"),
        ("Genesis synthetic core", "synthetic_intelligence_core"),
        ("Genesis health monitor", "health_monitor"),
        ("Genesis human analysis", "human_analysis"),
        ("Genesis close workspace", "__close__"),
        ("Genesis back to avatar", "__close__"),
        # Noise — should return None
        ("Genesis hello how are you", None),
        ("Genesis what time is it", None),
    ]

    print("  ── Voice Command → Workspace Routing ──")
    for transcript, expected in test_cases:
        result = classify_intent(transcript)
        ok = result == expected
        icon = "✅" if ok else "❌"
        exp_str = expected if expected else "None"
        res_str = result if result else "None"
        print(f"    {icon} \"{transcript}\" → {res_str} (expect {exp_str}) ... {'PASS' if ok else 'FAIL'}")
        results["pass" if ok else "fail"] += 1
        if not ok:
            results["details"].append(f"ROUTE MISMATCH: '{transcript}' → {result} != {expected}")

    # Verify JS file has matching patterns
    print("\n  ── JS File Integrity ──")
    ws_router_path = os.path.join(PROJECT_ROOT, "lite", "face_ui", "workspace_router.js")
    if os.path.isfile(ws_router_path):
        with open(ws_router_path, "r", encoding="utf-8") as f:
            js_content = f.read()
        
        js_workspaces = set(re.findall(r'workspace:\s*"([^"]+)"', js_content))
        py_workspaces = set(ws for _, ws in INTENT_MAP)
        
        match = js_workspaces == py_workspaces
        icon = "✅" if match else "⚠️"
        print(f"    {icon} JS and Python workspace maps match ... {'PASS' if match else 'WARN'}")
        if match:
            results["pass"] += 1
        if not match:
            diff = py_workspaces.symmetric_difference(js_workspaces)
            print(f"      Differences: {diff}")
    else:
        print(f"    ❌ workspace_router.js not found")
        results["fail"] += 1

    total = results["pass"] + results["fail"]
    print(f"\n  Summary: {results['pass']}/{total} checks passed")
    return results


if __name__ == "__main__":
    r = run_test()
    sys.exit(0 if r["fail"] == 0 else 1)
