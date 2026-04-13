"""
GENESIS Reasoning Trace Buffer
Captures the context pipeline of a single AI interaction
from thought to outcome, giving the reflection engine data to analyze.
"""
import time
import json
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class ReasoningTraceBuffer:
    def __init__(self):
        # In a multi-user prod environment, traces should be keyed by user tracking IDs.
        # We store them in a fixed-size in-memory dictionary acting as a ring buffer.
        self._traces: Dict[str, dict] = {}
        self._max_traces = 1000

    def start_trace(self, trace_id: str, prompt: str):
        """Initialize a new cognitive trace."""
        if len(self._traces) > self._max_traces:
            # Prune oldest
            oldest_key = min(self._traces.keys(), key=lambda k: self._traces[k].get("timestamp", 0))
            del self._traces[oldest_key]

        self._traces[trace_id] = {
            "timestamp": time.time(),
            "prompt": prompt,
            "detected_intent": None,
            "planner_decision": None,
            "agent_actions": [],
            "llm_response": None,
            "outcome": "pending"
        }

    def update_intent(self, trace_id: str, intent: str):
        if trace_id in self._traces:
            self._traces[trace_id]["detected_intent"] = intent

    def update_planner(self, trace_id: str, decision: dict):
        if trace_id in self._traces:
            self._traces[trace_id]["planner_decision"] = decision

    def add_agent_action(self, trace_id: str, action: dict):
        if trace_id in self._traces:
            self._traces[trace_id]["agent_actions"].append(action)

    def finalize_response(self, trace_id: str, response: str, outcome: str = "success"):
        if trace_id in self._traces:
            self._traces[trace_id]["llm_response"] = response
            self._traces[trace_id]["outcome"] = outcome
            
            # Emit completed trace to the intelligence bus for self-reflection
            try:
                from core.intelligence_bus import get_intelligence_bus
                bus = get_intelligence_bus()
                bus.publish("TRACE_COMPLETED", {"trace_id": trace_id, "data": self._traces[trace_id]})
            except Exception as e:
                logger.error(f"[TRACE] Failed to publish trace: {e}")

    def get_trace(self, trace_id: str) -> Optional[dict]:
        return self._traces.get(trace_id)


_global_buffer = None

def get_trace_buffer() -> ReasoningTraceBuffer:
    global _global_buffer
    if _global_buffer is None:
        _global_buffer = ReasoningTraceBuffer()
    return _global_buffer
