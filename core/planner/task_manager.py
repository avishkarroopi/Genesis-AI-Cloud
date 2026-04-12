from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class TaskStep:
    id: int
    description: str
    action: str  # e.g., 'tools' or 'reasoning'
    parameters: dict = field(default_factory=dict)
    status: str = "pending" # pending, running, done, failed
    result: Optional[str] = None

@dataclass
class Task:
    goal: str
    steps: List[TaskStep] = field(default_factory=list)
    current_step: int = 0
    status: str = "pending" # pending, running, done, failed
    final_result: Optional[str] = None

class TaskManager:
    def __init__(self):
        self._active_task: Optional[Task] = None
        
    def create_task(self, goal: str, steps: List[TaskStep]) -> Task:
        """Start tracking a new plan."""
        self._active_task = Task(goal=goal, steps=steps, status="running")
        return self._active_task
        
    def get_task_status(self):
        """Returns the current active multi-step task, if any."""
        return self._active_task
        
    def complete_task(self, result: str):
        """Mark task as completely done."""
        if self._active_task is not None:
            self._active_task.status = "done"
            self._active_task.final_result = result
            
    def cancel_task(self, reason: str):
        """Cancel task immediately, perhaps due to failure."""
        if self._active_task is not None:
            self._active_task.status = "failed"
            self._active_task.final_result = f"Task Cancelled: {reason}"
            
    def get_next_step(self):
        """Return the next pending step, or None if all are done."""
        if self._active_task is None or self._active_task.status != "running":
            return None
            
        for step in self._active_task.steps:
            if step.status == "pending":
                return step
                
        # If we reach here, all steps finished successfully.
        self.complete_task("All steps successfully executed.")
        return None

# Singleton to hold active plan state
manager = TaskManager()
