"""
Goal Queue Manager (Layer 2 - Intelligence)
Manages the lifecycle of system goals before they become executable tasks.
"""

from collections import deque

class GoalQueue:
    def __init__(self):
        self.goals = deque()
    
    def add_goal(self, goal: dict):
        """
        Adds a new goal.
        goal dictates the high level objective, e.g., {'target': 'find_info', 'query': 'robotics'}
        """
        self.goals.append(goal)
    
    def pop_next(self) -> dict:
        if self.goals:
            return self.goals.popleft()
        return None
    
    def has_goals(self) -> bool:
        return len(self.goals) > 0

goal_queue = GoalQueue()

def get_goal_queue() -> GoalQueue:
    return goal_queue
