"""
Agent Manager (Layer 2 - Intelligence)
Central coordinate for the agent framework. Handles initialization
and exposes the primary interfaces.
"""

from core.agents.agent_worker import get_agent_worker
from core.agents.goal_queue import get_goal_queue

def init_agents():
    """Starts the background agent workers."""
    worker = get_agent_worker()
    worker.start()

def dispatch_goal(target: str, **kwargs):
    """Adds a new high-level goal to the queue."""
    goal = {"target": target, **kwargs}
    queue = get_goal_queue()
    queue.add_goal(goal)
