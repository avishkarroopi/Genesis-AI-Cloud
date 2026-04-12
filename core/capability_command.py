"""
GENESIS — Capability Command
Improvement 8: "Genesis what can you do" voice command handler.

Reads from capability registry and returns a spoken list of abilities.
Registered as a tool in tool_registry.
"""

import logging
from typing import List

logger = logging.getLogger(__name__)

# Static capability manifest — these are GENESIS's verified abilities
CAPABILITIES = [
    ("Voice Interaction", "I can listen and respond using natural speech with Whisper and Piper TTS."),
    ("Wake Word Detection", "I activate when you say 'Genesis' and listen for your command."),
    ("Memory", "I can remember things you tell me and recall them later using semantic memory."),
    ("Vision", "I can detect objects using YOLO and reason about scenes using LLaVA."),
    ("Knowledge Graph", "I maintain a knowledge graph of people, objects, and relationships."),
    ("Automation", "I can open websites, search the web, and trigger automation workflows."),
    ("Agent Framework", "I can plan and execute multi-step goals using the Goal-Task-Skill architecture."),
    ("Prediction", "I can anticipate future needs based on behavior patterns and schedule analysis."),
    ("Digital Twin", "I maintain a behavioral model to simulate and predict decisions."),
    ("System Diagnostics", "I can run a full system health check when you ask for a diagnostic."),
    ("Creativity", "I can generate creative ideas, analogies, and concept blends."),
    ("Identity Recognition", "I can learn and recognize people using visual identity enrollment."),
    ("Ethical Safety", "I audit all actions against safety and value alignment rules before execution."),
    ("Face Animation", "I display emotions and lip-synced mouth movements on the avatar UI."),
    ("Life OS", "I track goals, habits, health, finances, and learning progress."),
]


def get_capability_list() -> List[str]:
    """Return list of capability names."""
    return [name for name, _ in CAPABILITIES]


def capability_spoken_summary() -> str:
    """Return a natural language summary of GENESIS capabilities."""
    names = [name for name, _ in CAPABILITIES]
    count = len(names)

    # Build a natural list
    if count <= 5:
        listing = ", ".join(names)
    else:
        listing = ", ".join(names[:7]) + f", and {count - 7} more capabilities"

    return (
        f"I currently have {count} active capabilities, sir. "
        f"These include {listing}. "
        f"You can ask me about any specific capability for more details."
    )


def capability_detailed_summary() -> str:
    """Return a detailed capability listing."""
    lines = [f"{name}: {desc}" for name, desc in CAPABILITIES]
    return "\n".join(lines)


def register_capability_tool():
    """Register the capability command as a tool in the tool registry."""
    try:
        from core.tool_registry import get_tool_registry, ToolType

        registry = get_tool_registry()

        async def _capability_tool() -> str:
            return capability_spoken_summary()

        registry.register_tool(
            "list_capabilities",
            "List Capabilities",
            "List all GENESIS system capabilities and abilities",
            ToolType.SYSTEM_COMMAND,
            _capability_tool,
            return_type=str,
        )
        logger.info("[CAPABILITY] Tool registered: list_capabilities")
    except Exception as e:
        logger.warning(f"[CAPABILITY] Tool registration failed: {e}")
