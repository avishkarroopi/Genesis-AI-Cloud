"""
Personal Knowledge Engine (Phase-2 User Intelligence)
Stores and retrieves personal knowledge via unified memory backend.
Constraint 4: Uses memory_manager.py.
"""

from core.memory.memory_manager import store_knowledge, search_memory

def record_knowledge(topic: str, fact: str):
    """Store knowledge factoid."""
    text_entry = f"[Knowledge] Topic: {topic}. Fact: {fact}."
    return store_knowledge(text_entry)

def search_personal_knowledge(query: str):
    """Retrieve knowledge on query."""
    return search_memory(f"[Knowledge] {query}")
