"""
GENESIS Phase-3 — Cognitive Orchestrator
Module 10: Meta-intelligence controller for attention management,
goal prioritization, system focus, decision scheduling, and autonomous reasoning.

Extends existing core/cognition/cognitive_loop.py.
Coordinates executive control, prediction, and ethical layers.
"""

import threading
import time
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from collections import deque

logger = logging.getLogger(__name__)


class AttentionManager:
    """Manages system focus allocation across modules."""

    def __init__(self):
        self._focus_weights: Dict[str, float] = {
            "voice": 1.0,
            "vision": 0.7,
            "prediction": 0.3,
            "creativity": 0.2,
            "ethics": 0.8,
        }
        self._active_focus: Optional[str] = "voice"

    def set_focus(self, domain: str, weight: float = 1.0):
        """Set attention weight for a domain."""
        self._focus_weights[domain] = max(0.0, min(1.0, weight))
        # Auto-select highest focus
        self._active_focus = max(self._focus_weights, key=self._focus_weights.get)

    def get_focus(self) -> str:
        return self._active_focus or "voice"

    def get_weights(self) -> Dict[str, float]:
        return dict(self._focus_weights)

    def should_process(self, domain: str) -> bool:
        """Check if a domain's weight is high enough to warrant processing."""
        return self._focus_weights.get(domain, 0) >= 0.3


class DecisionScheduler:
    """Queue and schedule autonomous reasoning tasks."""

    def __init__(self):
        self._queue: deque = deque(maxlen=100)
        self._completed: deque = deque(maxlen=200)
        self._lock = threading.Lock()

    def schedule(self, task_type: str, context: Dict = None,
                 priority: int = 5) -> str:
        """Schedule a reasoning task. Priority: 1 (highest) to 10 (lowest)."""
        task_id = f"sched_{task_type}_{int(time.time())}"
        task = {
            "id": task_id,
            "type": task_type,
            "context": context or {},
            "priority": priority,
            "scheduled_at": datetime.now().isoformat(),
            "status": "pending",
        }
        with self._lock:
            self._queue.append(task)
            # Sort by priority
            sorted_q = sorted(self._queue, key=lambda t: t["priority"])
            self._queue.clear()
            self._queue.extend(sorted_q)
        return task_id

    def get_next(self) -> Optional[Dict]:
        """Get the next task to process."""
        with self._lock:
            if self._queue:
                task = self._queue.popleft()
                task["status"] = "processing"
                return task
        return None

    def complete(self, task: Dict, result: Any = None):
        task["status"] = "completed"
        task["completed_at"] = datetime.now().isoformat()
        task["result"] = result
        self._completed.append(task)

    def get_queue_size(self) -> int:
        return len(self._queue)


