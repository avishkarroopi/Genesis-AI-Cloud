"""
GENESIS — System Health Monitor
Improvement 5: Periodic monitoring daemon that reports system health.

Publishes: SYSTEM_HEALTH_REPORT every 15 seconds
Monitors: event bus, CPU, RAM, GPU, thread health

Does NOT modify any protected file.
"""

import logging
import threading
import time
from typing import Dict, Any

logger = logging.getLogger(__name__)

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

try:
    import GPUtil
    HAS_GPU = True
except ImportError:
    HAS_GPU = False

MONITOR_INTERVAL = 15.0  # seconds

_monitor_running = False
_monitor_thread = None


def _collect_health() -> Dict[str, Any]:
    """Collect system health metrics."""
    health: Dict[str, Any] = {
        "timestamp": time.time(),
    }

    # CPU / RAM
    if HAS_PSUTIL:
        health["cpu_percent"] = psutil.cpu_percent(interval=None)
        mem = psutil.virtual_memory()
        health["ram_percent"] = mem.percent
        health["ram_used_gb"] = round(mem.used / (1024**3), 2)
        health["ram_total_gb"] = round(mem.total / (1024**3), 2)
    else:
        health["cpu_percent"] = None
        health["ram_percent"] = None

    # GPU
    if HAS_GPU:
        try:
            gpus = GPUtil.getGPUs()
            if gpus:
                gpu = gpus[0]
                health["gpu_load_percent"] = round(gpu.load * 100, 1)
                health["gpu_memory_percent"] = round(gpu.memoryUtil * 100, 1)
                health["gpu_temp"] = gpu.temperature
            else:
                health["gpu_load_percent"] = None
        except Exception:
            health["gpu_load_percent"] = None
    else:
        health["gpu_load_percent"] = None

    # Event bus queue
    try:
        from core.event_bus import get_event_bus
        bus = get_event_bus()
        stats = bus.get_stats()
        health["event_bus_queue_size"] = stats.get("queue_size", 0)
        health["event_bus_active_tasks"] = stats.get("active_tasks", 0)
        health["event_bus_running"] = stats.get("running", False)
    except Exception:
        health["event_bus_queue_size"] = None

    # Thread census
    health["active_threads"] = threading.active_count()
    thread_names = [t.name for t in threading.enumerate()]
    health["voice_thread_alive"] = "VoiceSystem" in thread_names
    health["orchestrator_alive"] = "CognitiveOrchestrator" in thread_names

    return health


def _monitor_loop():
    """Background monitoring loop."""
    global _monitor_running
    bus = None
    try:
        from core.event_bus import get_event_bus
        bus = get_event_bus()
    except Exception:
        pass

    while _monitor_running:
        try:
            health = _collect_health()
            if bus:
                bus.publish_sync("SYSTEM_HEALTH_REPORT", "system_health_monitor", health)
        except Exception as e:
            logger.error(f"[HEALTH] Monitor cycle error: {e}")
        time.sleep(MONITOR_INTERVAL)


def start_health_monitor():
    """Start the background health monitor."""
    global _monitor_running, _monitor_thread
    if _monitor_running:
        return
    _monitor_running = True
    _monitor_thread = threading.Thread(
        target=_monitor_loop, daemon=True, name="HealthMonitor"
    )
    _monitor_thread.start()
    logger.info("[HEALTH] System Health Monitor started")
    print("[HEALTH] System Health Monitor started", flush=True)


def stop_health_monitor():
    global _monitor_running
    _monitor_running = False


def get_health_snapshot() -> Dict[str, Any]:
    """Get a one-shot health snapshot (for diagnostic command)."""
    return _collect_health()
