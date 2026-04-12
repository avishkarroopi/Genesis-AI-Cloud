"""
Life Event Store (Phase-2 User Intelligence)
Stores and retrieves life timeline events via the unified memory backend.
Constraint 4: Uses memory_manager.py for all databases.
"""

import json
from datetime import datetime
from core.memory.memory_manager import store_user_memory, search_memory

def record_life_event(event_title: str, importance: str, details: dict):
    """Record a life event in the unified memory store."""
    record = {
        "memory_type": "life_event",
        "title": event_title,
        "importance": importance,
        "details": details,
        "recorded_at": datetime.now().isoformat()
    }
    # Format the store string to allow specific searches
    text_entry = f"[LifeEvent] {event_title} - Importance: {importance}. Details: {json.dumps(details)}"
    return store_user_memory(text_entry)

def recall_life_events(query: str):
    """Recall life events containing the query."""
    results = search_memory(f"[LifeEvent] {query}")
    return results
