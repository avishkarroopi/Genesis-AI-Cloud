"""
Agent Worker (Layer 2 -> Layer 3 Interface)
Dedicated background worker thread that monitors the goal queue,
generates tasks with the Task Planner, and invokes the Skill Executor.
Must NOT interact directly with hardware or action modules!
"""

import threading
import time
from core.agents.goal_queue import get_goal_queue
from core.agents.task_planner import TaskPlanner
from core.skills.skill_executor import SkillExecutor

class AgentWorker:
    def __init__(self):
        self.running = False
        self.thread = None
        self.planner = TaskPlanner()
        self.queue = get_goal_queue()
        
    def start(self):
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._worker_loop, daemon=True)
            self.thread.start()
            
    def stop(self):
        self.running = False
    
    def _worker_loop(self):
        while self.running:
            if self.queue.has_goals():
                goal = self.queue.pop_next()
                if goal:
                    # 1. Plan tasks (Goal -> Tasks)
                    tasks = self.planner.plan_tasks(goal)
                    
                    # 2. Execute Tasks (Tasks -> Skills -> Action Layer)
                    for task in tasks:
                        skill_name = task.get("skill")
                        args = task.get("args", {})
                        
                        # CONSTRAINT 1: strictly uses SkillExecutor
                        result = SkillExecutor.execute(skill_name, **args)
                        # Optionally log/save the result back to agent_memory
                        
            time.sleep(1)  # Throttling the tight loop

worker = AgentWorker()

def get_agent_worker() -> AgentWorker:
    return worker
