import time
from typing import Optional, List, Dict
from core.planner.task_manager import TaskStep

class AgentController:
    """Manages the lifecycle and bounds of the active agent."""
    def __init__(self, max_steps: int = 10, max_time_sec: int = 120):
        self.max_steps = max_steps
        self.max_time_sec = max_time_sec
        self.start_time: float = 0
        self.step_count: int = 0
        self.is_running: bool = False
        self.history: List[Dict[str, str]] = []

    def start(self):
        self.is_running = True
        self.start_time = time.time()
        self.step_count = 0
        self.history.clear()

    def stop(self):
        self.is_running = False

    def can_continue(self) -> bool:
        """Check if bounds are respected before proceeding."""
        if not self.is_running:
            return False
            
        if self.step_count >= self.max_steps:
            print("[AGENT] Halting: Max steps reached.", flush=True)
            return False
            
        if (time.time() - self.start_time) > self.max_time_sec:
            print("[AGENT] Halting: Max time limit reached.", flush=True)
            return False
            
        return True

    def log_step(self, step_obj: TaskStep, observation: str):
        self.step_count += 1
        self.history.append({
            "step": step_obj.description,
            "observation": observation
        })

agent_controller = AgentController()
