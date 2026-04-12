"""
Decision Pattern Model (Phase-2 User Intelligence)
Digital twin component to model user historical decision patterns.
"""

from core.memory.memory_manager import search_memory

def get_decision_patterns():
    """Fetch user decision making traits for simulation."""
    return {"risk_tolerance": "moderate", "bias": "action_oriented"}
