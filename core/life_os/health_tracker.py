"""
Health Tracker (Phase-2 User Intelligence)
Monitors sleep, fitness, health data.
"""

from core.event_bus import get_event_bus

def log_health_metric(metric: str, value: str):
    """Log health metric."""
    bus = get_event_bus()
    bus.publish_sync("LIFE_OS_UPDATE", "life_os.health_tracker", {"metric": metric, "value": value})
    return True
