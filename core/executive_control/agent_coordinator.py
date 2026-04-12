"""
GENESIS Phase-3 — Executive Control: Agent Coordinator
Multi-agent coordination and task delegation across the agent framework.
"""

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class AgentCoordinator:
    """Coordinates multiple agents for complex multi-step missions."""

    def __init__(self):
        self._active_delegations: Dict[str, Dict[str, Any]] = {}
        self._bus = None
        logger.info("[COORDINATOR] Agent Coordinator initialized")

    def bind_event_bus(self):
        try:
            from core.event_bus import get_event_bus
            self._bus = get_event_bus()
        except Exception as e:
            logger.warning(f"[COORDINATOR] Event bus binding failed: {e}")

    def delegate_task(self, agent_type: str, task_description: str,
                      priority: str = "medium", context: Dict = None) -> Optional[str]:
        """Delegate a task to a specific agent type."""
        import time
        delegation_id = f"deleg_{agent_type}_{int(time.time())}"

        self._active_delegations[delegation_id] = {
            "agent_type": agent_type,
            "task": task_description,
            "priority": priority,
            "context": context or {},
            "status": "assigned"
        }

        if self._bus:
            self._bus.publish_sync("AGENT_DIRECTIVE", "agent_coordinator", {
                "delegation_id": delegation_id,
                "agent_type": agent_type,
                "task": task_description,
                "priority": priority,
            })

        logger.info(f"[COORDINATOR] Delegated to {agent_type}: {task_description}")
        return delegation_id

    def get_active_delegations(self) -> Dict[str, Dict[str, Any]]:
        return dict(self._active_delegations)

    def get_status(self) -> Dict[str, Any]:
        return {
            "active_delegations": len(self._active_delegations),
        }


_agent_coordinator = None


def get_agent_coordinator() -> AgentCoordinator:
    global _agent_coordinator
    if _agent_coordinator is None:
        _agent_coordinator = AgentCoordinator()
    return _agent_coordinator
