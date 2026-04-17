import sys
import os
import json
import asyncio
from datetime import datetime

sys.path.append(os.path.dirname(__file__))

report = {}

async def run_tests():
    # Step 5: Event Bus
    try:
        from core.event_bus import get_event_bus
        bus = get_event_bus()
        await bus.start()
        
        received = []
        async def handler(event):
            received.append(event)
            
        bus.subscribe("test_event", handler)
        await bus.publish("test_event", "test_source", {"foo": "bar"})
        
        # Give it a moment to process the queue
        await asyncio.sleep(0.5)
        
        report["event_bus"] = {
            "success": len(received) > 0 and received[0].data.get("foo") == "bar"
        }
        await bus.stop()
    except Exception as e:
        report["event_bus"] = {"error": str(e)}

    # Step 6: Tool registry
    try:
        from core.tool_registry import get_tool_registry, ToolType, ToolParameter
        registry = get_tool_registry()
        
        # register dummy tool
        async def dummy_tool(arg1: str):
            return f"Processed {arg1}"
            
        registry.register_tool(
            tool_id="dummy_tool",
            name="Dummy Tool",
            description="Testing registry",
            tool_type=ToolType.COMPUTATION,
            callable_func=dummy_tool,
            parameters=[ToolParameter(name="arg1", param_type=str)]
        )
        
        result = await registry.execute_tool("dummy_tool", arg1="hello")
        
        report["tool_registry"] = {
            "success": result == "Processed hello",
            "tools_count": len(registry.tools)
        }
    except Exception as e:
        report["tool_registry"] = {"error": str(e)}

if __name__ == "__main__":
    asyncio.run(run_tests())
    print(json.dumps(report, indent=2))
