"""
Project Memory (Phase-2 User Intelligence)
Records long-term project definitions and updates via the unified memory.
Constraint 4: Uses memory_manager.py.
"""

from core.memory.memory_manager import store_user_memory, search_memory

def record_project_update(project_name: str, status: str, milestone: str):
    text_entry = f"[Project] {project_name}. Status: {status}. Milestone: {milestone}."
    return store_user_memory(text_entry)

def recall_projects(query: str):
    return search_memory(f"[Project] {query}")
