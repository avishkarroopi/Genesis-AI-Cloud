"""
GENESIS Self-Improvement Engine Orchestrator
Binds the Trace Buffer, Performance Monitor, and Reflection Engine via the Intelligence Bus.
"""
import logging
import asyncio

logger = logging.getLogger(__name__)

def _handle_trace_completed(event):
    """Sync handler for TRACE_COMPLETED from intelligence_bus."""
    try:
        data = event.data
        trace_id = data.get("trace_id")
        trace_data = data.get("data")
        
        from core.self_improvement.performance_monitor import get_performance_monitor
        get_performance_monitor().evaluate_trace(trace_id, trace_data)
    except Exception as e:
        logger.error(f"[SELF-IMPROVE] Error handling TRACE_COMPLETED: {e}")

async def _handle_reflection_triggered(event):
    """Async handler for REFLECTION_TRIGGERED."""
    try:
        data = event.data
        trace_data = data.get("data")
        
        # Push reflection async to not block the bus
        from core.self_improvement.reflection_engine import get_reflection_engine
        # Call it directly - it's an external network call, ideally done via thread pool but async context handles it here
        get_reflection_engine().reflect_on_failure(trace_data)
    except Exception as e:
        logger.error(f"[SELF-IMPROVE] Error handling REFLECTION_TRIGGERED: {e}")

def start_self_improvement_daemon():
    """Wire up the learning pipeline to the Intelligence Bus."""
    try:
        from core.intelligence_bus import get_intelligence_bus
        bus = get_intelligence_bus()
        
        bus.subscribe("TRACE_COMPLETED", _handle_trace_completed)
        bus.subscribe_async("REFLECTION_TRIGGERED", _handle_reflection_triggered)
        
        logger.info("[SELF-IMPROVE] Engine wired to Intelligence Bus.")
    except Exception as e:
        logger.error(f"[SELF-IMPROVE] Daemon start failed: {e}")
