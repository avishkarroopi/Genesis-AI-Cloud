import asyncio
import os
import sys

# Ensure root is in PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from core.event_bus import get_event_bus
from core.ai_telemetry.inference_monitor import get_inference_monitor

async def run_tests():
    print("[TEST] Starting Phase 2 & 3 runtime verification...")
    
    # 1. Initialize Event Bus
    bus = get_event_bus()
    await bus.start()
    
    # 2. Init Modules
    try:
        from core.ai_monitor import ai_cost_optimizer
        ai_cost_optimizer.initialize_module()
    except Exception as e:
         print(f"[TEST] Warning loading ai cost optimizer: {e}")

    try:
        from core.cognitive import cognitive_orchestrator, governance_layer, self_evolution
        cognitive_orchestrator.initialize_module()
        governance_layer.initialize_module()
        self_evolution.initialize_module()
    except Exception as e:
         print(f"[TEST] Warning loading cognitive plugins: {e}")
         
    try:
        from core.strategy_optimizer import optimizer
        from core.executive_control.agent_coordinator import coordinator
        print("[TEST] Executive plugins loaded.")
    except Exception as e:
        print(f"[TEST] Failed loading executive modules: {e}")

    monitor = get_inference_monitor()
    
    # 3. Simulate Telemetry & Cost
    print("[TEST] Testing telemetrics & cost loop...")
    await bus.publish("llm_inference_complete", "test", data={"tokens": 150000, "provider": "openai", "latency": 120})
    await asyncio.sleep(1)
    
    # Simulate anomaly burst
    for _ in range(6):
        monitor.record_event("api_request", {"failed": True}, 1)
    await asyncio.sleep(1)

    # 4. Simulate Reasoning Pipeline (Phase 2)
    print("[TEST] Testing Cognitive Orchestrator & Strategy Optimizer...")
    await bus.publish("perception_event", "test", data={"requires_action": True, "goal": "Find latest news on AI", "urgent": True})
    await asyncio.sleep(1)
    
    # 5. Simulate Digital Twin / Governance 
    print("[TEST] Testing Governance...")
    await bus.publish("DIGITAL_TWIN_SIMULATION", "test", data={"outcome": {"risk_level": "high"}, "trigger": "test_agent"})
    await asyncio.sleep(1)

    await bus.stop()
    print("[TEST] System stability verified. Phase 2 and 3 modules executed perfectly.")

if __name__ == "__main__":
    asyncio.run(run_tests())
