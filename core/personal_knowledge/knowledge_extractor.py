"""
Knowledge Extractor Tracker (Phase-2 User Intelligence)
Extracts structural knowledge from documents or notes to feed into the store.
"""

from .knowledge_store import record_knowledge

def extract_and_store_from_text(source: str, content: str):
    """
    Simulated extraction of knowledge.
    In future, this routes through LLM chunking.
    """
    # Stub: blindly saves content
    record_knowledge(f"extracted_from_{source}", content)
    return True
