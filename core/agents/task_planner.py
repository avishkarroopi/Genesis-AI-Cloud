"""
Task Planner (Layer 2 - Intelligence)
Reasons about high-level goals and schedules specific executable tasks.
Phase-2: Integrates Prediction Engine & Digital Twin workflows.
"""

from core.context_engine.context_router import get_context_router
from core.event_bus import get_event_bus
import asyncio
import uuid

class TaskPlanner:
    def _run_async(self, coro):
        try:
            loop = asyncio.get_running_loop()
            return loop.create_task(coro)
        except RuntimeError:
            return asyncio.run(coro)

    def plan_tasks(self, goal: dict) -> list:
        """
        Takes a goal dictionary and returns a list of task dictionaries.
        Each task corresponds to a skill to be executed.
        e.g., [{'skill': 'youtube_search', 'args': {'query': '...'}, 'dependencies': []}]
        """
        bus = get_event_bus()
        
        cycle_id = str(uuid.uuid4())
        
        # Constraint 5: Prediction Engine Isolation
        # Publish event so prediction engines can analyze without mutating state directly.
        # Constraint 7: Passes cycle_id to allow throttling.
        bus.publish_sync("AGENT_PLANNING_STARTED", "agents.task_planner", {"goal": goal, "cycle_id": cycle_id})
        
        # Constraint 6: Digital Twin Execution Guard
        # Only run simulation explicitly through approved triggers (e.g., agent_planning)
        try:
            from core.digital_twin.behavior_simulator import run_simulation
            self._run_async(run_simulation("agent_planning", {"proposed_action": goal}))
        except Exception as e:
            pass

        context = get_context_router().route_request("agent", task="planning", goal=str(goal))
        
        # Simplified planning for Phase 1. Real implementation relies on an LLM to generate these tasks
        # in the context of the Goal-Task-Skill pipeline.
        target = goal.get("target")
        tasks = []
        
        if target == "find_info":
            tasks.append({
                "skill": "browser_open",
                "args": {"url": f"https://duckduckgo.com/?q={goal.get('query', '')}"}
            })
        elif target == "vision_scan":
            tasks.append({
                "skill": "vision_scan",
                "args": {"parameters": {"depth": "full"}}
            })
        else:
            # Fallback
            tasks.append({
                "skill": "automation_webhook",
                "args": {"event_name": "generic_goal", "payload": goal}
            })
            
        return tasks
