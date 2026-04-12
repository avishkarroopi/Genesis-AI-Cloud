"""
GENESIS Face Server - Broadcasts animation events to Android tablet UI.
Uses aiohttp WebSocket for real-time face animation control.
"""

import asyncio
import json
import logging
import time
from aiohttp import web
from pathlib import Path

import sys, os
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

try:
    import GPUtil
    HAS_GPU = True
except ImportError:
    HAS_GPU = False

logger = logging.getLogger(__name__)

# Global set of connected WebSocket clients
CONNECTED_CLIENTS = set()

# --- RATE LIMITING ---
import collections
_client_timestamps = collections.defaultdict(list)
_RATE_LIMIT = 5  # max commands per second per client

def _check_rate_limit(ws):
    """Returns True if client is within rate limit, False if exceeded."""
    now = time.time()
    timestamps = _client_timestamps[id(ws)]
    # Remove timestamps older than 1 second
    _client_timestamps[id(ws)] = [t for t in timestamps if now - t < 1.0]
    if len(_client_timestamps[id(ws)]) >= _RATE_LIMIT:
        return False
    _client_timestamps[id(ws)].append(now)
    return True


async def send_response_to_client(ws, response_type, text):
    """Send a response message to a specific WebSocket client."""
    try:
        msg = json.dumps({"type": response_type, "text": text})
        await ws.send_str(msg)
    except Exception as e:
        logger.warning(f"Failed to send response to client: {e}")


async def websocket_handler(request):
    """WebSocket handler for face clients."""
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    
    # --- PART 6: LIGHTWEIGHT AUTH ---
    expected_token = os.environ.get("GENESIS_WS_TOKEN", "")
    authenticated = not expected_token  # If no token configured, allow all
    
    if expected_token:
        try:
            auth_msg = await asyncio.wait_for(ws.receive(), timeout=5.0)
            if auth_msg.type == web.WSMsgType.TEXT:
                auth_data = json.loads(auth_msg.data)
                if auth_data.get("type") == "auth" and auth_data.get("token") == expected_token:
                    authenticated = True
                    await ws.send_str(json.dumps({"type": "auth", "status": "ok"}))
        except Exception as e:
            logger.warning(f"Auth handshake failed: {e}")
        
        if not authenticated:
            logger.warning("Client auth failed — closing connection")
            await ws.send_str(json.dumps({"type": "auth", "status": "denied"}))
            await ws.close()
            return ws

    CONNECTED_CLIENTS.add(ws)
    logger.info(f"Face client connected. Total clients: {len(CONNECTED_CLIENTS)}")
    
    try:
        async for msg in ws:
            if msg.type == web.WSMsgType.TEXT:
                try:
                    data = json.loads(msg.data)
                    logger.debug(f"Face server received: {data}")
                    # --- LITE COMMAND ROUTING ---
                    if data.get("type") == "command":
                        command_text = data.get("text", "").strip()
                        if command_text:
                            if not _check_rate_limit(ws):
                                await send_response_to_client(ws, "error", "Rate limit exceeded")
                                continue
                            try:
                                from core.event_bus import get_event_bus
                                bus = get_event_bus()
                                await bus.publish(
                                    "COMMAND_RECEIVED", "lite_client",
                                    {"text": command_text, "ws": ws}
                                )
                            except Exception as e:
                                logger.error(f"Command publish failed: {e}")
                                await send_response_to_client(ws, "error", "Command routing failed")
                        continue  # don't rebroadcast commands
                    # Rebroadcast to ALL OTHER connected clients (face UI)
                    disconnected = set()
                    # FIX: Use list() to avoid RuntimeError: Set changed size during iteration
                    for client in list(CONNECTED_CLIENTS):
                        if client is not ws:
                            try:
                                await client.send_str(msg.data)
                            except Exception as e:
                                logger.warning(f"Failed to relay to client: {e}")
                                disconnected.add(client)
                    for client in disconnected:
                        CONNECTED_CLIENTS.discard(client)
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON from face client: {msg.data}")
                except Exception as e:
                    logger.error(f"Error processing websocket text: {e}")
            elif msg.type == web.WSMsgType.ERROR:
                logger.error(f"WebSocket error: {ws.exception()}")
    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")
    finally:
        CONNECTED_CLIENTS.discard(ws)
        logger.info(f"Face client disconnected. Total clients: {len(CONNECTED_CLIENTS)}")
    
    return ws


async def index_handler(request):
    """Serve the HTML face UI (no cache for development)."""
    face_ui_path = Path(__file__).parent / "../lite/face_ui" / "index.html"

    if face_ui_path.exists():
        resp = web.FileResponse(face_ui_path)

        # 🔴 Disable browser cache
        resp.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        resp.headers["Pragma"] = "no-cache"
        resp.headers["Expires"] = "0"

        return resp
    else:
        return web.Response(text="Face UI not found", status=404)


