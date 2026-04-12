"""
GENESIS — Thread Watchdog
Improvement 6: Monitors critical daemon threads for failures.
Attempts safe restart on thread death. Publishes THREAD_RECOVERY events.

Never crashes the system — only logs and attempts recovery.
"""

import logging
import threading
import time
from typing import Dict, Callable, Optional, Any

logger = logging.getLogger(__name__)

CHECK_INTERVAL = 10.0  # seconds
MAX_RESTARTS = 3

_watchdog_running = False
_watchdog_thread = None
_watched_threads: Dict[str, Dict[str, Any]] = {}
_lock = threading.Lock()


def register_thread(name: str, thread: threading.Thread,
                    restart_fn: Optional[Callable] = None):
    """Register a thread for watchdog monitoring."""
    with _lock:
        _watched_threads[name] = {
            "thread": thread,
            "restart_fn": restart_fn,
            "restart_count": 0,
            "registered_at": time.time(),
        }
    logger.info(f"[WATCHDOG] Registered thread: {name}")


def _check_threads():
    """Check all registered threads and attempt restart if dead."""
    bus = None
    try:
        from core.event_bus import get_event_bus
        bus = get_event_bus()
    except Exception:
        pass

    with _lock:
        for name, info in list(_watched_threads.items()):
            thread = info["thread"]
            if thread is None:
                continue

            if not thread.is_alive():
                restart_count = info["restart_count"]
                if restart_count >= MAX_RESTARTS:
                    logger.error(
                        f"[WATCHDOG] Thread '{name}' dead — max restarts ({MAX_RESTARTS}) exceeded"
                    )
                    continue

                logger.warning(f"[WATCHDOG] Thread '{name}' is dead — attempting restart ({restart_count + 1}/{MAX_RESTARTS})")

                restart_fn = info.get("restart_fn")
                if restart_fn:
                    try:
                        new_thread = restart_fn()
                        if isinstance(new_thread, threading.Thread):
                            info["thread"] = new_thread
                        info["restart_count"] = restart_count + 1

                        if bus:
                            bus.publish_sync("THREAD_RECOVERY", "thread_watchdog", {
                                "thread_name": name,
                                "restart_count": restart_count + 1,
                                "status": "restarted",
                            })
                        logger.info(f"[WATCHDOG] Thread '{name}' restarted successfully")
                    except Exception as e:
                        logger.error(f"[WATCHDOG] Thread '{name}' restart failed: {e}")
                        if bus:
                            bus.publish_sync("THREAD_RECOVERY", "thread_watchdog", {
                                "thread_name": name,
                                "restart_count": restart_count + 1,
                                "status": "failed",
                                "error": str(e),
                            })
                else:
                    logger.warning(f"[WATCHDOG] Thread '{name}' dead but no restart function registered")


def _watchdog_loop():
    """Background watchdog loop."""
    global _watchdog_running

    # Wait for system to stabilize before first check
    time.sleep(30)

    while _watchdog_running:
        try:
            _check_threads()
        except Exception as e:
            logger.error(f"[WATCHDOG] Check cycle error: {e}")
        time.sleep(CHECK_INTERVAL)


def start_watchdog():
    """Start the thread watchdog."""
    global _watchdog_running, _watchdog_thread
    if _watchdog_running:
        return
    _watchdog_running = True
    _watchdog_thread = threading.Thread(
        target=_watchdog_loop, daemon=True, name="ThreadWatchdog"
    )
    _watchdog_thread.start()
    logger.info("[WATCHDOG] Thread Watchdog started")
    print("[WATCHDOG] Thread Watchdog started", flush=True)


def stop_watchdog():
    global _watchdog_running
    _watchdog_running = False


def get_thread_status() -> Dict[str, Any]:
    """Get status of all watched threads (for diagnostic command)."""
    with _lock:
        result = {}
        for name, info in _watched_threads.items():
            thread = info["thread"]
            result[name] = {
                "alive": thread.is_alive() if thread else False,
                "restart_count": info["restart_count"],
            }
        return result
