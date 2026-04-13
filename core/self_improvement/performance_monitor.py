"""
GENESIS Self-Improvement: Performance Monitor
Listens for completed traces on the Intelligence Bus and triages failures.
"""
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class PerformanceMonitor:
    def evaluate_trace(self, trace_id: str, trace_data: Dict[str, Any]):
        """Check if an interaction failed and push to reflection if necessary."""
        outcome = trace_data.get("outcome", "success")
        
        # In the future, this can use an LLM or heuristic check to grade the response
        if outcome != "success":
            logger.info(f"[MONITOR] Trace {trace_id} flagged as a failure. Triggering reflection.")
            try:
                from core.intelligence_bus import get_intelligence_bus
                bus = get_intelligence_bus()
                bus.publish("REFLECTION_TRIGGERED", {"trace_id": trace_id, "data": trace_data})
            except Exception as e:
                logger.error(f"[MONITOR] Event publish failed: {e}")

_monitor = None
def get_performance_monitor() -> PerformanceMonitor:
    global _monitor
    if _monitor is None:
        _monitor = PerformanceMonitor()
    return _monitor
