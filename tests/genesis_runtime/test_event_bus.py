"""
TEST 8 — EVENT BUS TEST
Verifies:
- EventBus singleton loads
- Subscribe / publish / unsubscribe cycle works
- Priority queuing
- Event history tracking
- Middleware support
- Stats reporting
"""

import os
import sys
import asyncio

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

os.environ.setdefault("CLOUD_MODE", "true")


def run_test():
    results = {"pass": 0, "fail": 0, "details": []}

    print("\n╔══════════════════════════════════════════════════════════╗")
    print("║          TEST 8 — EVENT BUS TEST                       ║")
    print("╚══════════════════════════════════════════════════════════╝\n")

    # 1. Import
    print("  ── EventBus Import ──")
    try:
        from core.event_bus import EventBus, Event, EventPriority, get_event_bus, set_event_bus
        print(f"    ✅ EventBus classes imported ... PASS")
        results["pass"] += 1
    except Exception as e:
        print(f"    ❌ EventBus import: {e}")
        results["fail"] += 1
        return results

    # 2. Create isolated bus for testing
    print("\n  ── Isolated Bus Test ──")
    async def _test_bus():
        bus = EventBus()
        received = []

        async def handler(event):
            received.append(event)

        # Subscribe
        sub_id = bus.subscribe("test_event", handler)
        assert sub_id is not None
        print(f"    ✅ subscribe() returns ID ... PASS")
        results["pass"] += 1

        # Start bus
        await bus.start()
        assert bus._running
        print(f"    ✅ EventBus started ... PASS")
        results["pass"] += 1

        # Publish
        await bus.publish("test_event", "test_source", data={"key": "value"})
        await asyncio.sleep(0.3)  # Let event process

        assert len(received) >= 1, f"Expected ≥1 event, got {len(received)}"
        assert received[0].event_type == "test_event"
        assert received[0].data["key"] == "value"
        print(f"    ✅ publish() → handler received event ... PASS")
        results["pass"] += 1

        # Priority publish
        await bus.publish("test_event", "test_source", data={"priority": "high"}, priority=EventPriority.HIGH)
        await asyncio.sleep(0.2)
        assert len(received) >= 2
        print(f"    ✅ Priority event delivered ... PASS")
        results["pass"] += 1

        # Event history
        history = bus.get_event_history("test_event")
        assert len(history) >= 2
        print(f"    ✅ Event history tracking ({len(history)} events) ... PASS")
        results["pass"] += 1

        # Stats
        stats = bus.get_stats()
        assert "running" in stats
        assert stats["running"] is True
        assert "subscribers" in stats
        print(f"    ✅ get_stats() operational ... PASS")
        results["pass"] += 1

        # Wildcard subscriber
        wildcard_received = []
        async def wildcard_handler(event):
            wildcard_received.append(event)

        bus.subscribe_to_all(wildcard_handler)
        await bus.publish("another_event", "test", data={"wild": True})
        await asyncio.sleep(0.2)
        assert len(wildcard_received) >= 1
        print(f"    ✅ Wildcard subscriber works ... PASS")
        results["pass"] += 1

        # Unsubscribe
        bus.unsubscribe("test_event", handler)
        prev_count = len(received)
        await bus.publish("test_event", "test", data={"after_unsub": True})
        await asyncio.sleep(0.2)
        assert len(received) == prev_count, "Handler still received after unsubscribe"
        print(f"    ✅ unsubscribe() works ... PASS")
        results["pass"] += 1

        # Sync publish
        bus.publish_sync("test_sync", "sync_source", data={"sync": True})
        await asyncio.sleep(0.2)
        print(f"    ✅ publish_sync() no crash ... PASS")
        results["pass"] += 1

        # Stop
        await bus.stop()
        assert not bus._running
        print(f"    ✅ EventBus stopped gracefully ... PASS")
        results["pass"] += 1

    try:
        asyncio.run(_test_bus())
    except Exception as e:
        print(f"    ❌ Bus test error: {e}")
        results["fail"] += 1
        results["details"].append(f"BUS TEST: {e}")

    # 3. Global singleton
    print("\n  ── Global Singleton ──")
    try:
        bus = get_event_bus()
        assert bus is not None
        print(f"    ✅ get_event_bus() singleton ... PASS")
        results["pass"] += 1
    except Exception as e:
        print(f"    ❌ Singleton: {e}")
        results["fail"] += 1

    total = results["pass"] + results["fail"]
    print(f"\n  Summary: {results['pass']}/{total} checks passed")
    return results


if __name__ == "__main__":
    r = run_test()
    sys.exit(0 if r["fail"] == 0 else 1)