class CognitiveOrchestrator:
    """
    Meta-intelligence controller that orchestrates all Phase-3 modules.
    Runs a daemon loop coordinating attention, scheduling, and reasoning.
    """

    def __init__(self):
        self.attention = AttentionManager()
        self.scheduler = DecisionScheduler()
        self._running = False
        self._thread = None
        self._cycle_count = 0
        self._bus = None
        self._orchestration_interval = 15.0  # seconds
        logger.info("[ORCHESTRATOR] Cognitive Orchestrator initialized")

    def bind_event_bus(self):
        try:
            from core.event_bus import get_event_bus
            self._bus = get_event_bus()
            if self._bus:
                self._bus.subscribe("MISSION_UPDATE", self._on_mission_update)
                self._bus.subscribe("SAFETY_VETO", self._on_safety_veto)
                self._bus.subscribe("ENVIRONMENT_PREDICTION", self._on_env_prediction)
                self._bus.subscribe("ACTIVITY_DETECTED", self._on_activity)
                self._bus.subscribe("INTERACTION_INSIGHT", self._on_interaction)
                logger.info("[ORCHESTRATOR] Event bus bound — monitoring all Phase-3 signals")
        except Exception as e:
            logger.warning(f"[ORCHESTRATOR] Event bus binding failed: {e}")

    def start(self):
        """Start the orchestration loop."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._orchestration_loop,
                                         daemon=True, name="CognitiveOrchestrator")
        self._thread.start()
        logger.info("[ORCHESTRATOR] Orchestration loop started")

    def stop(self):
        self._running = False
        logger.info("[ORCHESTRATOR] Orchestration loop stopped")

    def _orchestration_loop(self):
        """Main orchestration loop — processes scheduled tasks and coordinates modules."""
        while self._running:
            try:
                self._cycle()
                self._cycle_count += 1
            except Exception as e:
                logger.error(f"[ORCHESTRATOR] Cycle error: {e}")
            time.sleep(self._orchestration_interval)

    def _cycle(self):
        """Single orchestration cycle."""
        # Process scheduled tasks
        task = self.scheduler.get_next()
        if task:
            result = self._process_task(task)
            self.scheduler.complete(task, result)

        # Periodic coordination check
        if self._cycle_count % 4 == 0:
            self._coordinate_modules()

    def _process_task(self, task: Dict) -> Any:
        """Process a scheduled reasoning task."""
        task_type = task.get("type", "")

        if task_type == "attention_shift":
            domain = task.get("context", {}).get("domain", "voice")
            self.attention.set_focus(domain)
            return {"focus_shifted_to": domain}

        elif task_type == "safety_review":
            return {"reviewed": True, "timestamp": datetime.now().isoformat()}

        elif task_type == "mission_evaluation":
            return self._evaluate_missions()

        return {"processed": True}

    def _evaluate_missions(self) -> Dict:
        """Evaluate current missions and suggest prioritization."""
        try:
            from core.executive_control import get_mission_manager
            mm = get_mission_manager()
            active = mm.get_active_missions()
            return {
                "active_missions": len(active),
                "recommendation": "continue" if active else "awaiting_missions",
            }
        except Exception:
            return {"active_missions": 0}

    def _coordinate_modules(self):
        """Periodic check to ensure all Phase-3 modules are healthy."""
        status = self.get_full_status()
        if self._bus:
            try:
                self._bus.publish_sync("ORCHESTRATOR_HEARTBEAT", "cognitive_orchestrator", status)
            except Exception:
                pass

    # ── Event Handlers ──

    def _on_mission_update(self, event):
        try:
            data = event.data if hasattr(event, 'data') else event
            self.scheduler.schedule("mission_evaluation", data, priority=3)
        except Exception as e:
            logger.error(f"[ORCHESTRATOR] Mission handler error: {e}")

    def _on_safety_veto(self, event):
        try:
            data = event.data if hasattr(event, 'data') else event
            logger.warning(f"[ORCHESTRATOR] Safety veto received: {data}")
            # Shift attention to safety
            self.attention.set_focus("ethics", 1.0)
        except Exception as e:
            logger.error(f"[ORCHESTRATOR] Safety veto handler error: {e}")

    def _on_env_prediction(self, event):
        try:
            data = event.data if hasattr(event, 'data') else event
            if data.get("confidence", 0) > 0.6:
                self.scheduler.schedule("attention_shift",
                                         {"domain": "vision"}, priority=4)
        except Exception as e:
            logger.error(f"[ORCHESTRATOR] Env prediction handler error: {e}")

    def _on_activity(self, event):
        try:
            data = event.data if hasattr(event, 'data') else event
            logger.info(f"[ORCHESTRATOR] Activity detected: {data.get('activity', '?')}")
        except Exception as e:
            logger.error(f"[ORCHESTRATOR] Activity handler error: {e}")

    def _on_interaction(self, event):
        try:
            data = event.data if hasattr(event, 'data') else event
            # Shift attention to voice when interaction happens
            self.attention.set_focus("voice", 1.0)
        except Exception as e:
            logger.error(f"[ORCHESTRATOR] Interaction handler error: {e}")

    def get_full_status(self) -> Dict[str, Any]:
        return {
            "running": self._running,
            "cycles": self._cycle_count,
            "focus": self.attention.get_focus(),
            "attention_weights": self.attention.get_weights(),
            "scheduled_tasks": self.scheduler.get_queue_size(),
        }


_orchestrator = None
_orch_lock = threading.Lock()


def get_cognitive_orchestrator() -> CognitiveOrchestrator:
    global _orchestrator
    if _orchestrator is None:
        with _orch_lock:
            if _orchestrator is None:
                _orchestrator = CognitiveOrchestrator()
    return _orchestrator


def start_cognitive_orchestrator():
    """Initialize, bind, and start the cognitive orchestrator.
    Also bootstraps all hardening modules (non-fatal on failure).
    """
    orch = get_cognitive_orchestrator()
    orch.bind_event_bus()
    orch.start()
    print("[ORCHESTRATOR] Cognitive Orchestrator started", flush=True)

    # ── Hardening: Phase-3 Bootstrap (emotion/motion/behavior) ──
    try:
        from core.phase3_bootstrap import delayed_bootstrap
        delayed_bootstrap(delay=5.0)
        logger.info("[ORCHESTRATOR] Phase-3 subsystem bootstrap scheduled (5s delay)")
    except Exception as e:
        logger.warning(f"[ORCHESTRATOR] Phase-3 bootstrap skipped: {e}")

    # ── Hardening: Orphan Event Bridge ──
    try:
        from core.orphan_event_bridge import start_orphan_bridge
        start_orphan_bridge()
    except Exception as e:
        logger.warning(f"[ORCHESTRATOR] Orphan bridge skipped: {e}")

    # ── Hardening: System Health Monitor ──
    try:
        from core.system_health_monitor import start_health_monitor
        start_health_monitor()
    except Exception as e:
        logger.warning(f"[ORCHESTRATOR] Health monitor skipped: {e}")

    # ── Hardening: Thread Watchdog ──
    try:
        from core.thread_watchdog import start_watchdog, register_thread
        start_watchdog()
        # Register the orchestrator's own thread
        if orch._thread:
            register_thread("CognitiveOrchestrator", orch._thread)
    except Exception as e:
        logger.warning(f"[ORCHESTRATOR] Thread watchdog skipped: {e}")

    # ── Hardening: Register diagnostic/capability/vision tools ──
    try:
        from core.diagnostic_command import register_diagnostic_tool
        register_diagnostic_tool()
    except Exception as e:
        logger.warning(f"[ORCHESTRATOR] Diagnostic tool registration skipped: {e}")

    try:
        from core.capability_command import register_capability_tool
        register_capability_tool()
    except Exception as e:
        logger.warning(f"[ORCHESTRATOR] Capability tool registration skipped: {e}")

    try:
        from core.vision_context import register_vision_context_tool
        register_vision_context_tool()
    except Exception as e:
        logger.warning(f"[ORCHESTRATOR] Vision context tool registration skipped: {e}")

    return orch
