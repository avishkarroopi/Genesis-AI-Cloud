try:
    from core.legacy_agents import (
        get_vision_agent,
        get_voice_agent,
        get_context_memory
    )
except ImportError:
    pass