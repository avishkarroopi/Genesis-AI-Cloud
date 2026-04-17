"""
TEST 15 — WORKSPACE SYSTEM TEST
Verifies that all 14 workspaces exist in the workspace router
and routing IDs are registered.
"""

import os
import sys
import re

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


EXPECTED_WORKSPACES = [
    "conversation_interface",
    "coding_lab",
    "agent_manager",
    "system_control",
    "memory_explorer",
    "system_intelligence_monitor",
    "model_health_monitor",
    "research_workspace",
    "strategic_workspace",
    "personal_intelligence_dashboard",
    "learning_engine",
    "synthetic_intelligence_core",
    "health_monitor",
    "human_analysis",
]


def run_test():
    results = {"pass": 0, "fail": 0, "details": []}

    print("\n╔══════════════════════════════════════════════════════════╗")
    print("║       TEST 15 — WORKSPACE SYSTEM TEST                  ║")
    print("╚══════════════════════════════════════════════════════════╝\n")

    # 1. workspace_router.js exists
    print("  ── Workspace Router File ──")
    ws_router_path = os.path.join(PROJECT_ROOT, "lite", "face_ui", "workspace_router.js")
    exists = os.path.isfile(ws_router_path)
    icon = "✅" if exists else "❌"
    print(f"    {icon} workspace_router.js exists ... {'PASS' if exists else 'FAIL'}")
    results["pass" if exists else "fail"] += 1

    if not exists:
        results["details"].append("MISSING: workspace_router.js")
        return results

    # 2. Read and parse workspace IDs from JS
    print("\n  ── Workspace IDs in Router ──")
    try:
        with open(ws_router_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Extract workspace IDs from JS
        found_workspaces = set(re.findall(r'workspace:\s*"([^"]+)"', content))

        for ws in EXPECTED_WORKSPACES:
            found = ws in found_workspaces
            icon = "✅" if found else "❌"
            print(f"    {icon} {ws} ... {'PASS' if found else 'FAIL'}")
            results["pass" if found else "fail"] += 1
            if not found:
                results["details"].append(f"MISSING WORKSPACE: {ws}")

        print(f"\n    Found {len(found_workspaces)} workspaces in router")

        # Check for __close__ special command
        has_close = "__close__" in found_workspaces
        icon = "✅" if has_close else "⚠️"
        print(f"    {icon} __close__ command ... {'PASS' if has_close else 'WARN'}")
        if has_close:
            results["pass"] += 1

    except Exception as e:
        print(f"    ❌ Router parsing: {e}")
        results["fail"] += 1
        results["details"].append(f"ROUTER PARSE: {e}")

    # 3. Workspace manager file
    print("\n  ── Workspace Manager ──")
    ws_mgr_path = os.path.join(PROJECT_ROOT, "lite", "face_ui", "workspace_manager.js")
    mgr_exists = os.path.isfile(ws_mgr_path)
    icon = "✅" if mgr_exists else "❌"
    print(f"    {icon} workspace_manager.js exists ... {'PASS' if mgr_exists else 'FAIL'}")
    results["pass" if mgr_exists else "fail"] += 1

    # 4. Workspace directories
    print("\n  ── Workspace Directories ──")
    ws_dir = os.path.join(PROJECT_ROOT, "lite", "face_ui", "workspaces")
    ws_dir_exists = os.path.isdir(ws_dir)
    icon = "✅" if ws_dir_exists else "❌"
    print(f"    {icon} workspaces/ directory exists ... {'PASS' if ws_dir_exists else 'FAIL'}")
    results["pass" if ws_dir_exists else "fail"] += 1

    if ws_dir_exists:
        subdirs = [d for d in os.listdir(ws_dir) if os.path.isdir(os.path.join(ws_dir, d))]
        print(f"    📂 Workspace subdirectories: {subdirs}")

    total = results["pass"] + results["fail"]
    print(f"\n  Summary: {results['pass']}/{total} checks passed")
    return results


if __name__ == "__main__":
    r = run_test()
    sys.exit(0 if r["fail"] == 0 else 1)
