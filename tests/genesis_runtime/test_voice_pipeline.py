"""
TEST 5 — VOICE PIPELINE TEST
Simulates a voice transcript and verifies:
- Workspace routing from transcript
- Transcript normalization
- Command recognition for workspace navigation
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
    print("║         TEST 5 — VOICE PIPELINE TEST                   ║")
    print("╚══════════════════════════════════════════════════════════╝\n")

    # 1. Voice pipeline adapter exists and imports
    print("  ── Voice Pipeline Adapter ──")
    try:
        from server.voice_pipeline_adapter import process_audio_chunk
        assert callable(process_audio_chunk)
        print(f"    ✅ process_audio_chunk importable ... PASS")
        results["pass"] += 1
    except Exception as e:
        print(f"    ❌ Voice pipeline import: {e}")
        results["fail"] += 1
        results["details"].append(f"PIPELINE IMPORT: {e}")

    # 2. AI Router intent classification (simulated transcript)
    print("\n  ── Intent Classification Pipeline ──")
    try:
        from core.ai_router import _classify_intent
        test_cases = [
            ("Genesis open coding lab", "AUTOMATION"),
            ("explain quantum computing", "RESEARCH"),
            ("write a python function to sort", "CODING"),
            ("evaluate pros and cons of microservices", "REASONING"),
            ("remember my birthday is June 5th", "MEMORY"),
            ("hello Genesis", "GENERAL"),
        ]
        for transcript, expected in test_cases:
            result = _classify_intent(transcript)
            ok = result == expected
            icon = "✅" if ok else "❌"
            print(f"    {icon} \"{transcript[:40]}...\" → {result} (expect {expected}) ... {'PASS' if ok else 'FAIL'}")
            results["pass" if ok else "fail"] += 1
            if not ok:
                results["details"].append(f"INTENT MISMATCH: '{transcript}' → {result} (expected {expected})")
    except Exception as e:
        print(f"    ❌ Intent classifier test: {e}")
        results["fail"] += 1
        results["details"].append(f"INTENT CLASSIFY FAIL: {e}")

    # 3. Workspace Router simulation (JS logic replicated in Python for test)
    print("\n  ── Workspace Routing Simulation ──")
    INTENT_MAP = [
        (["open conversation", "conversation interface", "open chat"], "conversation_interface"),
        (["coding lab", "open code", "code editor", "open coding"], "coding_lab"),
        (["show agents", "agent manager", "open agents"], "agent_manager"),
        (["system control", "open system", "system settings"], "system_control"),
        (["memory graph", "memory explorer", "show memory", "open memory"], "memory_explorer"),
        (["intelligence monitor", "system monitor", "open monitor"], "system_intelligence_monitor"),
        (["model health", "ai models", "show ai models"], "model_health_monitor"),
        (["research workspace", "open research"], "research_workspace"),
        (["strategic workspace", "open strategic", "strategy"], "strategic_workspace"),
        (["personal intelligence", "personal dashboard"], "personal_intelligence_dashboard"),
        (["learning engine", "open learning"], "learning_engine"),
        (["synthetic core", "synthetic intelligence"], "synthetic_intelligence_core"),
        (["health monitor", "health intelligence"], "health_monitor"),
        (["human analysis", "human intelligence"], "human_analysis"),
    ]

    def classify_workspace(transcript):
        t = transcript.lower().replace("genesis", "").strip()
        for patterns, workspace in INTENT_MAP:
            for pattern in patterns:
                if pattern in t:
                    return workspace
        return None

    workspace_tests = [
        ("Genesis open coding lab", "coding_lab"),
        ("Genesis open system control", "system_control"),
        ("Genesis show memory", "memory_explorer"),
        ("Genesis open research", "research_workspace"),
    ]

    for transcript, expected_ws in workspace_tests:
        ws = classify_workspace(transcript)
        ok = ws == expected_ws
        icon = "✅" if ok else "❌"
        print(f"    {icon} \"{transcript}\" → {ws} (expect {expected_ws}) ... {'PASS' if ok else 'FAIL'}")
        results["pass" if ok else "fail"] += 1
        if not ok:
            results["details"].append(f"WS ROUTE MISMATCH: '{transcript}'")

    total = results["pass"] + results["fail"]
    print(f"\n  Summary: {results['pass']}/{total} checks passed")
    return results


if __name__ == "__main__":
    r = run_test()
    sys.exit(0 if r["fail"] == 0 else 1)
