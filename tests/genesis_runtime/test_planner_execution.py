"""
TEST 14 — PLANNER EXECUTION TEST
Verifies:
- planner module loads
- step_executor module loads
- execution_graph_builder module loads
- task_manager module loads
- Plan creation structure
- Task graph structure
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
    print("║       TEST 14 — PLANNER EXECUTION TEST                 ║")
    print("╚══════════════════════════════════════════════════════════╝\n")

    # 1. Module imports
    print("  ── Planner Module Imports ──")
    modules = [
        ("planner", "core.planner.planner"),
        ("step_executor", "core.planner.step_executor"),
        ("execution_graph_builder", "core.planner.execution_graph_builder"),
        ("task_manager", "core.planner.task_manager"),
    ]
    for label, mod in modules:
        try:
            __import__(mod)
            print(f"    ✅ {label} ... PASS")
            results["pass"] += 1
        except Exception as e:
            print(f"    ❌ {label} ... FAIL — {e}")
            results["fail"] += 1
            results["details"].append(f"PLANNER MODULE: {label}")

    # 2. Planner functions exist
    print("\n  ── Planner Function Verification ──")
    try:
        from core.planner.planner import create_plan, create_task_graph, create_steps, execute_plan, _extract_json
        funcs = [
            ("create_plan", create_plan),
            ("create_task_graph", create_task_graph),
            ("create_steps", create_steps),
            ("execute_plan", execute_plan),
            ("_extract_json", _extract_json),
        ]
        for name, fn in funcs:
            ok = callable(fn)
            icon = "✅" if ok else "❌"
            print(f"    {icon} {name}() callable ... {'PASS' if ok else 'FAIL'}")
            results["pass" if ok else "fail"] += 1
    except Exception as e:
        print(f"    ❌ Function import: {e}")
        results["fail"] += 1

    # 3. JSON extractor test
    print("\n  ── JSON Extractor ──")
    try:
        from core.planner.planner import _extract_json
        
        # Clean JSON
        result = _extract_json('{"steps": [{"id": 1, "description": "test"}]}')
        assert "steps" in result
        print(f"    ✅ Clean JSON extraction ... PASS")
        results["pass"] += 1

        # JSON in markdown
        result = _extract_json('```json\n{"steps": [{"id": 1, "description": "test"}]}\n```')
        assert "steps" in result
        print(f"    ✅ Markdown-wrapped JSON extraction ... PASS")
        results["pass"] += 1

        # Invalid JSON
        try:
            _extract_json("not json at all")
            print(f"    ❌ Invalid JSON should raise ValueError ... FAIL")
            results["fail"] += 1
        except ValueError:
            print(f"    ✅ Invalid JSON raises ValueError ... PASS")
            results["pass"] += 1
    except Exception as e:
        print(f"    ❌ JSON extractor: {e}")
        results["fail"] += 1

    # 4. ExecutionGraphBuilder initialization
    print("\n  ── ExecutionGraphBuilder ──")
    try:
        from core.planner.execution_graph_builder import ExecutionGraphBuilder, initialize_module
        builder = ExecutionGraphBuilder()
        assert builder is not None
        print(f"    ✅ ExecutionGraphBuilder instantiation ... PASS")
        results["pass"] += 1
        
        initialize_module()
        print(f"    ✅ initialize_module() ... PASS")
        results["pass"] += 1
    except Exception as e:
        print(f"    ❌ GraphBuilder: {e}")
        results["fail"] += 1

    # 5. TaskManager
    print("\n  ── Task Manager ──")
    try:
        from core.planner.task_manager import manager, TaskStep
        assert manager is not None
        ts = TaskStep(id=1, description="Test step", action="test")
        assert ts.id == 1
        assert ts.description == "Test step"
        print(f"    ✅ TaskManager + TaskStep ... PASS")
        results["pass"] += 1
    except Exception as e:
        print(f"    ❌ TaskManager: {e}")
        results["fail"] += 1

    total = results["pass"] + results["fail"]
    print(f"\n  Summary: {results['pass']}/{total} checks passed")
    return results


if __name__ == "__main__":
    r = run_test()
    sys.exit(0 if r["fail"] == 0 else 1)
