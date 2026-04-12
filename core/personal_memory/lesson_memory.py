"""
Lesson Memory (Phase-2 User Intelligence)
Records learned lessons and insights via the unified memory.
Constraint 4: Uses memory_manager.py.
"""

from core.memory.memory_manager import store_user_memory, search_memory

def record_lesson(topic: str, lesson_insight: str):
    text_entry = f"[Lesson] On '{topic}': {lesson_insight}"
    return store_user_memory(text_entry)

def recall_lessons(query: str):
    return search_memory(f"[Lesson] {query}")
