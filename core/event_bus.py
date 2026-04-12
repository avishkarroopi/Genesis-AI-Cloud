"""
Production-grade event bus for GENESIS + JARVIS.
Implements pub/sub architecture for all system components.
Requirement 18: Event-driven architecture.
"""

import asyncio
import logging
import threading
from typing import Callable, Any, Dict, List, Set, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from contextlib import asynccontextmanager

try:
    from core.config import SAFE_START
except ImportError:
    SAFE_START = True


class EventPriority(Enum):
    CRITICAL = 0
    HIGH = 1
    NORMAL = 2
    LOW = 3


@dataclass
class Event:
    """Immutable event structure."""
    event_type: str
    source: str
    timestamp: datetime = field(default_factory=datetime.now)
    priority: EventPriority = EventPriority.NORMAL
    data: Dict[str, Any] = field(default_factory=dict)
    
    def __hash__(self):
        return hash((self.event_type, self.source, self.timestamp))


class EventBus:
    """
    Asynchronous event bus supporting pub/sub pattern.
    Handles event routing, priority queuing, and async callbacks.
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        self._subscribers: Dict[str, List[Callable[..., Any]]] = {}
        self._event_queue: asyncio.PriorityQueue[Any] = asyncio.PriorityQueue(maxsize=500)
        self._running = False
        self._tasks: Set[asyncio.Task[Any]] = set()
        self._processor_task: Optional[asyncio.Task[Any]] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._event_history: List[Event] = []
        self._max_history = 10000
        self._middleware: List[Callable] = []
        self._lock = asyncio.Lock()
        self._event_counter = 0  # Counter for priority queue tiebreaker
        
    def subscribe(self, event_type: str, callback: Callable) -> str:
        """
        Subscribe to events of a specific type.
        Returns subscription ID for later unsubscription.
        """
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        if callback not in self._subscribers[event_type]:
            self._subscribers[event_type].append(callback)
        sub_id = f"{event_type}_{id(callback)}"
        self.logger.debug(f"Subscription created: {sub_id}")
        return sub_id
    
    def unsubscribe(self, event_type: str, callback: Callable):
        """Unsubscribe from events."""
        if event_type in self._subscribers:
            self._subscribers[event_type].remove(callback)
    
    def subscribe_to_all(self, callback: Callable) -> str:
        """Subscribe to all events."""
        return self.subscribe("*", callback)
    
    def add_middleware(self, middleware: Callable):
        """Add event processing middleware."""
        if middleware not in self._middleware:
            self._middleware.append(middleware)
    
    async def emit(self, event: Event):
        """Emit an event asynchronously."""
        # Use counter as tiebreaker to avoid comparing Event objects
        self._event_counter += 1
        try:
            self._event_queue.put_nowait((event.priority.value, self._event_counter, event))
        except asyncio.QueueFull:
            if getattr(self, "logger", None):
                self.logger.warning(f"Event bus queue full! Dropping event: {event.event_type}")
    
    async def publish(
        self,
        event_type: str,
        source: str,
        data: Optional[Dict[str, Any]] = None,
        priority: EventPriority = EventPriority.NORMAL
    ):
        """Publish a new event."""
        event = Event(
            event_type=event_type,
            source=source,
            data=data or {},
            priority=priority
        )
        await self.emit(event)
    
    def publish_sync(
        self,
        event_type: str,
        source: str,
        data: Optional[Dict[str, Any]] = None,
        priority: EventPriority = EventPriority.NORMAL
    ):
        """Thread-safe synchronous publish for background threads."""
        if not self._loop or not self._running:
            return
            
        event = Event(
            event_type=event_type,
            source=source,
            data=data or {},
            priority=priority
        )
        
        # Use run_coroutine_threadsafe to safely push to the async queue from a sync thread
        loop = self._loop
        if loop is not None:
            try:
                asyncio.run_coroutine_threadsafe(self.emit(event), loop)
            except RuntimeError:
                # Loop was closed between our check and call — silently drop
                pass
    
    async def _process_event(self, event: Event):
        """Process a single event through all subscribers."""
        async with self._lock:
            self._event_history.append(event)
            if len(self._event_history) > self._max_history:
                self._event_history.pop(0)
        
        # Suppress repetitive cycle logs to reduce terminal flooding
        # Only log important events; cycle events are for debugging only
        if event.event_type not in ["reasoning_cycle_start", "reasoning_cycle_complete", "health_warning"]:
            pass  # Reduced spam
        
        for middleware in self._middleware:
            result = await self._run_async(middleware, event)
            if result is None:
                return
            if isinstance(result, Event):
                event = result
        
        callbacks = self._subscribers.get(event.event_type, [])
        callbacks.extend(self._subscribers.get("*", []))
        
        for callback in callbacks:
            try:
                await self._run_async(callback, event)
            except Exception as e:
                self.logger.error(
                    f"Error in event handler for {event.event_type}: {e}",
                    exc_info=True
                )
    
    async def _run_async(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        """Run function, handling both sync and async."""
        if asyncio.iscoroutinefunction(func):
            return await func(*args, **kwargs)
        else:
            return func(*args, **kwargs)
    
    async def start(self):
        """Start the event bus processor as a background task."""
        self._running = True
        self._loop = asyncio.get_running_loop()
        # Create background task for event processing loop
        self._processor_task = asyncio.create_task(self._event_processing_loop())
        self.logger.info("Event bus started")
    
    async def _event_processing_loop(self):
        """Process events in infinite background loop."""
        while self._running:
            try:
                priority, counter, event = await asyncio.wait_for(
                    self._event_queue.get(),
                    timeout=0.1
                )
                task = asyncio.create_task(self._process_event(event))
                self._tasks.add(task)
                def _safe_done(t, _tasks=self._tasks):
                    _tasks.discard(t)
                    if t.cancelled():
                        return
                    exc = t.exception()
                    if exc:
                        self.logger.error(f"Event task failed: {exc}")
                task.add_done_callback(_safe_done)
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                self.logger.error(f"Event bus error: {e}", exc_info=True)
    
    async def stop(self):
        """Stop the event bus gracefully."""
        self._running = False
        
        # Wait for processor task to finish
        t = self._processor_task
        if t is not None:
            try:
                await asyncio.wait_for(t, timeout=1.0)
            except asyncio.TimeoutError:
                t.cancel()
        
        # Wait for any in-flight event tasks
        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)
        
        self.logger.info("Event bus stopped")
    
    def get_event_history(self, event_type: Optional[str] = None, limit: int = 100) -> List[Event]:
        """Get event history, optionally filtered by type."""
        if event_type:
            history = [e for e in self._event_history if e.event_type == event_type]
        else:
            history = self._event_history
        
        return history[-limit:]  # type: ignore
    
    async def wait_for_event(
        self,
        event_type: str,
        timeout: Optional[float] = None,
        filter_func: Optional[Callable[..., Any]] = None
    ) -> Event:
        """
        Wait for a specific event.
        Optionally filter by custom function.
        """
        future = asyncio.Future()
        
        async def handler(event: Event):
            if filter_func is None or await self._run_async(filter_func, event):
                if not future.done():
                    future.set_result(event)
        
        self.subscribe(event_type, handler)
        
        try:
            result = await asyncio.wait_for(future, timeout=timeout)
            return result
        finally:
            self.unsubscribe(event_type, handler)
        raise RuntimeError("Unreachable")  # type: ignore
    
    @asynccontextmanager
    async def batch_events(self):  # type: ignore
        """Context manager for batch publishing."""
        original_queue = self._event_queue
        batch_queue: List[Any] = []
        
        try:
            self._event_queue = batch_queue  # type: ignore
            yield
        finally:
            self._event_queue = original_queue
            for item in sorted(batch_queue, key=lambda x: x[0]):
                await original_queue.put(item)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get event bus statistics."""
        return {
            "running": self._running,
            "subscribers": {k: len(v) for k, v in self._subscribers.items()},
            "queue_size": self._event_queue.qsize(),
            "history_size": len(self._event_history),
            "active_tasks": len(self._tasks)
        }


_global_event_bus: Optional[EventBus] = None
_bus_lock = threading.Lock()


def get_event_bus() -> EventBus:
    """Get or create the global event bus. Thread-safe singleton."""
    global _global_event_bus
    if _global_event_bus is None:
        with _bus_lock:
            if _global_event_bus is None:
                _global_event_bus = EventBus()
    return _global_event_bus


def set_event_bus(bus: EventBus):
    """Set the global event bus."""
    global _global_event_bus
    with _bus_lock:
        _global_event_bus = bus
