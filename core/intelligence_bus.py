"""
GENESIS Intelligence Bus
The central nervous system of the AI Operating System.
Extends the existing EventBus to provide explicit sync/async orchestration.
"""
import logging
from typing import Callable, Any, Optional
from core.event_bus import get_event_bus, Event, EventPriority

logger = logging.getLogger(__name__)

class IntelligenceBus:
    """Unified Orchestration Layer for all Cognitive Modules."""
    
    def __init__(self):
        self._bus = get_event_bus()

    def publish(self, event_type: str, payload: dict, source: str = "intelligence_bus", priority: int = 2):
        """
        Thread-safe synchronous publish wrapper.
        Priority: 0=CRITICAL, 1=HIGH, 2=NORMAL, 3=LOW
        """
        try:
            self._bus.publish_sync(
                event_type=event_type,
                source=source,
                data=payload,
                priority=EventPriority(priority)
            )
        except Exception as e:
            logger.error(f"[BUS] Publish failed for {event_type}: {e}")

    async def publish_async(self, event_type: str, payload: dict, source: str = "intelligence_bus", priority: int = 2):
        """Async publish wrapper for non-blocking emission."""
        try:
            event = Event(
                event_type=event_type,
                source=source,
                data=payload,
                priority=EventPriority(priority)
            )
            await self._bus.emit(event)
        except Exception as e:
            logger.error(f"[BUS] Async publish failed for {event_type}: {e}")

    def subscribe(self, event_type: str, handler: Callable):
        """Subscribe a synchronous handler to an event."""
        # The underlying event bus handles async promotion internally,
        # but we expose an explicit sync signature per architecture guidelines.
        return self._bus.subscribe(event_type, handler)

    def subscribe_async(self, event_type: str, async_handler: Callable):
        """Subscribe an asynchronous coroutine handler to an event."""
        # Registers the coroutine directly. The underlying event processor
        # awaits it automatically.
        return self._bus.subscribe(event_type, async_handler)

_global_intelligence_bus = None

def get_intelligence_bus() -> IntelligenceBus:
    global _global_intelligence_bus
    if _global_intelligence_bus is None:
        _global_intelligence_bus = IntelligenceBus()
    return _global_intelligence_bus
