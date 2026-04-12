"""
Autonomous Reasoning Engine (Unified)
This module has been consolidated to use the unified core.cognition.cognitive_loop engine.
Requirements: 5 (Tesla-level autonomous mode), 8 (task priority system).
"""

from core.cognition.cognitive_loop import (
    CognitiveLoop as AutonomousReasoningEngine,
    get_cognitive_loop as get_reasoning_engine,
    start_cognitive_loop as _start_engine
)

# For backward compatibility with any plugins expecting to set it globally
def set_reasoning_engine(engine):
    pass

# Safe alias for older components
class TaskPriority:
    LOW = 3
    NORMAL = 2
    HIGH = 1
    CRITICAL = 0
