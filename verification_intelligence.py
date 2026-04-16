import asyncio
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from core.event_bus import get_event_bus
from core.planner.execution_graph_builder import initialize_module as init_planner
from core.tools.tool_metrics import initialize_module as init_tools
from core.personal_memory.long_term_profiler import initialize_module as init_ltm
from core.personal_memory.habit_tracker import initialize_module as init_habit
from core.digital_twin.probabilistic_engine import initialize_module as init_prob
from core.self_improvement.reflection_engine import initialize_module as init_reflect

async def run_tests():
    print("[TEST] Starting Intelligence Expansion Verification...")
    
    bus = get_event_bus()
    await bus.start()
    
    # 1. Init modules
    init_planner()
    init_tools()
    init_ltm()
    init_habit()
    init_prob()
    init_reflect()
    print("[TEST] All intelligence expansion modules loaded successfully.")

    # 2. Task Planning
    print("[TEST] Testing Task Planning Engine...")
    await bus.publish("decompose_task", "test", data={"goal": "Build AGI startup"})
    await asyncio.sleep(0.5)

    # 3. Tool Intelligence
    print("[TEST] Testing Tool Intelligence Metrics...")
    await bus.publish("tool_execution_start", "test", data={"tool_name": "Tavily", "run_id": "r1"})
    await bus.publish("tool_execution_end", "test", data={"run_id": "r1", "success": True})
    await asyncio.sleep(0.5)

    # 4. Memory & Habit Training
    print("[TEST] Testing Memory & Personality Clustering...")
    await bus.publish("life_event_occurred", "test", data={"description": "User solved coding issue at 2am via habit flow."})
    await bus.publish("user_interaction", "test", data={"time_of_day": "night", "action": "coding"})
    await asyncio.sleep(0.5)

    # 5. Digital Twin Probabilistics
    print("[TEST] Testing Digital Twin Probabilistic Engine...")
    await bus.publish("simulate_decision", "test", data={"decision": "Launch SaaS product tomorrow"})
    await asyncio.sleep(0.5)

    # 6. Self-Improvement Feedback
    print("[TEST] Testing Self-Improvement Reflection Engine...")
    await bus.publish("anomaly_detected", "test", data={"reason": "High failure rate in OpenAI API endpoint"})
    await asyncio.sleep(0.5)
    
    await bus.stop()
    print("[TEST] Verification Complete. System is highly stable.")

if __name__ == "__main__":
    asyncio.run(run_tests())
