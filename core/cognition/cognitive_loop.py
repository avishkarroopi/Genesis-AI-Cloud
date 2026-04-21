"""
Phase-4 — Cognitive Loop Engine (Upgraded)
Full reasoning cycle: awareness → event_bus → cognitive_loop → planner →
execution_graph → agents → tools → results → reflection → memory update →
system_state update → back to awareness.

Allows GENESIS to initiate autonomous tasks without voice commands.
"""

import threading
import time
import traceback
from concurrent.futures import ThreadPoolExecutor

_cognitive_pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix="CognitiveLoop")

# Cycle interval in seconds
_CYCLE_INTERVAL = 20.0
_MAX_GOALS_PER_CYCLE = 2


class CognitiveLoop:
    """Autonomous reasoning loop connecting event_bus, world_model, planner,
    agents, learning_engine, and reflection into a continuous intelligence cycle."""

    def __init__(self):
        self._running = False
        self._thread = None
        self._cycle_count = 0
        self._last_observation = {}
        self._current_goal = None
        self._pending_goals = []
        self._reflection_log = []
        print("[COGNITIVE] Loop engine initialized (Phase-4 upgrade)", flush=True)

    def start(self):
        """Start the cognitive loop in a daemon thread."""
        if self._running:
            return
        self._running = True
        self._subscribe_to_events()
        self._thread = threading.Thread(target=self._run_loop, daemon=True, name="CognitiveLoop")
        self._thread.start()
        print("[COGNITIVE] Loop started (autonomous mode)", flush=True)

    def stop(self):
        """Stop the cognitive loop."""
        self._running = False
        print("[COGNITIVE] Loop stopped", flush=True)

    def is_running(self):
        return self._running

    def _subscribe_to_events(self):
        """Subscribe to event bus for real-time event consumption."""
        try:
            from core.event_bus import get_event_bus
            bus = get_event_bus()
            bus.subscribe("GOAL_TRIGGERED", self._on_goal_triggered)
            bus.subscribe("MEMORY_UPDATED", self._on_memory_updated)
            bus.subscribe("perception_event", self._on_perception)
            print("[COGNITIVE] Subscribed to event bus channels", flush=True)
        except Exception as e:
            print(f"[COGNITIVE] Event bus subscription failed: {e}", flush=True)

    def _on_goal_triggered(self, event):
        """Handle GOAL_TRIGGERED events from awareness loop."""
        try:
            data = event.data if hasattr(event, 'data') else event
            goal = data.get("goal", {}) if isinstance(data, dict) else {}
            if goal:
                self._pending_goals.append(goal)
                print(f"[COGNITIVE] Queued goal from awareness: {str(goal)[:60]}", flush=True)
        except Exception:
            pass

    def _on_memory_updated(self, event):
        """Handle MEMORY_UPDATED events for reflection."""
        pass  # Memory updates are consumed during reflection phase

    def _on_perception(self, event):
        """Handle perception events for world state awareness."""
        try:
            data = event.data if hasattr(event, 'data') else event
            if isinstance(data, dict) and data.get("requires_action"):
                self._pending_goals.append({
                    "type": "perception_response",
                    "description": data.get("goal", "respond to perception"),
                    "data": data
                })
        except Exception:
            pass

    def _run_loop(self):
        """Main loop — never crashes, always recovers."""
        while self._running:
            try:
                self._cycle()
                self._cycle_count += 1
            except Exception as e:
                print(f"[COGNITIVE] Cycle error (non-fatal): {e}", flush=True)
            time.sleep(_CYCLE_INTERVAL)

    def _cycle(self):
        """Single cognitive cycle: observe → update → goal → plan → execute → reflect → record."""
        # 1. Observe environment
        observation = self._observe_environment()

        # 2. Update world state
        self._update_world_state(observation)

        # 3. Select goals (from pending queue or proactive generation)
        goals = self._select_goals(observation)
        if not goals:
            return  # Nothing to act on this cycle

        for goal in goals[:_MAX_GOALS_PER_CYCLE]:
            # 4. Plan actions
            plan = self._plan_actions(goal)
            if not plan:
                continue

            # 5. Execute actions
            result = self._execute_actions(plan)

            # 6. Reflect on result
            reflection = self._reflect(goal, result)

            # 7. Update memory
            self._update_memory(goal, result, reflection)

            # 8. Update system state
            self._update_system_state(goal, result)

            # 9. Record experience
            self._record_experience(goal, result, reflection)

    def _observe_environment(self):
        """Pull latest state from event_bus and world_model."""
        try:
            from core.world_model import get_world_model
            wm = get_world_model()
            state = {
                "objects": len(wm.objects),
                "events": len(wm.event_history),
                "world_state": dict(wm.world_state),
            }
            self._last_observation = state
            return state
        except Exception:
            return {}

    def _update_world_state(self, observation):
        """Push observations into world model."""
        pass  # World model auto-updates via event_bus subscriptions

    def _select_goals(self, observation):
        """Select next goals from pending queue or generate proactively."""
        goals = []

        # Drain pending goals from event bus
        while self._pending_goals and len(goals) < _MAX_GOALS_PER_CYCLE:
            goals.append(self._pending_goals.pop(0))

        # Proactive goal generation based on world state changes
        if not goals and observation.get("events", 0) > 0:
            goals.append({"type": "monitor", "description": "proactive environment monitoring"})

        return goals

    def _plan_actions(self, goal):
        """Generate a plan for the selected goal."""
        try:
            goal_type = goal.get("type", "unknown")

            if goal_type == "monitor":
                return {"action": "log_state", "goal": goal}

            if goal_type == "perception_response":
                return {"action": "process_perception", "goal": goal}

            # Try planner agent for complex goals
            try:
                from core.agents.task_planner import create_plan
                plan = create_plan(goal.get("description", ""))
                if plan:
                    return {"action": "execute_plan", "goal": goal, "plan": plan}
            except Exception:
                pass

            return {"action": "log_state", "goal": goal}
        except Exception:
            return None

    def _execute_actions(self, plan):
        """Execute the planned actions."""
        try:
            action = plan.get("action", "")

            if action == "log_state":
                obs = self._last_observation
                if obs.get("objects", 0) > 0:
                    print(f"[COGNITIVE] Monitoring: {obs.get('objects', 0)} objects tracked", flush=True)
                return {"status": "ok", "observation": obs}

            if action == "process_perception":
                # Delegate to agent system for perception-triggered tasks
                try:
                    from core.agent_registry import delegate_agent_task
                    goal_desc = plan.get("goal", {}).get("description", "")
                    result = delegate_agent_task("research", goal_desc)
                    return {"status": "ok", "result": result}
                except Exception as e:
                    return {"status": "error", "error": str(e)}

            if action == "execute_plan":
                # Execute through agent scheduler
                try:
                    from core.agents.agent_scheduler import get_scheduler
                    scheduler = get_scheduler()
                    result = scheduler.execute_plan(plan.get("plan", {}))
                    return {"status": "ok", "result": result}
                except Exception as e:
                    return {"status": "partial", "error": str(e)}

            return {"status": "skip"}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def _reflect(self, goal, result):
        """Reflection engine: evaluate action outcome and generate insights."""
        status = result.get("status", "unknown") if result else "unknown"
        success = status == "ok"

        reflection = {
            "goal": goal.get("description", "unknown"),
            "success": success,
            "status": status,
            "insight": "",
            "timestamp": time.time()
        }

        if success:
            reflection["insight"] = f"Goal '{goal.get('description', '')}' achieved successfully."
        else:
            reflection["insight"] = f"Goal '{goal.get('description', '')}' failed: {result.get('error', 'unknown reason')}."

        self._reflection_log.append(reflection)
        if len(self._reflection_log) > 100:
            self._reflection_log = self._reflection_log[-100:]

        return reflection

    def _update_memory(self, goal, result, reflection):
        """Update memory with cycle outcome."""
        try:
            from core.memory.memory_manager import save_memory
            summary = f"Cognitive cycle: {goal.get('description', 'unknown')}. Result: {result.get('status', 'unknown')}"
            save_memory(summary)
        except Exception:
            pass

    def _update_system_state(self, goal, result):
        """Publish system state update to event bus."""
        try:
            from core.event_bus import get_event_bus
            bus = get_event_bus()
            bus.publish_sync("COGNITIVE_CYCLE_COMPLETE", "cognitive_loop", {
                "cycle": self._cycle_count,
                "goal": goal.get("description", ""),
                "status": result.get("status", "unknown"),
            })
        except Exception:
            pass

    def _record_experience(self, goal, result, reflection):
        """Record the cycle outcome via learning_engine."""
        try:
            from core.learning_engine import record_experience
            summary = f"Cognitive cycle: {goal.get('description', 'unknown')}. Result: {result.get('status', 'unknown')}"
            record_experience(summary, "success" if reflection.get("success") else "failed")
        except Exception:
            pass  # Non-fatal

    def get_status(self):
        """Return loop status for diagnostics."""
        return {
            "running": self._running,
            "cycles": self._cycle_count,
            "pending_goals": len(self._pending_goals),
            "reflections": len(self._reflection_log),
            "last_observation": self._last_observation,
        }


# Global singleton
_cognitive_loop = None
_cl_lock = threading.Lock()


def get_cognitive_loop():
    """Get or create the global CognitiveLoop."""
    global _cognitive_loop
    if _cognitive_loop is None:
        with _cl_lock:
            if _cognitive_loop is None:
                _cognitive_loop = CognitiveLoop()
    return _cognitive_loop


def start_cognitive_loop():
    """Convenience: get and start the loop."""
    loop = get_cognitive_loop()
    loop.start()
    return loop
