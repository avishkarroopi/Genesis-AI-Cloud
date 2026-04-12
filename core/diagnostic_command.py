"""
GENESIS — System Diagnostic Command
Improvement 7: "Genesis system diagnostic" voice command handler.

Registered as a tool in tool_registry so brain_chain can invoke it.
Checks all subsystems and returns a spoken summary.
"""

import logging
import threading
from typing import Dict, Any

logger = logging.getLogger(__name__)


def run_system_diagnostic() -> Dict[str, Any]:
    """Run a full system diagnostic and return results."""
    results: Dict[str, Any] = {}

    # 1. Event Bus
    try:
        from core.event_bus import get_event_bus
        bus = get_event_bus()
        stats = bus.get_stats()
        results["event_bus"] = {
            "status": "PASS" if stats.get("running") else "FAIL",
            "queue_size": stats.get("queue_size", 0),
            "subscribers": sum(stats.get("subscribers", {}).values()),
        }
    except Exception as e:
        results["event_bus"] = {"status": "FAIL", "error": str(e)}

    # 2. Voice System
    try:
        thread_names = [t.name for t in threading.enumerate()]
        voice_alive = "VoiceSystem" in thread_names
        results["voice_system"] = {
            "status": "PASS" if voice_alive else "PARTIAL",
            "thread_alive": voice_alive,
        }
    except Exception as e:
        results["voice_system"] = {"status": "FAIL", "error": str(e)}

    # 3. Memory System
    try:
        from core.memory.memory_manager import search_memory
        test = search_memory("diagnostic test")
        results["memory_system"] = {"status": "PASS", "queryable": True}
    except Exception as e:
        results["memory_system"] = {"status": "FAIL", "error": str(e)}

    # 4. Knowledge Graph
    try:
        from core.knowledge_graph import get_knowledge_graph
        kg = get_knowledge_graph()
        stats = kg.get_stats()
        results["knowledge_graph"] = {
            "status": "PASS",
            "nodes": stats.get("total_nodes", 0),
            "relationships": stats.get("total_relationships", 0),
        }
    except Exception as e:
        results["knowledge_graph"] = {"status": "FAIL", "error": str(e)}

    # 5. World Model
    try:
        from core.world_model import get_world_model
        wm = get_world_model()
        stats = wm.get_stats()
        results["world_model"] = {"status": "PASS"}
    except Exception as e:
        results["world_model"] = {"status": "FAIL", "error": str(e)}

    # 6. Agents
    try:
        from core.agents.agent_manager import AgentManager
        results["agent_system"] = {"status": "PASS"}
    except Exception as e:
        results["agent_system"] = {"status": "PARTIAL", "error": str(e)}

    # 7. Prediction Engine
    try:
        from core.prediction import get_predictor
        results["prediction_engine"] = {"status": "PASS"}
    except Exception:
        try:
            from core.prediction.behavior_model import BehaviorModel
            results["prediction_engine"] = {"status": "PASS"}
        except Exception as e:
            results["prediction_engine"] = {"status": "PARTIAL", "error": str(e)}

    # 8. Automation
    try:
        from core import automation_engine
        results["automation"] = {"status": "PASS"}
    except Exception as e:
        results["automation"] = {"status": "FAIL", "error": str(e)}

    # 9. Face UI
    try:
        from core.face_bridge import is_connected
        results["face_ui"] = {
            "status": "PASS" if is_connected else "PARTIAL",
            "connected": is_connected,
        }
    except Exception as e:
        results["face_ui"] = {"status": "PARTIAL", "error": str(e)}

    # 10. Health Monitor
    try:
        from core.system_health_monitor import get_health_snapshot
        health = get_health_snapshot()
        results["health_monitor"] = {
            "status": "PASS",
            "cpu": health.get("cpu_percent"),
            "ram": health.get("ram_percent"),
        }
    except Exception as e:
        results["health_monitor"] = {"status": "PARTIAL", "error": str(e)}

    # Generate summary
    statuses = [v.get("status", "FAIL") for v in results.values()]
    pass_count = statuses.count("PASS")
    total = len(statuses)

    results["_summary"] = {
        "passed": pass_count,
        "total": total,
        "overall": "ALL SYSTEMS OPERATIONAL" if pass_count == total else f"{pass_count}/{total} systems operational",
    }

    return results


def diagnostic_spoken_summary() -> str:
    """Return a natural language diagnostic summary for voice output."""
    results = run_system_diagnostic()
    summary = results.get("_summary", {})

    passed = summary.get("passed", 0)
    total = summary.get("total", 0)

    if passed == total:
        return f"System diagnostic complete. All {total} systems operational. Everything is running normally, sir."
    else:
        failed = []
        for name, info in results.items():
            if name.startswith("_"):
                continue
            if info.get("status") != "PASS":
                failed.append(name.replace("_", " "))
        fail_list = ", ".join(failed)
        return f"System diagnostic complete. {passed} of {total} systems operational. Issues detected in: {fail_list}."


def register_diagnostic_tool():
    """Register the diagnostic command as a tool in the tool registry."""
    try:
        from core.tool_registry import get_tool_registry, ToolType, ToolParameter

        registry = get_tool_registry()

        async def _diagnostic_tool() -> str:
            return diagnostic_spoken_summary()

        registry.register_tool(
            "system_diagnostic",
            "System Diagnostic",
            "Run a comprehensive system diagnostic to check all GENESIS subsystems",
            ToolType.SYSTEM_COMMAND,
            _diagnostic_tool,
            return_type=str,
        )
        logger.info("[DIAGNOSTIC] Tool registered: system_diagnostic")
    except Exception as e:
        logger.warning(f"[DIAGNOSTIC] Tool registration failed: {e}")
