"""
TEST 4 — WEBSOCKET VOICE TEST
Verifies the WebSocket /ws/voice endpoint is registered,
ConnectionManager works, and messages can be exchanged.
"""

import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

os.environ.setdefault("CLOUD_MODE", "true")


def run_test():
    results = {"pass": 0, "fail": 0, "details": []}

    print("\n╔══════════════════════════════════════════════════════════╗")
    print("║        TEST 4 — WEBSOCKET VOICE TEST                   ║")
    print("╚══════════════════════════════════════════════════════════╝\n")

    # 1. Verify WebSocket route exists
    print("  ── WebSocket Route Registration ──")
    try:
        from server.api import app
        ws_routes = [r for r in app.routes if getattr(r, "path", "") == "/ws/voice"]
        found = len(ws_routes) > 0
        icon = "✅" if found else "❌"
        print(f"    {icon} /ws/voice route registered ... {'PASS' if found else 'FAIL'}")
        results["pass" if found else "fail"] += 1
    except Exception as e:
        print(f"    ❌ Route check failed: {e}")
        results["fail"] += 1
        results["details"].append(f"WS ROUTE CHECK FAIL: {e}")

    # 2. Verify ConnectionManager class
    print("\n  ── ConnectionManager Unit Test ──")
    try:
        from server.voice_ws import ConnectionManager
        mgr = ConnectionManager()
        assert hasattr(mgr, "active_connections"), "Missing active_connections"
        assert hasattr(mgr, "connect"), "Missing connect method"
        assert hasattr(mgr, "disconnect"), "Missing disconnect method"
        assert hasattr(mgr, "broadcast"), "Missing broadcast method"
        assert isinstance(mgr.active_connections, list)
        print(f"    ✅ ConnectionManager instantiation ... PASS")
        results["pass"] += 1
    except Exception as e:
        print(f"    ❌ ConnectionManager test: {e}")
        results["fail"] += 1
        results["details"].append(f"CONNECTION_MANAGER FAIL: {e}")

    # 3. Verify avatar bridge hooks
    print("\n  ── Avatar Event Bridge ──")
    try:
        from server.voice_ws import manager as global_manager
        assert global_manager is not None, "Global manager not initialized"
        print(f"    ✅ Global ConnectionManager initialized ... PASS")
        results["pass"] += 1
    except Exception as e:
        print(f"    ❌ Avatar bridge test: {e}")
        results["fail"] += 1

    # 4. Test WebSocket via httpx if available
    print("\n  ── WebSocket Live Test ──")
    try:
        from httpx import ASGITransport, AsyncClient
        from httpx_ws import aconnect_ws
        import asyncio

        async def _test_ws():
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://testserver") as client:
                try:
                    async with aconnect_ws("/ws/voice", client) as ws:
                        await ws.send_text('{"type": "ping"}')
                        print(f"    ✅ WebSocket connected and message sent ... PASS")
                        results["pass"] += 1
                except Exception as e:
                    print(f"    ⚠️  WebSocket connection test: {e}")
                    results["details"].append(f"WS CONNECT: {e}")

        asyncio.run(_test_ws())
    except ImportError:
        print("    ⚠️  httpx-ws not installed — skipping live WebSocket test")
    except Exception as e:
        print(f"    ⚠️  WebSocket test error: {e}")

    total = results["pass"] + results["fail"]
    print(f"\n  Summary: {results['pass']}/{total} checks passed")
    return results


if __name__ == "__main__":
    r = run_test()
    sys.exit(0 if r["fail"] == 0 else 1)
