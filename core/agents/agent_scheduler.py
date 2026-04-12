"""
GENESIS Agent Scheduler — Phase 2.5
Prevents agent execution collisions.
Max 3 concurrent agents, priority queue, thread-safe, no starvation.
"""

import threading
import time
import heapq
import logging
from typing import Dict, Any, Callable, Optional
from dataclasses import dataclass, field
from core.event_bus import get_event_bus

logger = logging.getLogger(__name__)

MAX_CONCURRENT_AGENTS = 3
MAX_QUEUE_SIZE = 50


@dataclass(order=True)
class ScheduledTask:
    """A prioritized task for the agent scheduler."""
    priority: int                    # lower = higher priority (1 = highest)
    enqueued_at: float = field(compare=False)
    task_id: str = field(compare=False)
    goal: Dict[str, Any] = field(compare=False)
    callback: Optional[Callable] = field(compare=False, default=None)

    def to_dict(self):
        return {
            "task_id": self.task_id,
            "priority": self.priority,
            "enqueued_at": self.enqueued_at,
            "goal": self.goal,
        }


class AgentScheduler:
    """
    Thread-safe priority queue scheduler for GENESIS agents.
    Enforces max_agents_running and fair scheduling.
    """

    def __init__(self, max_concurrent: int = MAX_CONCURRENT_AGENTS):
        self._max_concurrent = max_concurrent
        self._semaphore = threading.Semaphore(max_concurrent)
        self._queue: list = []          # min-heap of ScheduledTask
        self._queue_lock = threading.Lock()
        self._running: Dict[str, threading.Thread] = {}
        self._running_lock = threading.Lock()
        self._task_counter = 0
        self._shutdown = False
        self._bus = None
        self._dispatcher_thread = threading.Thread(
            target=self._dispatch_loop, daemon=True, name="AgentScheduler"
        )
        self._dispatcher_thread.start()
        logger.info(f"[SCHEDULER] Agent scheduler started (max={max_concurrent})")

    def bind_event_bus(self):
        try:
            self._bus = get_event_bus()
            if self._bus:
                self._bus.subscribe("GOAL_CREATED", self._on_goal_created)
                logger.info("[SCHEDULER] EventBus bound")
        except Exception as e:
            logger.warning(f"[SCHEDULER] EventBus binding failed: {e}")

    def submit(self, goal: Dict[str, Any], priority: int = 5,
               callback: Optional[Callable] = None) -> str:
        """Submit a goal for scheduled execution. Returns task_id."""
        with self._queue_lock:
            if len(self._queue) >= MAX_QUEUE_SIZE:
                logger.warning("[SCHEDULER] Queue full — dropping low-priority task")
                return ""
            self._task_counter += 1
            task_id = f"task_{self._task_counter}_{int(time.time())}"
            task = ScheduledTask(
                priority=priority,
                enqueued_at=time.time(),
                task_id=task_id,
                goal=goal,
                callback=callback,
            )
            heapq.heappush(self._queue, task)
            logger.info(f"[SCHEDULER] Queued {task_id} (priority={priority}, queue_len={len(self._queue)})")

        self._publish("AGENT_QUEUED", {"task_id": task_id, "priority": priority, "goal": goal})
        return task_id

    def _on_goal_created(self, source: str, data: dict):
        """Auto-subscribe to GOAL_CREATED events."""
        try:
            priority = data.get("priority", 5)
            self.submit(data, priority=priority)
        except Exception as e:
            logger.error(f"[SCHEDULER] Goal auto-submit error: {e}")

    def _dispatch_loop(self):
        """Background dispatcher — pops tasks and executes them respecting semaphore."""
        while not self._shutdown:
            task = self._pop_next()
            if task is None:
                time.sleep(0.05)
                continue

            # Acquire semaphore slot (blocks if MAX_CONCURRENT_AGENTS are running)
            acquired = self._semaphore.acquire(timeout=1.0)
            if not acquired:
                # Put task back and try again
                with self._queue_lock:
                    heapq.heappush(self._queue, task)
                time.sleep(0.1)
                continue

            thread = threading.Thread(
                target=self._run_task, args=(task,),
                daemon=True, name=f"Agent-{task.task_id}"
            )
            with self._running_lock:
                self._running[task.task_id] = thread
            thread.start()

    def _run_task(self, task: ScheduledTask):
        """Execute a single scheduled task."""
        self._publish("AGENT_STARTED", task.to_dict())
        logger.info(f"[SCHEDULER] Starting {task.task_id}")
        try:
            from core.agents.agent_worker import get_agent_worker
            worker = get_agent_worker()
            from core.agents.goal_queue import get_goal_queue
            get_goal_queue().add_goal(task.goal)
            if task.callback:
                task.callback(task.task_id, task.goal)
        except Exception as e:
            logger.error(f"[SCHEDULER] Task {task.task_id} failed: {e}")
        finally:
            self._semaphore.release()
            with self._running_lock:
                self._running.pop(task.task_id, None)
            self._publish("AGENT_COMPLETED", task.to_dict())
            logger.info(f"[SCHEDULER] Completed {task.task_id}")

    def _pop_next(self) -> Optional[ScheduledTask]:
        with self._queue_lock:
            if self._queue:
                return heapq.heappop(self._queue)
        return None

    def _publish(self, event: str, data: dict):
        try:
            if self._bus:
                self._bus.publish_sync(event, "agent_scheduler", data)
        except Exception:
            pass

    def get_stats(self) -> Dict[str, Any]:
        with self._queue_lock:
            queue_len = len(self._queue)
        with self._running_lock:
            running_count = len(self._running)
        return {
            "max_concurrent": self._max_concurrent,
            "queue_length": queue_len,
            "running_agents": running_count,
            "available_slots": self._max_concurrent - running_count,
        }

    def stop(self):
        self._shutdown = True


# Singleton
_scheduler: Optional[AgentScheduler] = None


def get_agent_scheduler() -> AgentScheduler:
    global _scheduler
    if _scheduler is None:
        _scheduler = AgentScheduler()
    return _scheduler


def start_agent_scheduler() -> AgentScheduler:
    scheduler = get_agent_scheduler()
    scheduler.bind_event_bus()
    logger.info("[SCHEDULER] Agent scheduler initialized")
    return scheduler
