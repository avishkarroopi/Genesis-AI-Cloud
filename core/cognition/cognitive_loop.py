"""
Phase-2 — Cognitive Loop Engine
Continuous reasoning cycle: observe → update → goal → plan → execute → evaluate → record.
Runs asynchronously in a daemon thread. Never blocks the main brain pipeline.
"""

import threading
import time
import traceback
from concurrent.futures import ThreadPoolExecutor

_cognitive_pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix="CognitiveLoop")

# Cycle interval in seconds — how often the loop ticks
_CYCLE_INTERVAL = 30.0
_MAX_GOALS_PER_CYCLE = 1


class CognitiveLoop:
    """Autonomous reasoning loop that connects event_bus, world_model, planner,
    agents, and learning_engine into a continuous intelligence cycle."""

    def __init__(self):
        self._running = False
        self._thread = None
        self._cycle_count = 0
        self._last_observation = {}
        self._current_goal = None
        print("[COGNITIVE] Loop engine initialized", flush=True)

    def start(self):
        """Start the cognitive loop in a daemon thread."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True, name="CognitiveLoop")
        self._thread.start()
        print("[COGNITIVE] Loop started", flush=True)

    def stop(self):
        """Stop the cognitive loop."""
        self._running = False
        print("[COGNITIVE] Loop stopped", flush=True)

    def is_running(self):
        return self._running

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
        """Single cognitive cycle: observe → update → goal → plan → execute → evaluate → record."""
        # 1. Observe environment via event_bus
        observation = self._observe_environment()

        # 2. Update world state
        self._update_world_state(observation)

        # 3. Select a goal (currently passive — logs state)
        goal = self._select_goal(observation)
        if not goal:
            return  # Nothing to act on this cycle

        # 4. Plan actions
        plan = self._plan_actions(goal)
        if not plan:
            return

        # 5. Execute actions
        result = self._execute_actions(plan)

        # 6. Evaluate result
        success = self._evaluate_result(result)

        # 7. Record experience
        self._record_experience(goal, result, success)

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
        """Push observations into world model (already handled via event subscriptions)."""
        pass  # World model auto-updates via event_bus subscriptions

    def _select_goal(self, observation):
        """Select next goal based on observations. Currently passive monitoring."""
        # Future: proactive goal selection based on environment changes
        if observation.get("events", 0) > 0:
            return {"type": "monitor", "description": "passive environment monitoring"}
        return None

    def _plan_actions(self, goal):
        """Generate a plan for the selected goal."""
        try:
            if goal.get("type") == "monitor":
                return {"action": "log_state", "goal": goal}
            return None
        except Exception:
            return None

    def _execute_actions(self, plan):
        """Execute the planned actions."""
        try:
            if plan.get("action") == "log_state":
                obs = self._last_observation
                if obs.get("objects", 0) > 0:
                    print(f"[COGNITIVE] Monitoring: {obs.get('objects', 0)} objects tracked", flush=True)
                return {"status": "ok", "observation": obs}
        except Exception as e:
            return {"status": "error", "error": str(e)}
        return {"status": "skip"}

    def _evaluate_result(self, result):
        """Evaluate whether the action succeeded."""
        return result.get("status") == "ok" if result else False

    def _record_experience(self, goal, result, success):
        """Record the cycle outcome via learning_engine."""
        try:
            from core.learning_engine import record_experience
            summary = f"Cognitive cycle: {goal.get('description', 'unknown')}. Result: {result.get('status', 'unknown')}"
            record_experience(summary, "success" if success else "failed")
        except Exception:
            pass  # Non-fatal

    def get_status(self):
        """Return loop status for diagnostics."""
        return {
            "running": self._running,
            "cycles": self._cycle_count,
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
