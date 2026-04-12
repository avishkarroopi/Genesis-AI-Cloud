import os
import sys
import json
import asyncio
from pathlib import Path

# Add root to sys.path
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from core.self_repair_engine import SelfRepairEngine
from core.face_server import create_app
from aiohttp import web

async def test_self_repair_safeguard():
    print("\n--- Testing Self-Repair Safeguard ---")
    engine = SelfRepairEngine()
    
    # Test protected file
    protected_file = "core/event_bus.py"
    patch = "print('this should not be applied')"
    reason = "Testing safeguard"
    
    print(f"Attempting to patch protected file: {protected_file}")
    engine.apply_patch(protected_file, patch, reason)
    
    proposal_path = Path("logs/patch_proposals/patch_proposal_event_bus.py.json")
    if proposal_path.exists():
        print(f"SUCCESS: Patch proposal generated at {proposal_path}")
        with open(proposal_path, "r") as f:
            data = json.load(f)
            print(f"Proposal status: {data['status']}")
    else:
        print("FAILURE: Patch proposal not generated for protected file")

async def test_api_endpoint():
    print("\n--- Testing API Endpoint Route ---")
    app = create_app()
    # Check if route exists
    for route in app.router.routes():
        if route.resource.canonical == "/api/update_credentials":
            print(f"SUCCESS: Found route {route}")
            return
    print("FAILURE: Route /api/update_credentials not found in face_server")

if __name__ == "__main__":
    asyncio.run(test_self_repair_safeguard())
    asyncio.run(test_api_endpoint())
