"""
TEST 3 — FASTAPI ROUTES VERIFICATION
Verifies that critical API endpoints are defined on the FastAPI app
and can respond (where possible without external dependencies).
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
    print("║        TEST 3 — FASTAPI ROUTES VERIFICATION            ║")
    print("╚══════════════════════════════════════════════════════════╝\n")

    try:
        from server.api import app
    except Exception as e:
        print(f"  ❌ Cannot import FastAPI app: {e}")
        results["fail"] += 1
        results["details"].append(f"IMPORT FAIL: {e}")
        return results

    # Expected routes
    expected_routes = [
        ("/", "GET"),
        ("/api/system/health", "GET"),
        ("/api/system/metrics", "GET"),
        ("/api/license/verify", "GET"),
        ("/api/referral/register", "POST"),
        ("/api/referral/status", "GET"),
        ("/ws/voice", "WEBSOCKET"),
    ]

    # Gather registered routes
    registered = set()
    for route in app.routes:
        path = getattr(route, "path", None)
        if path:
            methods = getattr(route, "methods", set())
            if methods:
                for m in methods:
                    registered.add((path, m.upper()))
            else:
                # WebSocket routes have no methods attr
                registered.add((path, "WEBSOCKET"))

    print("  ── Endpoint Registration Check ──")
    for path, method in expected_routes:
        found = (path, method) in registered
        status = "PASS" if found else "FAIL"
        icon = "✅" if found else "❌"
        print(f"    {icon} {method:10s} {path} ... {status}")
        results["pass" if found else "fail"] += 1
        if not found:
            results["details"].append(f"MISSING ROUTE: {method} {path}")

    # Test via httpx TestClient if available
    print("\n  ── Live Endpoint Test (TestClient) ──")
    try:
        from httpx import ASGITransport, AsyncClient
        import asyncio

        async def _test_endpoints():
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://testserver") as client:
                for path in ["/", "/api/system/health"]:
                    try:
                        resp = await client.get(path)
                        ok = resp.status_code == 200
                        icon = "✅" if ok else "❌"
                        print(f"    {icon} GET {path} → {resp.status_code} ... {'PASS' if ok else 'FAIL'}")
                        results["pass" if ok else "fail"] += 1
                        if not ok:
                            results["details"].append(f"HTTP {resp.status_code}: GET {path}")
                    except Exception as e:
                        print(f"    ⚠️  GET {path} → Exception: {e}")
                        results["fail"] += 1

        asyncio.run(_test_endpoints())
    except ImportError:
        print("    ⚠️  httpx not installed — skipping live endpoint tests")
    except Exception as e:
        print(f"    ⚠️  TestClient error: {e}")

    total = results["pass"] + results["fail"]
    print(f"\n  Summary: {results['pass']}/{total} checks passed")
    return results


if __name__ == "__main__":
    r = run_test()
    sys.exit(0 if r["fail"] == 0 else 1)
