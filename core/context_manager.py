"""
Phase C — Context Manager
Builds the final AI prompt context safely without hallucination.
Phase-1 Upgrade: Closes the learning loop by retrieving past experiences.
"""

try:
    from core.owner_system import OwnerProfile
except ImportError:
    class OwnerProfile:
        def get_full_profile(self): return {}

_profile_instance = OwnerProfile()


def retrieve_similar_experiences(command, n_results=3):
    """Retrieve past experiences from ChromaDB that are relevant to the current command.
    Returns a formatted string of experiences, or empty string on failure."""
    try:
        from core.memory.memory_search import search_memory_safe
        results = search_memory_safe(
            command,
            n_results=n_results,
            filter_metadata={"type": "experience"}
        )
        if results and isinstance(results, list):
            lines = []
            for i, exp in enumerate(results[:3], 1):
                lines.append(f"{i}. {exp}")
            return "\n".join(lines)
    except Exception as e:
        print(f"[CONTEXT] Experience retrieval failed (non-fatal): {e}", flush=True)
    return ""


def build_context(command, memory_context, vector_memories, conversation_context):
    # --- Phase-1: Retrieve relevant past experiences ---
    experience_section = ""
    try:
        experiences = retrieve_similar_experiences(command)
        if experiences:
            experience_section = f"Relevant Past Experiences:\n{experiences}\n\n"
    except Exception:
        experience_section = ""

    try:
        profile = _profile_instance.get_full_profile()
        profile_lines = [f"{k}: {v}" for k, v in profile.items()]
        profile_context = "\n".join(profile_lines)
    except Exception:
        profile_context = ""

    if isinstance(vector_memories, list):
        vector_memory_context = "\n".join(vector_memories) if vector_memories else ""
    else:
        vector_memory_context = str(vector_memories)
        
    vector_memory_context = vector_memory_context[:2000]

    return f"""{experience_section}Owner profile:
{profile_context}

Known memory:
{memory_context}

Vector memory:
{vector_memory_context}

Conversation context:
{conversation_context}

Rules:
Use this information including past experiences to improve your response.
Do not hallucinate unknown facts."""
