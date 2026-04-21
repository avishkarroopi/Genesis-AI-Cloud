"""
TEST — Phase 3 AI Router Tool-Calling
Verifies AI router has tool schemas and tool dispatch works.
"""

import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

os.environ.setdefault("CLOUD_MODE", "true")


def test_tool_schemas_defined():
    """TOOL_SCHEMAS should be defined with at least 5 tools."""
    from core.ai_router import TOOL_SCHEMAS
    assert isinstance(TOOL_SCHEMAS, list)
    assert len(TOOL_SCHEMAS) >= 5, f"Only {len(TOOL_SCHEMAS)} tool schemas defined"
    # All schemas should have function.name
    for schema in TOOL_SCHEMAS:
        assert "function" in schema
        assert "name" in schema["function"]


def test_tool_schema_names():
    """Expected tool names should be present."""
    from core.ai_router import TOOL_SCHEMAS
    names = [s["function"]["name"] for s in TOOL_SCHEMAS]
    expected = ["system_time", "web_search", "file_operations", "code_execution", "send_message", "calendar_event", "send_email"]
    for name in expected:
        assert name in names, f"Missing tool schema: {name}"


def test_dispatch_system_time():
    """Tool dispatch for system_time should return current time."""
    from core.ai_router import _dispatch_tool_call
    result = _dispatch_tool_call("system_time", {})
    assert "Current time:" in result


def test_classify_intent_preserved():
    """_classify_intent should still work as fallback."""
    from core.ai_router import _classify_intent
    assert _classify_intent("research quantum computing") == "RESEARCH"
    assert _classify_intent("open browser") == "AUTOMATION"
    assert _classify_intent("write python function") == "CODING"
    assert _classify_intent("hello there") == "GENERAL"


def test_routing_decision_structure():
    """analyze_routing should return a RoutingDecision."""
    from core.ai_router import analyze_routing
    decision = analyze_routing("what is the weather today")
    assert hasattr(decision, "intent")
    assert hasattr(decision, "use_planner")
    assert hasattr(decision, "use_tools")


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
