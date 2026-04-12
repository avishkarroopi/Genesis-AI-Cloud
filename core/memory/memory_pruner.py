"""
GENESIS Memory Pruner
Applies external pruning logic to the experience memory store without modifying its core code.
"""

import logging
from core.event_bus import get_event_bus
from core.experience_memory import get_experience_memory

logger = logging.getLogger(__name__)

async def handle_prune_check(source: str, data: dict):
    """
    Triggered when new experiences are recorded.
    Applies pruning logic safely from outside experience_memory.py.
    """
    try:
        memory = get_experience_memory()
        
        # We only prune if we are getting close to max capacity
        if len(memory._store) > (memory.MAX_EXPERIENCES * 0.9):
            logger.info("[MEMORY PRUNER] Capacity at 90%, starting pruning.")
            with memory._lock:
                items = list(memory._store)
                
                # Logic: preserve all successful actions, prune the oldest non-successful ones.
                # Keep the last 1000 items regardless of success to preserve recent context.
                recent_threshold = len(items) - 1000
                
                pruned = []
                for i, exp in enumerate(items):
                    if exp.success or i >= recent_threshold:
                        pruned.append(exp)
                
                pruned_clean = len(items) - len(pruned)
                if pruned_clean > 0:
                    memory._store.clear()
                    memory._store.extend(pruned)
                    logger.info(f"[MEMORY PRUNER] Pruned {pruned_clean} low-value experiences.")
                    
    except Exception as e:
        logger.error(f"[MEMORY PRUNER] Error during pruning: {e}")

def initialize_memory_pruner():
    """Subscribe to EventBus to trigger pruning."""
    bus = get_event_bus()
    if bus:
        bus.subscribe("EXPERIENCE_RECORDED", handle_prune_check)
        logger.info("[MEMORY PRUNER] Initialized and subscribed to EXPERIENCE_RECORDED.")
