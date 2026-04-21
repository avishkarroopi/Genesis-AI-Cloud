"""
TEST — Phase 4 Cognitive Intelligence Loop
Verifies cognitive loop cycles, event bus integration, and awareness engine.
"""

import os
import sys
import asyncio
import time

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

os.environ.setdefault("CLOUD_MODE", "true")


def test_cognitive_loop_instantiation():
    """CognitiveLoop should instantiate with upgraded attributes."""
    from core.cognition.cognitive_loop import get_cognitive_loop
    loop = get_cognitive_loop()
    assert loop is not None
    status = loop.get_status()
    assert "running" in status
    assert "pending_goals" in status
    assert "reflections" in status


def test_cognitive_loop_cycle():
    """A single cognitive cycle should execute without crashing."""
    from core.cognition.cognitive_loop import get_cognitive_loop
    loop = get_cognitive_loop()
    # Execute one cycle manually
    loop._cycle()
    # Should have incremented or at least not crashed
    assert True


def test_awareness_engine_instantiation():
    """AwarenessEngine should instantiate with Phase-4 attributes."""
    from core.awareness.awareness_loop import get_awareness_engine
    engine = get_awareness_engine()
    assert engine is not None
    status = engine.get_status()
    assert "running" in status
    assert "idle" in status
    assert "scans" in status


def test_event_bus_goal_triggered():
    """GOAL_TRIGGERED events should be publishable on the event bus."""
    from core.event_bus import EventBus

    async def _test():
        bus = EventBus()
        received = []

        async def on_goal(event):
            received.append(event)

        bus.subscribe("GOAL_TRIGGERED", on_goal)
        await bus.start()
        await bus.publish("GOAL_TRIGGERED", "test", data={"goal": {"type": "test", "description": "test goal"}})
        await asyncio.sleep(0.3)
        await bus.stop()
        return received

    events = asyncio.run(_test())
    assert len(events) >= 1
    assert events[0].data["goal"]["type"] == "test"


def test_cognitive_loop_accepts_goals():
    """CognitiveLoop should accept goals via _on_goal_triggered."""
    from core.cognition.cognitive_loop import get_cognitive_loop
    from core.event_bus import Event, EventPriority

    loop = get_cognitive_loop()
    initial_count = len(loop._pending_goals)

    # Simulate a GOAL_TRIGGERED event
    mock_event = Event(
        event_type="GOAL_TRIGGERED",
        source="test",
        data={"goal": {"type": "test_goal", "description": "unit test goal"}}
    )
    loop._on_goal_triggered(mock_event)

    assert len(loop._pending_goals) == initial_count + 1
    # Clean up
    loop._pending_goals.pop()


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