async def update_credentials_handler(request):
    """API endpoint to update system credentials at runtime."""
    try:
        data = await request.json()
        if not data:
            return web.json_response({"error": "No payload provided"}, status=400)
            
        from core.event_bus import get_event_bus
        bus = get_event_bus()
        await bus.publish("CREDENTIALS_UPDATED", "face_server", data)
        
        return web.json_response({"status": "success", "message": "Credentials updated successfully"})
    except json.JSONDecodeError:
        return web.json_response({"error": "Invalid JSON payload"}, status=400)
    except Exception as e:
        logger.error(f"Credential update failed: {e}")
        return web.json_response({"error": str(e)}, status=500)


async def broadcast_event(event_type: str, data: Optional[Dict[str, Any]] = None):
    """Broadcast an animation event to all connected face clients."""
    if not CONNECTED_CLIENTS:
        logger.debug(f"No face clients connected. Event not broadcast: {event_type}")
        return
    
    message = {
        "event": event_type,
        "data": data or {}
    }
    
    json_str = json.dumps(message)
    logger.info(f"Broadcasting face event: {event_type}")
    
    # Send to all connected clients
    disconnected = set()
    # FIX: Use list() to avoid RuntimeError if clients connect/disconnect during broadcast
    for ws in list(CONNECTED_CLIENTS):
        try:
            await ws.send_str(json_str)
        except Exception as e:
            logger.warning(f"Failed to send to face client: {e}")
            disconnected.add(ws)
    
    # Clean up disconnected clients
    for ws in disconnected:
        CONNECTED_CLIENTS.discard(ws)


async def static_handler(request):
    file_path = request.match_info['filepath']
    face_ui_path = Path(__file__).parent / "../lite/face_ui" / file_path

    if face_ui_path.exists() and face_ui_path.is_file():
        resp = web.FileResponse(face_ui_path)

        # Disable cache for all UI files
        resp.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        resp.headers["Pragma"] = "no-cache"
        resp.headers["Expires"] = "0"

        return resp
    else:
        return web.Response(text="File not found", status=404)


def create_app():
    """Create and configure the aiohttp application."""
    app = web.Application()
    
    # Routes
    app.router.add_get("/", index_handler)
    app.router.add_get("/ws", websocket_handler)
    app.router.add_post("/api/update_credentials", update_credentials_handler)
    app.router.add_static('/static', Path(__file__).parent / "../lite/face_ui", name='static')
    app.router.add_get("/{filepath:.*}", static_handler)
    
    return app


async def stats_loop():
    """Background task to broadcast system stats every 3 seconds."""
    while True:
        try:
            cpu = psutil.cpu_percent(interval=None) if HAS_PSUTIL else None
            ram = psutil.virtual_memory().percent if HAS_PSUTIL else None
            gpu = None
            if HAS_GPU:
                gpus = GPUtil.getGPUs()
                if gpus:
                    gpu = round(gpus[0].load * 100, 1)
            
            await broadcast_event("sys_stats", {"cpu": cpu, "ram": ram, "gpu": gpu})
        except Exception as e:
            logger.error(f"Stats loop error: {e}")
        await asyncio.sleep(3)


async def run_server(host="0.0.0.0", port=8080):
    """Run the WebSocket server."""
    port_retries = 0
    max_port_retries = 3
    while True:
        try:
            app = create_app()
            runner = web.AppRunner(app)
            await runner.setup()
            site = web.TCPSite(runner, host, port)
            await site.start()
            logger.info(f"[OK] Face server started on ws://{host}:{port}/ws")
            port_retries = 0  # Reset on success
            
            # Start background stats broadcast task
            asyncio.create_task(stats_loop())
            
            # Keep server running
            while True:
                await asyncio.sleep(1)
        except OSError as e:
            if e.errno == 10048 or "10048" in str(e):
                # Port already in use — do NOT infinitely retry
                port_retries += 1
                if port_retries >= max_port_retries:
                    logger.error(f"Port {port} permanently occupied after {max_port_retries} attempts. Exiting.")
                    return  # Exit cleanly instead of infinite loop
                logger.warning(f"Port {port} in use (attempt {port_retries}/{max_port_retries}), retrying in 5s...")
                await asyncio.sleep(5)
            else:
                logger.error(f"Fatal face server error: {e}", exc_info=True)
                await asyncio.sleep(3)
        except Exception as e:
            logger.error(f"Fatal face server error: {e}", exc_info=True)
            logger.info("Restarting face server in 3 seconds...")
            await asyncio.sleep(3)


def start_server_thread():
    """Start the face server in a background thread (for synchronous context)."""
    import threading
    
    def run_event_loop():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(run_server())
        except KeyboardInterrupt:
            logger.info("Face server shutting down...")
        finally:
            loop.close()
    
    thread = threading.Thread(target=run_event_loop, daemon=True, name="FaceServer")
    thread.start()
    logger.info("Face server thread started")
    
    return thread


def get_active_client_count():
    """Return number of connected face clients."""
    return len(CONNECTED_CLIENTS)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    try:
        asyncio.run(run_server())
    except KeyboardInterrupt:
        logger.info("Face server stopped by user.")
    except Exception as e:
        logger.error(f"Face Server critical exception: {e}", exc_info=True)

