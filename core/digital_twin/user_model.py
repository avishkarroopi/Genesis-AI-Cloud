"""
User Model (Phase-2 User Intelligence)
Maintains the internal digital twin representation of the user.
"""

from core.memory.memory_manager import search_memory

def get_virtual_user_state():
    """Retrieve user state variables to seed a simulation."""
    # Stub that reads user memories to shape simulation
    history = search_memory("User Profile")
    return {"state": "active", "recent_profile_data": history}
