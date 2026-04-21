"""
Awareness Engine (Layer 2 - Intelligence) — Phase-4 Upgrade
Monitors WorldModel + GoalQueue and emits proactive GOAL_TRIGGERED events
on the EventBus, closing the cognition feedback loop.
"""

import threading
import time

try:
    from core.world_model import get_world_model
except ImportError:
    def get_world_model(): return None

try:
    from core.agents.goal_queue import get_goal_queue
except ImportError:
    def get_goal_queue(): return None


class AwarenessEngine:
    def __init__(self):
        self.running = False
        self.thread = None
        self.system_idle = True
        self._last_world_hash = None
        self._scan_count = 0

    def check_world_model(self):
        """Check world model for changes and emit GOAL_TRIGGERED if needed."""
        wm = get_world_model()
        if not wm:
            return

        try:
            current_hash = hash(frozenset(wm.world_state.items())) if hasattr(wm, 'world_state') else None
            if current_hash and current_hash != self._last_world_hash:
                self._last_world_hash = current_hash
                # World state changed — emit goal trigger
                try:
                    from core.event_bus import get_event_bus
                    bus = get_event_bus()
                    bus.publish_sync("GOAL_TRIGGERED", "awareness_engine", {
                        "goal": {
                            "type": "world_state_change",
                            "description": "World state changed — evaluate environment",
                        },
                        "scan_count": self._scan_count,
                    })
                except Exception:
                    pass
        except Exception:
            pass

    def process_agent_queue(self):
        queue = get_goal_queue()
        if queue:
            self.system_idle = not queue.has_goals()

    def monitor_scene_changes(self):
        """Monitor for scene changes that might trigger autonomous actions."""
        try:
            from core.event_bus import get_event_bus
            bus = get_event_bus()
            # Check recent events for actionable items
            recent = bus.get_event_history(event_type="VISION_DETECTED", limit=5)
            if recent:
                for event in recent:
                    objects = event.data.get("objects", []) if hasattr(event, 'data') else []
                    if len(objects) > 3:  # Significant scene change
                        bus.publish_sync("GOAL_TRIGGERED", "awareness_engine", {
                            "goal": {
                                "type": "scene_analysis",
                                "description": f"Analyze scene with {len(objects)} detected objects",
                            }
                        })
                        break
        except Exception:
            pass

    def _loop(self):
        while self.running:
            self._scan_count += 1
            self.check_world_model()
            self.process_agent_queue()
            self.monitor_scene_changes()

            if self.system_idle:
                time.sleep(4)
            else:
                time.sleep(1.5)

    def start(self):
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._loop, daemon=True)
            self.thread.start()
            print("[AWARENESS] Engine started (Phase-4)", flush=True)

    def stop(self):
        self.running = False

    def get_status(self):
        return {
            "running": self.running,
            "idle": self.system_idle,
            "scans": self._scan_count,
        }


awareness_engine = AwarenessEngine()

def start_awareness_loop():
    awareness_engine.start()

def get_awareness_engine():
    return awareness_engine
