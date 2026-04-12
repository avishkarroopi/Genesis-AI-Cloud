"""
GENESIS Synthetic Intelligence Layer — Phase 2.5
Combines memory, vision, knowledge graph, prediction, and agent state
to generate high-level strategic insights.

Example:
  User building startup + market research + conversation history
  → strategic recommendation
"""

import logging
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)


class SyntheticIntelligence:
    def __init__(self):
        self._running = False
        self._last_insight: Optional[Dict] = None
        logger.info("[SYNTH-AI] Synthetic Intelligence Layer initialized")

    def start(self):
        self._running = True
        try:
            from core.event_bus import get_event_bus
            bus = get_event_bus()
            if bus:
                bus.subscribe("SYNTHETIC_INSIGHT_REQUEST", self._handle_request)
                bus.subscribe("GOAL_CREATED", self._on_goal_context)
            logger.info("[SYNTH-AI] EventBus subscriptions active")
        except Exception as e:
            logger.warning(f"[SYNTH-AI] EventBus bind failed: {e}")

    def generate_insight(self, query: str = "", context: Dict = None) -> Dict[str, Any]:
        """
        Aggregate intelligence sources and produce a strategic insight.
        """
        aggregated = {"query": query, "timestamp": datetime.now().isoformat()}

        # 1. Recent life memory
        try:
            from core.memory.life_memory_engine import get_life_memory_engine
            engine = get_life_memory_engine()
            recent = engine.get_recent(limit=10)
            aggregated["life_context"] = [e["content"][:100] for e in recent]
        except Exception as e:
            aggregated["life_context"] = []
            logger.debug(f"[SYNTH-AI] Life memory unavailable: {e}")

        # 2. Active goals from goal engine
        try:
            from core.goal_engine import get_goal_engine
            goals = get_goal_engine().get_active_goals()
            aggregated["active_goals"] = [g["description"] for g in goals[:5]]
        except Exception:
            aggregated["active_goals"] = []

        # 3. Knowledge graph stats
        try:
            from core.knowledge_graph import get_knowledge_graph
            kg = get_knowledge_graph()
            stats = kg.get_stats()
            aggregated["knowledge_nodes"] = stats.get("total_nodes", 0)
        except Exception:
            aggregated["knowledge_nodes"] = 0

        # 4. World model snapshot
        try:
            from core.world_model import get_world_model
            wm = get_world_model()
            world_stats = wm.get_stats()
            aggregated["world_snapshot"] = world_stats
        except Exception:
            aggregated["world_snapshot"] = {}

        # 5. Agent scheduler state
        try:
            from core.agents.agent_scheduler import get_agent_scheduler
            sched_stats = get_agent_scheduler().get_stats()
            aggregated["agent_state"] = sched_stats
        except Exception:
            aggregated["agent_state"] = {}

        # 6. Self-improvement suggestions
        try:
            from core.monitoring.self_improvement_engine import get_self_improvement_engine
            suggestions = get_self_improvement_engine().get_suggestions()
            aggregated["performance_suggestions"] = suggestions[:3]
        except Exception:
            aggregated["performance_suggestions"] = []

        # Synthesize a text recommendation
        insight_text = self._synthesize(aggregated, query)

        insight = {
            "timestamp": aggregated["timestamp"],
            "query": query,
            "aggregated_sources": list(aggregated.keys()),
            "insight": insight_text,
            "raw": aggregated,
        }
        self._last_insight = insight

        # Publish result
        try:
            from core.event_bus import get_event_bus
            bus = get_event_bus()
            if bus:
                bus.publish_sync("SYNTHETIC_INSIGHT", "synthetic_intelligence",
                                 {"insight": insight_text, "context": aggregated})
        except Exception:
            pass

        logger.info(f"[SYNTH-AI] Insight generated for query: '{query[:50]}'")
        return insight

    def _synthesize(self, data: Dict, query: str) -> str:
        """Build a plain-language synthesis from aggregated sources."""
        parts = []

        goals = data.get("active_goals", [])
        if goals:
            parts.append(f"Current focus areas: {'; '.join(goals[:3])}.")

        life_ctx = data.get("life_context", [])
        if life_ctx:
            parts.append(f"Recent activities include: {life_ctx[0][:80]}.")

        suggestions = data.get("performance_suggestions", [])
        if suggestions:
            parts.append(f"Performance note: {suggestions[0].get('recommendation', '')}.")

        knowledge = data.get("knowledge_nodes", 0)
        if knowledge:
            parts.append(f"Knowledge base contains {knowledge} nodes.")

        if not parts:
            return "Insufficient data to generate strategic insight at this time."

        synthesis = " ".join(parts)
        if query:
            synthesis = f"Regarding '{query}': {synthesis}"
        return synthesis

    def _handle_request(self, source: str, data: dict):
        query = data.get("query", "")
        self.generate_insight(query=query, context=data)

    def _on_goal_context(self, source: str, data: dict):
        """Auto-generate insight when a new goal is created."""
        try:
            self.generate_insight(query=data.get("description", ""))
        except Exception:
            pass

    def get_last_insight(self) -> Optional[Dict]:
        return self._last_insight


_synthetic_ai: Optional[SyntheticIntelligence] = None


def get_synthetic_intelligence() -> SyntheticIntelligence:
    global _synthetic_ai
    if _synthetic_ai is None:
        _synthetic_ai = SyntheticIntelligence()
    return _synthetic_ai


def start_synthetic_intelligence() -> SyntheticIntelligence:
    si = get_synthetic_intelligence()
    si.start()
    return si
