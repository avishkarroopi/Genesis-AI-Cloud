"""
GENESIS — Orphan Event Bridge
Connects orphaned events to intelligence consumers.

Subscribes to:
  - LIFE_OS_UPDATE → routes to Cognitive Orchestrator scheduling
  - GOAL_PROGRESS_UPDATED → routes to Mission Manager + Prediction Engine

No protected files modified. Pure event bus wiring.
"""

import logging

logger = logging.getLogger(__name__)

_bridge_active = False


def start_orphan_bridge():
    """Subscribe to orphaned events and route to Phase-3 consumers."""
    global _bridge_active
    if _bridge_active:
        return
    _bridge_active = True

    try:
        from core.event_bus import get_event_bus
        bus = get_event_bus()
        if not bus:
            logger.warning("[ORPHAN_BRIDGE] Event bus not available")
            return

        # ── LIFE_OS_UPDATE → Cognitive Orchestrator ──
        def _on_life_os_update(event):
            try:
                data = event.data if hasattr(event, 'data') else event
                # Route to orchestrator scheduler
                try:
                    from core.cognitive_orchestrator import get_cognitive_orchestrator
                    orch = get_cognitive_orchestrator()
                    orch.scheduler.schedule("life_os_evaluation", data, priority=6)
                except Exception:
                    pass
            except Exception as e:
                logger.error(f"[ORPHAN_BRIDGE] LIFE_OS_UPDATE handler error: {e}")

        bus.subscribe("LIFE_OS_UPDATE", _on_life_os_update)

        # ── GOAL_PROGRESS_UPDATED → Mission Manager + Prediction ──
        def _on_goal_progress(event):
            try:
                data = event.data if hasattr(event, 'data') else event
                # Route to mission manager
                try:
                    from core.executive_control import get_mission_manager
                    mm = get_mission_manager()
                    goal_id = data.get("goal_id", "")
                    progress = data.get("progress", 0)
                    # Update mission tracking
                    for mission in mm.get_active_missions():
                        if goal_id in str(mission.get("goals", [])):
                            mission["progress"] = progress
                except Exception:
                    pass

                # Forward to prediction engine for pattern learning
                try:
                    bus.publish_sync("GOAL_PROGRESS_FORWARDED", "orphan_bridge", data)
                except Exception:
                    pass
            except Exception as e:
                logger.error(f"[ORPHAN_BRIDGE] GOAL_PROGRESS handler error: {e}")

        bus.subscribe("GOAL_PROGRESS_UPDATED", _on_goal_progress)

        logger.info("[ORPHAN_BRIDGE] Subscribed: LIFE_OS_UPDATE, GOAL_PROGRESS_UPDATED")
        print("[ORPHAN_BRIDGE] Orphan event bridge active", flush=True)

    except Exception as e:
        logger.error(f"[ORPHAN_BRIDGE] Failed to start: {e}")
