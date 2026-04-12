"""
Context Router (Layer 2 - Intelligence)
Routes context requests depending on whether they come from voice UI (Brain) 
or from background Agent tasks.
"""

from core.context_engine.context_engine import build_context, get_agent_context

class ContextRouter:
    def __init__(self):
        pass

    def route_request(self, requester: str, **kwargs) -> str:
        if requester == "brain":
            return build_context(
                kwargs.get("command", ""),
                kwargs.get("memory_context", ""),
                kwargs.get("vector_memories", []),
                kwargs.get("conversation_history", "")
            )
        elif requester == "agent":
            return get_agent_context(
                kwargs.get("task", ""),
                kwargs.get("goal", "")
            )
        else:
            return "Unknown context requester."

router = ContextRouter()

def get_context_router() -> ContextRouter:
    return router
