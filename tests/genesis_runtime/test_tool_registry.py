"""
TEST 7 — TOOL REGISTRY TEST
Verifies:
- Tool registry singleton loads
- Tools can be registered
- Tool execution works
- Tool type enum is complete
- Existing tool modules import
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
    print("║         TEST 7 — TOOL REGISTRY TEST                    ║")
    print("╚══════════════════════════════════════════════════════════╝\n")

    # 1. Import and singleton
    print("  ── Tool Registry Singleton ──")
    try:
        from core.tool_registry import get_tool_registry, ToolRegistry, ToolType, Tool, ToolParameter
        registry = get_tool_registry()
        assert isinstance(registry, ToolRegistry), "Singleton is not a ToolRegistry"
        print(f"    ✅ ToolRegistry singleton ... PASS")
        results["pass"] += 1
    except Exception as e:
        print(f"    ❌ ToolRegistry import: {e}")
        results["fail"] += 1
        results["details"].append(f"REGISTRY IMPORT: {e}")
        return results

    # 2. ToolType enum completeness
    print("\n  ── ToolType Enum ──")
    expected_types = [
        "FILE_OPERATION", "VISION_QUERY", "MEMORY_QUERY", "WEB_SEARCH",
        "COMPUTATION", "SENSOR_READ", "ACTUATOR_CONTROL", "SYSTEM_COMMAND"
    ]
    for tt in expected_types:
        found = hasattr(ToolType, tt)
        icon = "✅" if found else "❌"
        print(f"    {icon} ToolType.{tt} ... {'PASS' if found else 'FAIL'}")
        results["pass" if found else "fail"] += 1

    # 3. Register and execute a test tool
    print("\n  ── Tool Registration & Execution ──")
    try:
        def _dummy_tool(query="test"):
            return f"Executed with: {query}"

        tool = registry.register_tool(
            tool_id="test_runtime_tool",
            name="Runtime Test Tool",
            description="A tool for testing the registry",
            tool_type=ToolType.COMPUTATION,
            callable_func=_dummy_tool,
            parameters=[ToolParameter(name="query", param_type=str, required=False)],
        )
        assert tool is not None
        assert registry.get_tool("test_runtime_tool") is not None
        print(f"    ✅ Tool registration ... PASS")
        results["pass"] += 1

        # Execute
        result = asyncio.run(registry.execute_tool("test_runtime_tool", query="hello"))
        assert "Executed with: hello" in result
        print(f"    ✅ Tool execution ... PASS")
        results["pass"] += 1

        # Stats
        stats = registry.get_tool_stats("test_runtime_tool")
        assert stats is not None
        assert stats["usage_count"] >= 1
        print(f"    ✅ Tool stats tracking ... PASS")
        results["pass"] += 1

        # Clean up
        registry.disable_tool("test_runtime_tool")
        tool_obj = registry.get_tool("test_runtime_tool")
        assert not tool_obj.enabled
        print(f"    ✅ Tool disable/enable ... PASS")
        results["pass"] += 1
        registry.enable_tool("test_runtime_tool")

    except Exception as e:
        print(f"    ❌ Tool registration/execution: {e}")
        results["fail"] += 1
        results["details"].append(f"TOOL EXEC: {e}")

    # 4. Existing tool modules
    print("\n  ── Tool Module Imports ──")
    tool_modules = [
        ("Advanced File Tool", "core.tools.advanced_file_tool"),
        ("Web Research Tool", "core.tools.web_research_tool"),
        ("Email Tool", "core.tools.email_tool"),
        ("Calendar Tool", "core.tools.calendar_tool"),
        ("Messaging Tool", "core.tools.messaging_tool"),
        ("Shell Tool", "core.tools.shell_tool"),
        ("Script Tool", "core.tools.script_tool"),
        ("System Diagnostics", "core.tools.system_diagnostics"),
        ("Init Tools", "core.tools.init_tools"),
    ]
    for label, mod in tool_modules:
        try:
            __import__(mod)
            print(f"    ✅ {label} ... PASS")
            results["pass"] += 1
        except Exception as e:
            print(f"    ❌ {label} ... FAIL — {e}")
            results["fail"] += 1
            results["details"].append(f"TOOL MODULE: {label}")

    # 5. List available tools
    print("\n  ── Available Tools Listing ──")
    try:
        tools_list = registry.list_available_tools()
        assert isinstance(tools_list, list)
        print(f"    ✅ {len(tools_list)} tools listed ... PASS")
        results["pass"] += 1
    except Exception as e:
        print(f"    ❌ Tool listing: {e}")
        results["fail"] += 1

    total = results["pass"] + results["fail"]
    print(f"\n  Summary: {results['pass']}/{total} checks passed")
    return results


if __name__ == "__main__":
    r = run_test()
    sys.exit(0 if r["fail"] == 0 else 1)
