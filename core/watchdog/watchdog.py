import threading
from core.watchdog.system_monitor import SystemMonitorDaemon # type: ignore

_watchdog_instance = None

def start_watchdog():
    """Bootstraps the stability manager daemon."""
    global _watchdog_instance
    try:
        if _watchdog_instance is None:
            _watchdog_instance = SystemMonitorDaemon()
            t = threading.Thread(target=_watchdog_instance.run_loop, daemon=True, name="SystemWatchdog")
            t.start()
            print("[WATCHDOG] Stability daemon thread started.", flush=True)
    except Exception as e:
        print(f"[WATCHDOG] Failed to start watchdog daemon: {e}", flush=True)
