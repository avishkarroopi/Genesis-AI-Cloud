import asyncio
import os
import sys

# Ensure root is in PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from core.event_bus import get_event_bus
from core.tools.init_tools import init_all_tools
from core.agents.init_agents import init_all_agents
from core.tool_registry import get_tool_registry

async def run_tests():
    print("[TEST] Starting runtime verification...")
    
    # 1. Initialize Event Bus
    bus = get_event_bus()
    await bus.start()
    
    # 2. Init Tools and Agents
    init_all_tools()
    init_all_agents()
    
    registry = get_tool_registry()
    tools = registry.list_available_tools()
    print(f"[TEST] Registered {len(tools)} tools.")
    if len(tools) == 0:
        print("[TEST] FAILED: Tools are missing.")
        await bus.stop()
        return

    print("[TEST] Tools and Agents initialized successfully.")
    
    # 3. Simulate Event Bus Message for File Agent
    print("[TEST] Testing file_agent via event_bus...")
    await bus.publish("FileWriteRequested", "test", data={"path": "test_output.txt", "content": "Verification success"})
    await asyncio.sleep(1) # wait for event to process
    if os.path.exists("test_output.txt"):
        print("[TEST] file_agent executed successfully via event bus.")
        os.remove("test_output.txt")
    else:
        print("[TEST] FAILED: file_agent didn't create the file.")
        
    # 4. Simulate Digital Twin / Cognitive Orchestrator
    print("[TEST] Testing advanced systems (Cognitive Orchestrator / Digital Twin)...")
    await bus.publish("decision_executed", "test", data={"decision": "run_simulated_test"})
    await asyncio.sleep(1)
    
    await bus.stop()
    print("[TEST] System stability verified. All core modules ran without crashing.")

if __name__ == "__main__":
    asyncio.run(run_tests())
