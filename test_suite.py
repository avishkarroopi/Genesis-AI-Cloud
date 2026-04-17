import urllib.request
import urllib.error
import json
import asyncio
import websockets
import sys

async def run_tests():
    report = {"backend": {}, "websocket": {}, "pipeline": {}}
    
    # STEP 1: Backend Server Checks
    print("Running STEP 1 tests...")
    try:
        req = urllib.request.urlopen("http://127.0.0.1:8000/docs")
        report["backend"]["docs"] = req.getcode() == 200
    except Exception as e:
        report["backend"]["docs"] = str(e)

    try:
        req = urllib.request.urlopen("http://127.0.0.1:8000/api/system/health")
        report["backend"]["health"] = json.loads(req.read().decode())
    except urllib.error.HTTPError as e:
        report["backend"]["health"] = json.loads(e.read().decode())
    except Exception as e:
        report["backend"]["health"] = str(e)

    try:
        req = urllib.request.urlopen("http://127.0.0.1:8000/api/system/metrics")
        report["backend"]["metrics"] = json.loads(req.read().decode())
    except urllib.error.HTTPError as e:
        report["backend"]["metrics"] = json.loads(e.read().decode())
    except Exception as e:
        report["backend"]["metrics"] = str(e)

    # STEP 2 & 3: WebSocket and Pipeline
    print("Running STEP 2 & 3 tests...")
    try:
        async with websockets.connect("ws://127.0.0.1:8000/ws/voice") as websocket:
            report["websocket"]["connected"] = True
            
            # Send test transcript
            msg = {"transcript": "Genesis open coding lab"}
            await websocket.send(json.dumps(msg))
            
            # Wait for responses
            responses = []
            try:
                for _ in range(5): # Wait for up to 5 messages or timeout
                    res = await asyncio.wait_for(websocket.recv(), timeout=3.0)
                    responses.append(json.loads(res))
            except asyncio.TimeoutError:
                pass
            
            report["pipeline"]["ws_responses"] = responses
            report["websocket"]["stable"] = websocket.open
    except Exception as e:
        report["websocket"]["error"] = str(e)
        
    print(json.dumps(report, indent=2))
    
if __name__ == "__main__":
    asyncio.run(run_tests())
