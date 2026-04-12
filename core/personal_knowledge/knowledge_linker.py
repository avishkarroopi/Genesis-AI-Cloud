"""
Knowledge Linker (Phase-2 User Intelligence)
Builds relationships between knowledge nodes natively in unified memory.
"""

from core.memory.memory_manager import store_knowledge

def link_concepts(concept_a: str, concept_b: str, relationship: str):
    """Store relationship edge in memory."""
    text_entry = f"[KnowledgeLink] {concept_a} -> {concept_b} ({relationship})"
    return store_knowledge(text_entry)
