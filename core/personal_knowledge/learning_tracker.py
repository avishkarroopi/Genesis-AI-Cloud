"""
Learning Tracker (Phase-2 User Intelligence)
Tracks progress of study or skill acquisition in personal memory backend.
"""

from core.memory.memory_manager import store_user_memory, search_memory

def log_learning_progress(subject: str, hours_spent: float, milestones_hit: list):
    """Log progress towards mastering a specific subject."""
    milestones_str = ", ".join(milestones_hit)
    text_entry = f"[LearningProgress] Subject: {subject}. Hours logged: {hours_spent}. Milestones: {milestones_str}"
    return store_user_memory(text_entry)

def get_learning_history(subject: str):
    return search_memory(f"[LearningProgress] {subject}")
