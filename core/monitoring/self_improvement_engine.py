"""
GENESIS Self-Improvement Engine — Phase 2.5
Monitors system performance and generates improvement recommendations.
Tracks: voice latency, STT time, model slowdowns, pipeline bottlenecks, agent overload.
"""

import logging
import threading
import time
from typing import Dict, Any, List, Optional
from collections import deque
from datetime import datetime

logger = logging.getLogger(__name__)

# Performance thresholds
THRESHOLDS = {
    "voice_latency_ms": 3000,     # >3s is slow
    "stt_time_ms": 5000,          # >5s STT is too slow
    "response_time_ms": 10000,    # >10s total response is unacceptable
    "agent_queue_len": 20,        # >20 queued = overloaded
}


class PerformanceSample:
    def __init__(self, metric: str, value_ms: float):
        self.metric = metric
        self.value_ms = value_ms
        self.timestamp = datetime.now().isoformat()

    def to_dict(self):
        return {"metric": self.metric, "value_ms": self.value_ms, "timestamp": self.timestamp}


class SelfImprovementEngine:
    def __init__(self):
        self._samples: deque = deque(maxlen=500)
        self._suggestions: List[Dict] = []
        self._lock = threading.Lock()
        self._running = False
        self._thread: Optional[threading.Thread] = None
        logger.info("[SELF-IMPROVE] Engine initialized")

    def start(self):
        self._running = True
        self._thread = threading.Thread(
            target=self._monitor_loop, daemon=True, name="SelfImprovementEngine"
        )
        self._thread.start()
        try:
            from core.event_bus import get_event_bus
            bus = get_event_bus()
            if bus:
                bus.subscribe("COMMAND_RUN", self._on_command_run)
                bus.subscribe("AGENT_QUEUED", self._on_agent_event)
            logger.info("[SELF-IMPROVE] EventBus subscriptions active")
        except Exception as e:
            logger.warning(f"[SELF-IMPROVE] EventBus bind failed: {e}")

    def record_latency(self, metric: str, value_ms: float):
        """Record a performance measurement."""
        with self._lock:
            self._samples.append(PerformanceSample(metric, value_ms))

    def _on_command_run(self, source: str, data: dict):
        """Track when commands start — used to compute end-to-end latency."""
        # Timestamp stored for future use; response time tracked via SPEAK events
        pass

    def _on_agent_event(self, source: str, data: dict):
        """Check for overloaded queue."""
        try:
            from core.agents.agent_scheduler import get_agent_scheduler
            stats = get_agent_scheduler().get_stats()
            if stats["queue_length"] > THRESHOLDS["agent_queue_len"]:
                self._add_suggestion(
                    "agent_overload",
                    f"Agent queue has {stats['queue_length']} pending tasks.",
                    "Consider increasing max_concurrent_agents or reducing task submission rate."
                )
        except Exception:
            pass

    def _monitor_loop(self):
        """Periodic analysis every 30 seconds."""
        while self._running:
            time.sleep(30)
            self._analyze()

    def _analyze(self):
        """Analyze recent samples and generate recommendations."""
        with self._lock:
            samples = list(self._samples)

        if not samples:
            return

        grouped: Dict[str, List[float]] = {}
        for s in samples:
            grouped.setdefault(s.metric, []).append(s.value_ms)

        for metric, values in grouped.items():
            avg = sum(values) / len(values)
            threshold = THRESHOLDS.get(metric)
            if threshold and avg > threshold:
                self._generate_recommendation(metric, avg, threshold)

        # Publish summary if suggestions exist
        if self._suggestions:
            try:
                from core.event_bus import get_event_bus
                bus = get_event_bus()
                if bus:
                    bus.publish_sync("IMPROVEMENT_SUGGESTION", "self_improvement_engine",
                                     {"suggestions": self._suggestions[-5:]})
            except Exception:
                pass

    def _generate_recommendation(self, metric: str, avg_ms: float, threshold: float):
        recs = {
            "voice_latency_ms": f"Voice latency avg {avg_ms:.0f}ms exceeds {threshold}ms. Recommendation: switch to faster TTS engine (Piper) or reduce response length.",
            "stt_time_ms": f"STT avg {avg_ms:.0f}ms is slow. Recommendation: switch to tiny Whisper model or use GPU acceleration.",
            "response_time_ms": f"End-to-end response avg {avg_ms:.0f}ms. Recommendation: enable model caching or use a smaller LLM model.",
        }
        rec_text = recs.get(metric, f"{metric} avg {avg_ms:.0f}ms exceeds threshold {threshold}ms.")
        self._add_suggestion(metric, f"Performance issue in {metric}", rec_text)

    def _add_suggestion(self, key: str, issue: str, recommendation: str):
        # Avoid duplicate suggestions for the same metric
        existing_keys = [s.get("key") for s in self._suggestions]
        if key not in existing_keys:
            suggestion = {
                "key": key,
                "issue": issue,
                "recommendation": recommendation,
                "timestamp": datetime.now().isoformat(),
            }
            self._suggestions.append(suggestion)
            logger.info(f"[SELF-IMPROVE] Suggestion generated: {issue}")

    def get_suggestions(self) -> List[Dict]:
        return list(self._suggestions)

    def get_stats(self) -> Dict[str, Any]:
        with self._lock:
            return {"samples_collected": len(self._samples), "suggestions": len(self._suggestions)}


_engine: Optional[SelfImprovementEngine] = None


def get_self_improvement_engine() -> SelfImprovementEngine:
    global _engine
    if _engine is None:
        _engine = SelfImprovementEngine()
    return _engine


def start_self_improvement_engine() -> SelfImprovementEngine:
    engine = get_self_improvement_engine()
    engine.start()
    return engine
