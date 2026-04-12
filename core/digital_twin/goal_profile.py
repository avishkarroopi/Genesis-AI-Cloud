"""
Goal Profile (Phase-2 User Intelligence)
Maintains the user's ultimate life goals in the digital twin.
"""

from core.memory.memory_manager import search_memory

def get_current_life_goals():
    """Load core priorities to contextualize agent planning."""
    return search_memory("[Goal]")
