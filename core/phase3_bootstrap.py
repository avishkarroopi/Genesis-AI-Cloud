"""
GENESIS — Phase-3 Bootstrap
Safely re-enables disabled subsystems (emotion, motion, behavior)
AFTER voice initialization is complete.

Called by the cognitive orchestrator startup — NOT by system.py.
All modules communicate via event bus only.
"""

import logging
import threading
import time

logger = logging.getLogger(__name__)

# Feature flags — set to False to disable individual subsystems
ENABLE_EMOTION = True
ENABLE_MOTION = True
ENABLE_BEHAVIOR = True

_bootstrapped = False
_lock = threading.Lock()


def bootstrap_phase3_subsystems():
    """
    Safely start disabled Phase-1 subsystems.
    Must be called AFTER voice initialization is complete.
    Idempotent — will not run twice.
    """
    global _bootstrapped
    with _lock:
        if _bootstrapped:
            return
        _bootstrapped = True

    logger.info("[BOOTSTRAP] Starting Phase-3 subsystem bootstrap...")

    # ── Emotion Engine ──
    if ENABLE_EMOTION:
        try:
            from core import emotion_engine
            if hasattr(emotion_engine, 'start_emotion_engine'):
                emotion_engine.start_emotion_engine()
                logger.info("[BOOTSTRAP] ✓ Emotion engine started")
            else:
                logger.info("[BOOTSTRAP] ✓ Emotion engine loaded (no start function)")
        except Exception as e:
            logger.warning(f"[BOOTSTRAP] Emotion engine skipped: {e}")

    # ── Motion System ──
    if ENABLE_MOTION:
        try:
            from core import motion_system
            if hasattr(motion_system, 'start_motion_system'):
                motion_system.start_motion_system()
                logger.info("[BOOTSTRAP] ✓ Motion system started")
            else:
                logger.info("[BOOTSTRAP] ✓ Motion system loaded (no start function)")
        except Exception as e:
            logger.warning(f"[BOOTSTRAP] Motion system skipped: {e}")

    # ── Behavior Engine ──
    if ENABLE_BEHAVIOR:
        try:
            from core import behavior_engine
            if hasattr(behavior_engine, 'start_behavior_engine'):
                behavior_engine.start_behavior_engine()
                logger.info("[BOOTSTRAP] ✓ Behavior engine started")
            else:
                logger.info("[BOOTSTRAP] ✓ Behavior engine loaded (no start function)")
        except Exception as e:
            logger.warning(f"[BOOTSTRAP] Behavior engine skipped: {e}")

    # ── Phase 1 & 1.5 Tools and Agents ──
    try:
        from core.tools.init_tools import init_all_tools
        init_all_tools()
        logger.info("[BOOTSTRAP] ✓ Tool Layer initialized")
    except Exception as e:
        logger.warning(f"[BOOTSTRAP] Tool Layer initialization skipped: {e}")

    try:
        from core.agents.init_agents import init_all_agents
        init_all_agents()
        logger.info("[BOOTSTRAP] ✓ Agent Layer initialized")
    except Exception as e:
        logger.warning(f"[BOOTSTRAP] Agent Layer initialization skipped: {e}")

    logger.info("[BOOTSTRAP] Phase-3 subsystem bootstrap complete")


def delayed_bootstrap(delay: float = 5.0):
    """
    Start bootstrap after a delay to ensure voice is fully initialized.
    Run on a daemon thread for non-blocking startup.
    """
    def _run():
        time.sleep(delay)
        bootstrap_phase3_subsystems()

    t = threading.Thread(target=_run, daemon=True, name="Phase3Bootstrap")
    t.start()
    return t
