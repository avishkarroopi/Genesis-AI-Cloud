"""
Context Engine Layer (Layer 2 - Intelligence)
Wraps the existing `core/context_manager.py` to seamlessly provide context capabilities
to agents without modifying the functional historical modules.
"""

from core import context_manager

def build_context(command: str, memory_context: str, vector_memories: list, conversation_history: str) -> str:
    """
    Core wrapper around the historical context_manager.build_context.
    """
    try:
        return context_manager.build_context(command, memory_context, vector_memories, conversation_history)
    except Exception as e:
        print(f"[CONTEXT ENGINE] Error building generic context: {e}")
        return "Context Engine offline."

def get_agent_context(task: str, current_goal: str) -> str:
    """
    Provides context customized for the Agent Task Planner.
    Incorporates world model state and User Intelligence (Phase 2).
    """
    context = ""
    try:
        from core.world_model import get_world_model
        wm = get_world_model()
        world_state = wm.get_current_state()
        context += f"Current World State:\n{world_state}\n\n"
    except Exception as e:
        context += f"World State Unavailable.\n\n"

    try:
        from core.digital_twin.goal_profile import get_current_life_goals
        from core.digital_twin.decision_pattern_model import get_decision_patterns
        goals = get_current_life_goals()
        patterns = get_decision_patterns()
        context += f"User Life Goals: {goals}\nDecision Patterns: {patterns}\n\n"
    except Exception:
        pass
        
    context += f"Current Goal: {current_goal}\nTask Focus: {task}\n"
    return context
