"""
Relationship Memory (Phase-2 User Intelligence)
Stores and retrieves relationships and interactions via unified memory.
Constraint 4: Uses memory_manager.py.
"""

from core.memory.memory_manager import store_user_memory, search_memory

def record_relationship(person_name: str, connection: str, interaction_notes: str):
    """Record a relationship event or profile update."""
    text_entry = f"[Relationship] {person_name} ({connection}). Note: {interaction_notes}"
    return store_user_memory(text_entry)

def recall_relationships(query: str):
    return search_memory(f"[Relationship] {query}")
