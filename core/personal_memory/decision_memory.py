"""
Decision Memory (Phase-2 User Intelligence)
Stores and retrieves user decisions via the unified memory backend.
Constraint 4: Uses memory_manager.py for all database needs.
"""

import json
from datetime import datetime
from core.memory.memory_manager import store_user_memory, search_memory

def record_decision(decision: str, reason: str, alternatives: list):
    """Record a decision in the unified memory store."""
    text_entry = f"[Decision] {decision}. Reason: {reason}. Alternatives considered: {', '.join(alternatives)}."
    return store_user_memory(text_entry)

def recall_decisions(query: str):
    """Recall decisions matching query."""
    return search_memory(f"[Decision] {query}")
