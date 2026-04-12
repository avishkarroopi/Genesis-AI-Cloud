"""
Awareness Engine (Layer 2 - Intelligence)
Constraint 2: The awareness loop must be adaptive and non-blocking.
Runs in a separate background thread with dynamic sleep throttling.
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
        
    def check_world_model(self):
        wm = get_world_model()
        if wm:
            # e.g., Evaluate state to see if proactive actions are needed
            pass
            
    def process_agent_queue(self):
        queue = get_goal_queue()
        if queue:
            # If there's high capacity items, we're not idle
            self.system_idle = not queue.has_goals()
            
    def monitor_scene_changes(self):
        # Look at vision SceneMemory for changes that might invoke goals
        # e.g. someone entered the room
        pass

    def _loop(self):
        while self.running:
            self.check_world_model()
            self.process_agent_queue()
            self.monitor_scene_changes()

            if self.system_idle:
                time.sleep(4)  # Adaptive throttling: 3-5
            else:
                time.sleep(1.5)  # Adaptive throttling: 1-2

    def start(self):
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._loop, daemon=True)
            self.thread.start()

    def stop(self):
        self.running = False

awareness_engine = AwarenessEngine()

def start_awareness_loop():
    awareness_engine.start()
