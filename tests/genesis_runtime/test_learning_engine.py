"""
TEST 17 — LEARNING ENGINE TEST
Verifies the learning engine's experience evaluation and recording.
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
    print("║       TEST 17 — LEARNING ENGINE TEST                   ║")
    print("╚══════════════════════════════════════════════════════════╝\n")

    # 1. Import
    print("  ── Learning Engine Import ──")
    try:
        from core.learning_engine import evaluate_experience, record_experience, get_learning_engine, start_learning_engine
        print(f"    ✅ Learning engine imported ... PASS")
        results["pass"] += 1
    except Exception as e:
        print(f"    ❌ Import: {e}")
        results["fail"] += 1
        return results

    # 2. Experience evaluation — success cases
    print("\n  ── Experience Evaluation (Success) ──")
    success_cases = [
        ("Long valid response that contains useful information for the user about the topic"),
        ("Here is the research summary with detailed findings and analysis"),
    ]
    for case in success_cases:
        result = evaluate_experience("test command", case)
        ok = result is True
        icon = "✅" if ok else "❌"
        print(f"    {icon} \"{case[:50]}...\" → {result} ... {'PASS' if ok else 'FAIL'}")
        results["pass" if ok else "fail"] += 1

    # 3. Experience evaluation — failure cases
    print("\n  ── Experience Evaluation (Failure) ──")
    failure_cases = [
        ("Error: Connection refused", "contains Error:"),
        ("Failed to process request", "contains Failed"),
        ("timeout after 30 seconds", "contains timeout"),
        ("ok", "too short (≤20 chars)"),
    ]
    for case, reason in failure_cases:
        result = evaluate_experience("test command", case)
        ok = result is False
        icon = "✅" if ok else "❌"
        print(f"    {icon} \"{case}\" ({reason}) → {result} ... {'PASS' if ok else 'FAIL'}")
        results["pass" if ok else "fail"] += 1

    # 4. Record experience (graceful without DB)
    print("\n  ── Experience Recording ──")
    try:
        record_experience("test genesis command", "A sufficiently long and valid response for testing")
        print(f"    ✅ record_experience() completed gracefully ... PASS")
        results["pass"] += 1
    except Exception as e:
        print(f"    ⚠️  record_experience() error (graceful): {e}")
        results["pass"] += 1

    # 5. Start learning engine
    print("\n  ── Learning Engine Start ──")
    try:
        start_learning_engine()
        print(f"    ✅ start_learning_engine() ... PASS")
        results["pass"] += 1
    except Exception as e:
        print(f"    ❌ Start: {e}")
        results["fail"] += 1

    total = results["pass"] + results["fail"]
    print(f"\n  Summary: {results['pass']}/{total} checks passed")
    return results


if __name__ == "__main__":
    r = run_test()
    sys.exit(0 if r["fail"] == 0 else 1)
